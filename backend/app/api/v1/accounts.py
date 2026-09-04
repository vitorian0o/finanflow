from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.constants import TransactionType
from app.core.deps import get_current_user, get_db
from app.models.entities import User
from app.schemas.common import AccountSummary, PaginatedTransactions
from app.services.finance import FinanceService
from app.services.transactions import TransactionService

router = APIRouter(prefix="/accounts", tags=["Contas"])


@router.get("/summary", response_model=AccountSummary)
def summary(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return FinanceService(db).account_summary(current_user.company_id)


@router.get("/payable", response_model=PaginatedTransactions)
def payable(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return TransactionService(db).list(
        current_user.company_id,
        page=page,
        page_size=page_size,
        search=search,
        type_=TransactionType.EXPENSE,
        pending_only=True,
        order_by_due=True,
    )


@router.get("/receivable", response_model=PaginatedTransactions)
def receivable(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return TransactionService(db).list(
        current_user.company_id,
        page=page,
        page_size=page_size,
        search=search,
        type_=TransactionType.INCOME,
        pending_only=True,
        order_by_due=True,
    )
