"""Seed Aurora Digital with several months of demo financial data."""

from __future__ import annotations

import sys
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select

from app.core.constants import DEFAULT_CATEGORIES, TransactionStatus, TransactionType
from app.core.security import hash_password
from app.database.session import SessionLocal
from app.models.entities import Category, Company, ImportBatch, Notification, Transaction, User

DEMO_EMAIL = "demo@finanflow.app"
DEMO_PASSWORD = "demo12345"
DEMO_COMPANY = "Aurora Digital"


def _category_map(db, company_id) -> dict[tuple[str, str], Category]:
    items = db.scalars(select(Category).where(Category.company_id == company_id)).all()
    return {(item.name, item.type): item for item in items}


def _tx(
    company_id,
    categories,
    *,
    day: date,
    description: str,
    category: str,
    type_: str,
    amount: str | int | float,
    status: str = TransactionStatus.PAID,
    party: str | None = None,
    due: date | None = None,
    notes: str | None = None,
) -> Transaction:
    cat = categories[(category, type_)]
    paid_at = datetime(day.year, day.month, day.day, 15, 0, tzinfo=timezone.utc) if status == TransactionStatus.PAID else None
    return Transaction(
        company_id=company_id,
        category_id=cat.id,
        type=type_,
        status=status,
        amount=Decimal(str(amount)),
        date=day,
        due_date=due or (day if status == TransactionStatus.PENDING else None),
        paid_at=paid_at,
        party_name=party,
        description=description,
        notes=notes,
    )


def seed() -> None:
    db = SessionLocal()
    try:
        existing = db.scalar(select(User).where(User.email == DEMO_EMAIL))
        if existing:
            company_id = existing.company_id
            db.query(Transaction).filter(Transaction.company_id == company_id).delete()
            db.query(Notification).filter(Notification.company_id == company_id).delete()
            db.query(ImportBatch).filter(ImportBatch.company_id == company_id).delete()
            db.query(Category).filter(Category.company_id == company_id).delete()
            db.delete(existing)
            company = db.get(Company, company_id)
            if company:
                db.delete(company)
            db.commit()
            print("Existing demo data removed. Seeding again.")

        company = Company(name=DEMO_COMPANY)
        db.add(company)
        db.flush()

        db.add(
            User(
                company_id=company.id,
                name="Marina Alves",
                email=DEMO_EMAIL,
                password_hash=hash_password(DEMO_PASSWORD),
            )
        )

        for type_, names in DEFAULT_CATEGORIES.items():
            for name in names:
                db.add(Category(company_id=company.id, name=name, type=type_.value, is_default=True))
        db.flush()
        categories = _category_map(db, company.id)

        rows: list[Transaction] = []
        monthly_clients = [
            ("Norte Alimentos", 4200),
            ("Clínica Vida", 3100),
            ("Studio Pilar", 2400),
        ]
        for month in range(3, 10):
            for index, (client, amount) in enumerate(monthly_clients, start=5):
                bump = 150 if month >= 8 else 0
                rows.append(
                    _tx(
                        company.id,
                        categories,
                        day=date(2026, month, index + 2),
                        description=f"Retainer mensal — {client}",
                        category="Serviços",
                        type_=TransactionType.INCOME,
                        amount=amount + bump,
                        party=client,
                    )
                )
            rows.append(
                _tx(
                    company.id,
                    categories,
                    day=date(2026, month, 18),
                    description=f"Projeto pontual #{month:02d}",
                    category="Vendas",
                    type_=TransactionType.INCOME,
                    amount=4200 + month * 120,
                    party="Cliente avulso",
                )
            )
            rows.extend(
                [
                    _tx(company.id, categories, day=date(2026, month, 5), description="Salários equipe", category="Salários", type_=TransactionType.EXPENSE, amount=4800 if month < 9 else 5200),
                    _tx(company.id, categories, day=date(2026, month, 8), description="Assinaturas de software", category="Software", type_=TransactionType.EXPENSE, amount=890),
                    _tx(company.id, categories, day=date(2026, month, 12), description="Anúncios Meta e Google", category="Marketing", type_=TransactionType.EXPENSE, amount=1100 if month < 9 else 1750, party="Agência Ponto"),
                    _tx(company.id, categories, day=date(2026, month, 20), description="Aluguel e internet", category="Operacional", type_=TransactionType.EXPENSE, amount=1800),
                    _tx(company.id, categories, day=date(2026, month, 25), description="DAS / impostos", category="Impostos", type_=TransactionType.EXPENSE, amount=980),
                    _tx(company.id, categories, day=date(2026, month, 15), description="Fornecedor de impressos", category="Fornecedores", type_=TransactionType.EXPENSE, amount=430, party="Gráfica Lume"),
                ]
            )

        rows.extend(
            [
                _tx(
                    company.id,
                    categories,
                    day=date(2026, 9, 2),
                    description="Entrega projeto e-commerce",
                    category="Serviços",
                    type_=TransactionType.INCOME,
                    amount=9800,
                    party="Loja Serra",
                ),
                _tx(
                    company.id,
                    categories,
                    day=date(2026, 8, 20),
                    description="Hospedagem anual",
                    category="Software",
                    type_=TransactionType.EXPENSE,
                    amount=720,
                    status=TransactionStatus.PENDING,
                    due=date(2026, 8, 28),
                    party="CloudHost",
                ),
                _tx(
                    company.id,
                    categories,
                    day=date(2026, 8, 22),
                    description="Freela de motion",
                    category="Fornecedores",
                    type_=TransactionType.EXPENSE,
                    amount=1400,
                    status=TransactionStatus.PENDING,
                    due=date(2026, 8, 30),
                    party="Ana Freelancer",
                ),
                _tx(
                    company.id,
                    categories,
                    day=date(2026, 9, 1),
                    description="Energia elétrica",
                    category="Operacional",
                    type_=TransactionType.EXPENSE,
                    amount=330,
                    status=TransactionStatus.PENDING,
                    due=date(2026, 9, 4),
                    party="Concessionária",
                ),
                _tx(
                    company.id,
                    categories,
                    day=date(2026, 9, 2),
                    description="Pacote extra de tráfego",
                    category="Marketing",
                    type_=TransactionType.EXPENSE,
                    amount=900,
                    status=TransactionStatus.PENDING,
                    due=date(2026, 9, 9),
                    party="Agência Ponto",
                ),
                _tx(
                    company.id,
                    categories,
                    day=date(2026, 9, 3),
                    description="Projeto e-commerce fase 1",
                    category="Serviços",
                    type_=TransactionType.INCOME,
                    amount=4500,
                    status=TransactionStatus.PENDING,
                    due=date(2026, 8, 25),
                    party="Loja Serra",
                ),
                _tx(
                    company.id,
                    categories,
                    day=date(2026, 9, 4),
                    description="Consultoria de marca",
                    category="Serviços",
                    type_=TransactionType.INCOME,
                    amount=1800,
                    status=TransactionStatus.PENDING,
                    due=date(2026, 9, 10),
                    party="Café Bruma",
                ),
                _tx(
                    company.id,
                    categories,
                    day=date(2026, 7, 10),
                    description="Projeto cancelado pelo cliente",
                    category="Serviços",
                    type_=TransactionType.INCOME,
                    amount=2500,
                    status=TransactionStatus.CANCELLED,
                    party="Cliente X",
                    notes="Cancelado antes do kickoff",
                ),
            ]
        )

        db.add_all(rows)
        db.commit()
        print(f"Seed completed: {DEMO_EMAIL} / {DEMO_PASSWORD} — {len(rows)} transactions.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
