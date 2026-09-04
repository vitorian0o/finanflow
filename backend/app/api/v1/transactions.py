from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.v1.errors import raise_from_service
from app.core.deps import get_current_user, get_db
from app.models.entities import User
from app.schemas.common import (
    MessageOut,
    PaginatedTransactions,
    TransactionCreate,
    TransactionOut,
    TransactionUpdate,
)
from app.services.transactions import TransactionService

router = APIRouter(prefix="/transactions", tags=["Lançamentos"])


@router.get("", response_model=PaginatedTransactions)
def list_transactions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = None,
    category_id: UUID | None = None,
    type: str | None = None,
    status: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return TransactionService(db).list(
        current_user.company_id,
        page=page,
        page_size=page_size,
        search=search,
        category_id=category_id,
        type_=type,
        status=status,
        date_from=date_from,
        date_to=date_to,
    )


@router.post("", response_model=TransactionOut, status_code=201)
def create_transaction(
    payload: TransactionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return TransactionService(db).create(current_user, payload)
    except Exception as exc:
        raise_from_service(exc)


@router.get("/{transaction_id}", response_model=TransactionOut)
def get_transaction(
    transaction_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    item = TransactionService(db).repo.get(current_user.company_id, transaction_id)
    if item is None:
        raise_from_service(LookupError("Lançamento não encontrado."))
    return TransactionOut.from_entity(item)


@router.put("/{transaction_id}", response_model=TransactionOut)
def update_transaction(
    transaction_id: UUID,
    payload: TransactionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return TransactionService(db).update(current_user, transaction_id, payload)
    except Exception as exc:
        raise_from_service(exc)


@router.delete("/{transaction_id}", response_model=MessageOut)
def delete_transaction(
    transaction_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        TransactionService(db).delete(current_user, transaction_id)
        return MessageOut(message="Lançamento excluído.")
    except Exception as exc:
        raise_from_service(exc)


@router.post("/{transaction_id}/settle", response_model=TransactionOut)
def settle_transaction(
    transaction_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return TransactionService(db).settle(current_user, transaction_id)
    except Exception as exc:
        raise_from_service(exc)
