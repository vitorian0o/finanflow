from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal
from uuid import UUID

import pandas as pd
from sqlalchemy.orm import Session

from app.core.constants import TransactionStatus, TransactionType
from app.models.entities import Notification, Transaction
from app.repositories.base import TransactionRepository
from app.schemas.common import (
    AccountSummary,
    CategorySlice,
    DashboardOut,
    InsightOut,
    KpiPoint,
)
from app.services.insights import collect_insight_messages
from app.utils.dates import today_in_app_tz
from app.utils.money import as_money
from app.utils.periods import resolve_period


def _to_frame(items: list[Transaction]) -> pd.DataFrame:
    if not items:
        return pd.DataFrame(
            columns=[
                "id",
                "type",
                "status",
                "amount",
                "date",
                "due_date",
                "category",
                "description",
            ]
        )
    return pd.DataFrame(
        [
            {
                "id": str(item.id),
                "type": item.type,
                "status": item.status,
                "amount": float(item.amount),
                "date": item.date,
                "due_date": item.due_date,
                "category": item.category.name if item.category else "Outros",
                "description": item.description,
            }
            for item in items
        ]
    )


def _signed(row) -> float:
    amount = float(row["amount"])
    return amount if row["type"] == TransactionType.INCOME else -amount


class FinanceService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = TransactionRepository(db)

    def _load(self, company_id: UUID) -> pd.DataFrame:
        return _to_frame(self.repo.list_for_analysis(company_id))

    def dashboard(
        self,
        company_id: UUID,
        period: str,
        date_from: date | None,
        date_to: date | None,
    ) -> DashboardOut:
        today = today_in_app_tz()
        start, end = resolve_period(period, date_from, date_to, today)
        frame = self._load(company_id)
        paid = frame[frame["status"] == TransactionStatus.PAID].copy() if not frame.empty else frame
        pending = frame[frame["status"] == TransactionStatus.PENDING].copy() if not frame.empty else frame

        period_paid = paid[(paid["date"] >= start) & (paid["date"] <= end)] if not paid.empty else paid
        income = period_paid[period_paid["type"] == TransactionType.INCOME]["amount"].sum() if not period_paid.empty else 0
        expense = period_paid[period_paid["type"] == TransactionType.EXPENSE]["amount"].sum() if not period_paid.empty else 0
        profit = float(income) - float(expense)
        margin = (profit / float(income) * 100) if float(income) else 0.0

        payable = pending[pending["type"] == TransactionType.EXPENSE]["amount"].sum() if not pending.empty else 0
        receivable = pending[pending["type"] == TransactionType.INCOME]["amount"].sum() if not pending.empty else 0

        opening = 0.0
        if not paid.empty:
            before = paid[paid["date"] < start]
            if not before.empty:
                opening = float(before.apply(_signed, axis=1).sum())
        current_balance = opening
        if not paid.empty:
            current_balance = float(paid[paid["date"] <= today].apply(_signed, axis=1).sum()) if not paid.empty else 0.0

        return DashboardOut(
            period=period,
            date_from=start,
            date_to=end,
            total_income=as_money(income),
            total_expense=as_money(expense),
            profit=as_money(profit),
            margin=as_money(margin),
            payable_total=as_money(payable),
            receivable_total=as_money(receivable),
            current_balance=as_money(current_balance),
            income_vs_expense=self._income_vs_expense(period_paid, start, end),
            balance_evolution=self._balance_evolution(paid, start, end, opening),
            income_by_category=self._category_slices(period_paid, TransactionType.INCOME),
            expense_by_category=self._category_slices(period_paid, TransactionType.EXPENSE),
            monthly_cash_flow=self._monthly_cash_flow(period_paid, start, end),
            insights=self._dashboard_insights(company_id, frame, today),
        )

    def account_summary(self, company_id: UUID) -> AccountSummary:
        today = today_in_app_tz()
        soon = today + timedelta(days=7)
        frame = self._load(company_id)
        pending = frame[frame["status"] == TransactionStatus.PENDING].copy() if not frame.empty else frame
        if pending.empty:
            return AccountSummary(
                overdue_count=0,
                overdue_amount=0,
                due_today_count=0,
                due_today_amount=0,
                due_soon_count=0,
                due_soon_amount=0,
                expected_inflow=0,
                expected_outflow=0,
            )
        pending["due_date"] = pd.to_datetime(pending["due_date"]).dt.date
        overdue = pending[pending["due_date"].notna() & (pending["due_date"] < today)]
        due_today = pending[pending["due_date"] == today]
        due_soon = pending[
            pending["due_date"].notna() & (pending["due_date"] > today) & (pending["due_date"] <= soon)
        ]
        expected_in = pending[pending["type"] == TransactionType.INCOME]["amount"].sum()
        expected_out = pending[pending["type"] == TransactionType.EXPENSE]["amount"].sum()
        return AccountSummary(
            overdue_count=int(len(overdue.index)),
            overdue_amount=as_money(overdue["amount"].sum() if not overdue.empty else 0),
            due_today_count=int(len(due_today.index)),
            due_today_amount=as_money(due_today["amount"].sum() if not due_today.empty else 0),
            due_soon_count=int(len(due_soon.index)),
            due_soon_amount=as_money(due_soon["amount"].sum() if not due_soon.empty else 0),
            expected_inflow=as_money(expected_in),
            expected_outflow=as_money(expected_out),
        )

    def _income_vs_expense(self, period_paid: pd.DataFrame, start: date, end: date) -> list[KpiPoint]:
        months = pd.period_range(start=start.replace(day=1), end=end, freq="M")
        grouped: dict[str, dict[str, float]] = defaultdict(lambda: {"income": 0.0, "expense": 0.0})
        if not period_paid.empty:
            work = period_paid.copy()
            work["month"] = pd.to_datetime(work["date"]).dt.to_period("M").astype(str)
            for _, row in work.iterrows():
                key = "income" if row["type"] == TransactionType.INCOME else "expense"
                grouped[row["month"]][key] += float(row["amount"])
        points = []
        for month in months:
            label = month.strftime("%m/%Y")
            bucket = grouped[str(month)]
            points.append(
                KpiPoint(
                    label=label,
                    income=as_money(bucket["income"]),
                    expense=as_money(bucket["expense"]),
                    net=as_money(bucket["income"] - bucket["expense"]),
                )
            )
        return points

    def _monthly_cash_flow(self, period_paid: pd.DataFrame, start: date, end: date) -> list[KpiPoint]:
        return self._income_vs_expense(period_paid, start, end)

    def _balance_evolution(
        self, paid: pd.DataFrame, start: date, end: date, opening: float
    ) -> list[KpiPoint]:
        span = (end - start).days
        use_daily = span <= 40
        running = opening
        points: list[KpiPoint] = []
        if paid.empty:
            label = start.strftime("%d/%m") if use_daily else start.strftime("%m/%Y")
            return [KpiPoint(label=label, balance=as_money(opening), net=0)]

        work = paid[(paid["date"] >= start) & (paid["date"] <= end)].copy()
        if use_daily:
            cursor = start
            by_day = defaultdict(float)
            if not work.empty:
                for _, row in work.iterrows():
                    by_day[row["date"]] += _signed(row)
            while cursor <= end:
                running += by_day[cursor]
                points.append(
                    KpiPoint(label=cursor.strftime("%d/%m"), balance=as_money(running), net=as_money(by_day[cursor]))
                )
                cursor += timedelta(days=1)
            return points

        months = pd.period_range(start=start.replace(day=1), end=end, freq="M")
        by_month = defaultdict(float)
        if not work.empty:
            work["month"] = pd.to_datetime(work["date"]).dt.to_period("M").astype(str)
            for _, row in work.iterrows():
                by_month[row["month"]] += _signed(row)
        for month in months:
            delta = by_month[str(month)]
            running += delta
            points.append(
                KpiPoint(label=month.strftime("%m/%Y"), balance=as_money(running), net=as_money(delta))
            )
        return points

    def _category_slices(self, period_paid: pd.DataFrame, type_: TransactionType) -> list[CategorySlice]:
        if period_paid.empty:
            return []
        subset = period_paid[period_paid["type"] == type_]
        if subset.empty:
            return []
        grouped = subset.groupby("category", as_index=False)["amount"].sum().sort_values("amount", ascending=False)
        return [CategorySlice(name=row.category, amount=as_money(row.amount)) for row in grouped.itertuples()]

    def _dashboard_insights(self, company_id: UUID, frame: pd.DataFrame, today: date) -> list[InsightOut]:
        unread = (
            self.db.query(Notification)
            .filter(
                Notification.company_id == company_id,
                Notification.is_read.is_(False),
            )
            .order_by(Notification.created_at.desc())
            .limit(5)
            .all()
        )
        if unread:
            return [InsightOut(type=item.type, title=item.title, message=item.message) for item in unread]
        return collect_insight_messages(frame, today)
