from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.v1.errors import raise_from_service
from app.core.deps import get_current_user, get_db
from app.models.entities import User
from app.schemas.common import CategoryCreate, CategoryOut, CategoryUpdate, MessageOut
from app.services.categories import CategoryService

router = APIRouter(prefix="/categories", tags=["Categorias"])


@router.get("", response_model=list[CategoryOut])
def list_categories(
    type: str | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return CategoryService(db).list(current_user.company_id, type)


@router.post("", response_model=CategoryOut, status_code=201)
def create_category(
    payload: CategoryCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return CategoryService(db).create(current_user.company_id, payload)
    except Exception as exc:
        raise_from_service(exc)


@router.put("/{category_id}", response_model=CategoryOut)
def update_category(
    category_id: UUID,
    payload: CategoryUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return CategoryService(db).update(current_user.company_id, category_id, payload)
    except Exception as exc:
        raise_from_service(exc)


@router.delete("/{category_id}", response_model=MessageOut)
def delete_category(
    category_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        CategoryService(db).delete(current_user.company_id, category_id)
        return MessageOut(message="Categoria excluída.")
    except Exception as exc:
        raise_from_service(exc)
