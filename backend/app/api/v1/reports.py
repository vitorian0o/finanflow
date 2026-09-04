from datetime import date

from fastapi import APIRouter, Depends, Query
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from app.api.v1.errors import raise_from_service
from app.core.deps import get_current_user, get_db
from app.models.entities import User
from app.schemas.common import InsightOut, ReportOut
from app.services.insights import InsightService
from app.services.reports import ReportService

router = APIRouter(prefix="/reports", tags=["Relatórios"])
insights_router = APIRouter(prefix="/insights", tags=["Automação"])


@router.get("", response_model=ReportOut)
def get_report(
    period: str = Query("this_month"),
    date_from: date | None = None,
    date_to: date | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return ReportService(db).build(current_user.company_id, period, date_from, date_to)
    except Exception as exc:
        raise_from_service(exc)


@router.get("/export")
def export_report(
    period: str = Query("this_month"),
    date_from: date | None = None,
    date_to: date | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        service = ReportService(db)
        report = service.build(current_user.company_id, period, date_from, date_to)
        csv = service.to_csv(report)
        return PlainTextResponse(
            csv,
            media_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": 'attachment; filename="relatorio-finanflow.csv"'},
        )
    except Exception as exc:
        raise_from_service(exc)


@insights_router.post("/run", response_model=list[InsightOut])
def run_insights(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return InsightService(db).run_for_company(current_user.company_id)
