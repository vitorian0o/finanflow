from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.constants import TransactionStatus
from app.models.entities import Transaction, User
from app.repositories.base import CategoryRepository, TransactionRepository
from app.schemas.common import (
    PaginatedTransactions,
    TransactionCreate,
    TransactionOut,
    TransactionUpdate,
)


class TransactionService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = TransactionRepository(db)
        self.categories = CategoryRepository(db)

    def _validate_category(self, company_id: UUID, category_id: UUID, type_: str):
        category = self.categories.get(company_id, category_id)
        if category is None:
            raise LookupError("Categoria não encontrada.")
        if category.type != type_:
            raise ValueError("A categoria não corresponde ao tipo do lançamento.")
        return category

    def _apply_status_side_effects(self, item: Transaction, status: str) -> None:
        item.status = status
        if status == TransactionStatus.PAID and item.paid_at is None:
            item.paid_at = datetime.now(timezone.utc)
        if status != TransactionStatus.PAID:
            item.paid_at = None

    def list(
        self,
        company_id: UUID,
        **filters,
    ) -> PaginatedTransactions:
        items, total = self.repo.list_filtered(company_id, **filters)
        return PaginatedTransactions(
            items=[TransactionOut.from_entity(item) for item in items],
            total=total,
            page=filters.get("page", 1),
            page_size=filters.get("page_size", 20),
        )

    def create(self, user: User, payload: TransactionCreate) -> TransactionOut:
        self._validate_category(user.company_id, payload.category_id, payload.type.value)
        item = Transaction(
            company_id=user.company_id,
            category_id=payload.category_id,
            type=payload.type.value,
            status=payload.status.value,
            amount=payload.amount,
            date=payload.date,
            due_date=payload.due_date or (payload.date if payload.status == TransactionStatus.PENDING else None),
            party_name=payload.party_name.strip() if payload.party_name else None,
            description=payload.description.strip(),
            notes=payload.notes.strip() if payload.notes else None,
        )
        self._apply_status_side_effects(item, payload.status.value)
        self.db.add(item)
        self.db.commit()
        item = self.repo.get(user.company_id, item.id)
        return TransactionOut.from_entity(item)

    def update(self, user: User, transaction_id: UUID, payload: TransactionUpdate) -> TransactionOut:
        item = self.repo.get(user.company_id, transaction_id)
        if item is None:
            raise LookupError("Lançamento não encontrado.")
        data = payload.model_dump(exclude_unset=True)
        next_type = data.get("type", item.type)
        next_type = next_type.value if hasattr(next_type, "value") else next_type
        next_category_id = data.get("category_id", item.category_id)
        self._validate_category(user.company_id, next_category_id, next_type)
        for field in ("date", "description", "category_id", "amount", "due_date", "party_name", "notes"):
            if field in data:
                value = data[field]
                if field in {"description", "party_name", "notes"} and isinstance(value, str):
                    value = value.strip() or None
                setattr(item, field, value)
        item.type = next_type
        if "status" in data:
            status = data["status"].value if hasattr(data["status"], "value") else data["status"]
            self._apply_status_side_effects(item, status)
        self.db.commit()
        item = self.repo.get(user.company_id, item.id)
        return TransactionOut.from_entity(item)

    def delete(self, user: User, transaction_id: UUID) -> None:
        item = self.repo.get(user.company_id, transaction_id)
        if item is None:
            raise LookupError("Lançamento não encontrado.")
        self.db.delete(item)
        self.db.commit()

    def settle(self, user: User, transaction_id: UUID) -> TransactionOut:
        item = self.repo.get(user.company_id, transaction_id)
        if item is None:
            raise LookupError("Lançamento não encontrado.")
        if item.status != TransactionStatus.PENDING:
            raise ValueError("Somente lançamentos pendentes podem ser marcados como pagos.")
        self._apply_status_side_effects(item, TransactionStatus.PAID)
        self.db.commit()
        item = self.repo.get(user.company_id, item.id)
        return TransactionOut.from_entity(item)
