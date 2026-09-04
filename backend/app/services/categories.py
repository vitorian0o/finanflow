from uuid import UUID

from sqlalchemy.orm import Session

from app.core.constants import TransactionType
from app.models.entities import Category
from app.repositories.base import CategoryRepository
from app.schemas.common import CategoryCreate, CategoryOut, CategoryUpdate


class CategoryService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = CategoryRepository(db)

    def list(self, company_id: UUID, type_: str | None = None) -> list[CategoryOut]:
        return [CategoryOut.model_validate(item) for item in self.repo.list_for_company(company_id, type_)]

    def create(self, company_id: UUID, payload: CategoryCreate) -> CategoryOut:
        existing = self.repo.get_by_name(company_id, payload.name.strip(), payload.type.value)
        if existing:
            raise ValueError("Já existe uma categoria com este nome para o tipo informado.")
        item = Category(
            company_id=company_id,
            name=payload.name.strip(),
            type=payload.type.value,
            is_default=False,
        )
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return CategoryOut.model_validate(item)

    def update(self, company_id: UUID, category_id: UUID, payload: CategoryUpdate) -> CategoryOut:
        item = self.repo.get(company_id, category_id)
        if item is None:
            raise LookupError("Categoria não encontrada.")
        new_name = payload.name.strip() if payload.name else item.name
        new_type = payload.type.value if payload.type else item.type
        if payload.type and payload.type.value != item.type and self.repo.usage_count(item.id):
            raise ValueError("Não é possível alterar o tipo de uma categoria que já possui lançamentos.")
        clash = self.repo.get_by_name(company_id, new_name, new_type)
        if clash and clash.id != item.id:
            raise ValueError("Já existe uma categoria com este nome para o tipo informado.")
        item.name = new_name
        item.type = new_type
        self.db.commit()
        self.db.refresh(item)
        return CategoryOut.model_validate(item)

    def delete(self, company_id: UUID, category_id: UUID) -> None:
        item = self.repo.get(company_id, category_id)
        if item is None:
            raise LookupError("Categoria não encontrada.")
        if self.repo.usage_count(item.id):
            raise ValueError("Não é possível excluir uma categoria que possui lançamentos.")
        self.db.delete(item)
        self.db.commit()

    def get_or_create(self, company_id: UUID, name: str, type_: TransactionType) -> Category:
        existing = self.repo.get_by_name(company_id, name, type_.value)
        if existing:
            return existing
        item = Category(company_id=company_id, name=name.strip(), type=type_.value, is_default=False)
        self.db.add(item)
        self.db.flush()
        return item
