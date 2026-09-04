from __future__ import annotations

from datetime import date, timedelta
from uuid import UUID

import pandas as pd
from sqlalchemy.orm import Session

from app.core.constants import TransactionStatus, TransactionType
from app.models.entities import Notification, Transaction
from app.repositories.base import CompanyRepository, TransactionRepository
from app.schemas.common import InsightOut
from app.utils.dates import today_in_app_tz
from app.utils.money import as_money


def _to_frame(items: list[Transaction]) -> pd.DataFrame:
    if not items:
        return pd.DataFrame(columns=["type", "status", "amount", "date", "due_date"])
    return pd.DataFrame(
        [
            {
                "type": item.type,
                "status": item.status,
                "amount": float(item.amount),
                "date": item.date,
                "due_date": item.due_date,
            }
            for item in items
        ]
    )


def collect_insight_messages(frame: pd.DataFrame, today: date) -> list[InsightOut]:
    insights: list[InsightOut] = []
    if frame.empty:
        return insights

    pending = frame[frame["status"] == TransactionStatus.PENDING].copy()
    paid = frame[frame["status"] == TransactionStatus.PAID].copy()
    if not pending.empty:
        pending["due_date"] = pd.to_datetime(pending["due_date"]).dt.date
        overdue_pay = pending[
            (pending["type"] == TransactionType.EXPENSE)
            & pending["due_date"].notna()
            & (pending["due_date"] < today)
        ]
        overdue_rec = pending[
            (pending["type"] == TransactionType.INCOME)
            & pending["due_date"].notna()
            & (pending["due_date"] < today)
        ]
        due_soon = pending[
            pending["due_date"].notna()
            & (pending["due_date"] >= today)
            & (pending["due_date"] <= today + timedelta(days=7))
        ]
        if not overdue_pay.empty:
            total = as_money(overdue_pay["amount"].sum())
            insights.append(
                InsightOut(
                    type="overdue_payable",
                    title="Contas vencidas",
                    message=f"Existem {len(overdue_pay.index)} contas a pagar vencidas, totalizando R$ {total:,.2f}.".replace(",", "X").replace(".", ",").replace("X", "."),
                )
            )
        if not overdue_rec.empty:
            total = as_money(overdue_rec["amount"].sum())
            insights.append(
                InsightOut(
                    type="overdue_receivable",
                    title="Recebimentos em atraso",
                    message=f"Existem {len(overdue_rec.index)} contas a receber atrasadas, totalizando R$ {total:,.2f}.".replace(",", "X").replace(".", ",").replace("X", "."),
                )
            )
        if not due_soon.empty:
            total = as_money(due_soon["amount"].sum())
            insights.append(
                InsightOut(
                    type="due_soon",
                    title="Vencimentos próximos",
                    message=f"{len(due_soon.index)} contas vencem nos próximos 7 dias, totalizando R$ {total:,.2f}.".replace(",", "X").replace(".", ",").replace("X", "."),
                )
            )

    if not paid.empty:
        this_start = today.replace(day=1)
        last_end = this_start - timedelta(days=1)
        last_start = last_end.replace(day=1)
        this_month = paid[(paid["date"] >= this_start) & (paid["date"] <= today)]
        last_month = paid[(paid["date"] >= last_start) & (paid["date"] <= last_end)]
        this_exp = float(this_month[this_month["type"] == TransactionType.EXPENSE]["amount"].sum()) if not this_month.empty else 0.0
        last_exp = float(last_month[last_month["type"] == TransactionType.EXPENSE]["amount"].sum()) if not last_month.empty else 0.0
        this_inc = float(this_month[this_month["type"] == TransactionType.INCOME]["amount"].sum()) if not this_month.empty else 0.0
        last_inc = float(last_month[last_month["type"] == TransactionType.INCOME]["amount"].sum()) if not last_month.empty else 0.0
        if last_exp > 0:
            change = (this_exp - last_exp) / last_exp * 100
            if change >= 10:
                insights.append(
                    InsightOut(
                        type="expense_above_average",
                        title="Despesas em alta",
                        message=f"As despesas aumentaram {change:.0f}% em relação ao mês anterior.",
                    )
                )
        if last_inc > 0:
            change = (this_inc - last_inc) / last_inc * 100
            if change <= -10:
                insights.append(
                    InsightOut(
                        type="revenue_drop",
                        title="Receita abaixo da média",
                        message=f"A receita caiu {abs(change):.0f}% em relação ao mês anterior.",
                    )
                )
    return insights


class InsightService:
    def __init__(self, db: Session):
        self.db = db
        self.transactions = TransactionRepository(db)
        self.companies = CompanyRepository(db)

    def run_for_company(self, company_id: UUID) -> list[InsightOut]:
        today = today_in_app_tz()
        frame = _to_frame(self.transactions.list_for_analysis(company_id))
        insights = collect_insight_messages(frame, today)
        for insight in insights:
            existing = (
                self.db.query(Notification)
                .filter(
                    Notification.company_id == company_id,
                    Notification.type == insight.type,
                    Notification.is_read.is_(False),
                )
                .first()
            )
            if existing:
                existing.title = insight.title
                existing.message = insight.message
            else:
                self.db.add(
                    Notification(
                        company_id=company_id,
                        type=insight.type,
                        title=insight.title,
                        message=insight.message,
                        channel="in_app",
                    )
                )
        self.db.commit()
        return insights

    def run_for_all_companies(self) -> int:
        count = 0
        for company_id in self.companies.list_ids():
            self.run_for_company(company_id)
            count += 1
        return count
