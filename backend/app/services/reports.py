from datetime import date, timedelta
from uuid import UUID

import pandas as pd
from sqlalchemy.orm import Session

from app.core.constants import TransactionStatus, TransactionType
from app.repositories.base import CompanyRepository, TransactionRepository
from app.schemas.common import KpiPoint, ReportCategoryRow, ReportOut
from app.utils.dates import today_in_app_tz
from app.utils.money import as_money
from app.utils.periods import resolve_period


class ReportService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = TransactionRepository(db)
        self.companies = CompanyRepository(db)

    def build(
        self,
        company_id: UUID,
        period: str,
        date_from: date | None,
        date_to: date | None,
    ) -> ReportOut:
        today = today_in_app_tz()
        start, end = resolve_period(period, date_from, date_to, today)
        company = self.companies.get(company_id)
        items = self.repo.list_for_analysis(company_id)
        if not items:
            frame = pd.DataFrame(columns=["type", "status", "amount", "date", "due_date", "category"])
        else:
            frame = pd.DataFrame(
                [
                    {
                        "type": item.type,
                        "status": item.status,
                        "amount": float(item.amount),
                        "date": item.date,
                        "due_date": item.due_date,
                        "category": item.category.name if item.category else "Outros",
                    }
                    for item in items
                ]
            )

        paid = frame[frame["status"] == TransactionStatus.PAID] if not frame.empty else frame
        pending = frame[frame["status"] == TransactionStatus.PENDING] if not frame.empty else frame
        period_paid = paid[(paid["date"] >= start) & (paid["date"] <= end)] if not paid.empty else paid
        income = float(period_paid[period_paid["type"] == TransactionType.INCOME]["amount"].sum()) if not period_paid.empty else 0.0
        expense = float(period_paid[period_paid["type"] == TransactionType.EXPENSE]["amount"].sum()) if not period_paid.empty else 0.0
        profit = income - expense
        margin = (profit / income * 100) if income else 0.0
        current_balance = 0.0
        if not paid.empty:
            current_balance = float(
                paid[paid["date"] <= today].apply(
                    lambda row: row["amount"] if row["type"] == TransactionType.INCOME else -row["amount"],
                    axis=1,
                ).sum()
            )

        overdue_pay = overdue_rec = upcoming_pay = upcoming_rec = 0.0
        if not pending.empty:
            pending = pending.copy()
            pending["due_date"] = pd.to_datetime(pending["due_date"]).dt.date
            overdue = pending[pending["due_date"].notna() & (pending["due_date"] < today)]
            upcoming = pending[
                pending["due_date"].notna()
                & (pending["due_date"] >= today)
                & (pending["due_date"] <= today + timedelta(days=30))
            ]
            overdue_pay = float(overdue[overdue["type"] == TransactionType.EXPENSE]["amount"].sum()) if not overdue.empty else 0.0
            overdue_rec = float(overdue[overdue["type"] == TransactionType.INCOME]["amount"].sum()) if not overdue.empty else 0.0
            upcoming_pay = float(upcoming[upcoming["type"] == TransactionType.EXPENSE]["amount"].sum()) if not upcoming.empty else 0.0
            upcoming_rec = float(upcoming[upcoming["type"] == TransactionType.INCOME]["amount"].sum()) if not upcoming.empty else 0.0

        categories: list[ReportCategoryRow] = []
        if not period_paid.empty:
            grouped = period_paid.groupby(["category", "type"], as_index=False)["amount"].sum()
            for row in grouped.itertuples():
                categories.append(
                    ReportCategoryRow(name=row.category, type=row.type, amount=as_money(row.amount))
                )
            categories.sort(key=lambda item: item.amount, reverse=True)

        monthly: list[KpiPoint] = []
        if not period_paid.empty:
            work = period_paid.copy()
            work["month"] = pd.to_datetime(work["date"]).dt.to_period("M").astype(str)
            months = sorted(work["month"].unique())
            running = 0.0
            before = paid[paid["date"] < start] if not paid.empty else paid
            if not before.empty:
                running = float(
                    before.apply(
                        lambda row: row["amount"] if row["type"] == TransactionType.INCOME else -row["amount"],
                        axis=1,
                    ).sum()
                )
            for month in months:
                chunk = work[work["month"] == month]
                inc = float(chunk[chunk["type"] == TransactionType.INCOME]["amount"].sum())
                exp = float(chunk[chunk["type"] == TransactionType.EXPENSE]["amount"].sum())
                running += inc - exp
                year, month_n = month.split("-")
                monthly.append(
                    KpiPoint(
                        label=f"{month_n}/{year}",
                        income=as_money(inc),
                        expense=as_money(exp),
                        net=as_money(inc - exp),
                        balance=as_money(running),
                    )
                )

        return ReportOut(
            company_name=company.name if company else "FinanFlow",
            date_from=start,
            date_to=end,
            total_income=as_money(income),
            total_expense=as_money(expense),
            profit=as_money(profit),
            margin=as_money(margin),
            current_balance=as_money(current_balance),
            overdue_payables=as_money(overdue_pay),
            overdue_receivables=as_money(overdue_rec),
            upcoming_payables=as_money(upcoming_pay),
            upcoming_receivables=as_money(upcoming_rec),
            categories=categories,
            monthly_evolution=monthly,
        )

    def to_csv(self, report: ReportOut) -> str:
        lines = [
            f"Empresa;{report.company_name}",
            f"Periodo;{report.date_from.isoformat()};{report.date_to.isoformat()}",
            f"Receitas;{report.total_income:.2f}",
            f"Despesas;{report.total_expense:.2f}",
            f"Lucro;{report.profit:.2f}",
            f"Margem %;{report.margin:.2f}",
            f"Saldo atual;{report.current_balance:.2f}",
            f"Contas vencidas a pagar;{report.overdue_payables:.2f}",
            f"Contas vencidas a receber;{report.overdue_receivables:.2f}",
            f"Contas futuras a pagar;{report.upcoming_payables:.2f}",
            f"Contas futuras a receber;{report.upcoming_receivables:.2f}",
            "",
            "Categoria;Tipo;Valor",
        ]
        for row in report.categories:
            lines.append(f"{row.name};{row.type};{row.amount:.2f}")
        lines.extend(["", "Mes;Receita;Despesa;Resultado;Saldo"])
        for point in report.monthly_evolution:
            lines.append(
                f"{point.label};{point.income:.2f};{point.expense:.2f};{point.net:.2f};{point.balance or 0:.2f}"
            )
        return "\n".join(lines)
