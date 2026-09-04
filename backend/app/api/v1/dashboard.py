from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.v1.errors import raise_from_service
from app.core.deps import get_current_user, get_db
from app.models.entities import User
from app.schemas.common import CompanyOut, CompanyUpdate, DashboardOut
from app.services.companies import CompanyService
from app.services.finance import FinanceService

router = APIRouter(tags=["Dashboard"])


@router.get("/dashboard", response_model=DashboardOut)
def dashboard(
    period: str = Query("this_month"),
    date_from: date | None = None,
    date_to: date | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return FinanceService(db).dashboard(current_user.company_id, period, date_from, date_to)
    except Exception as exc:
        raise_from_service(exc)


company_router = APIRouter(prefix="/company", tags=["Empresa"])


@company_router.get("", response_model=CompanyOut)
def get_company(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        return CompanyService(db).get(current_user.company_id)
    except Exception as exc:
        raise_from_service(exc)


@company_router.put("", response_model=CompanyOut)
def update_company(
    payload: CompanyUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return CompanyService(db).update(current_user.company_id, payload)
    except Exception as exc:
        raise_from_service(exc)
