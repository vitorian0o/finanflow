from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from app.api.v1.errors import raise_from_service
from app.core.deps import get_current_user, get_db
from app.models.entities import User
from app.schemas.common import ImportPreviewOut, ImportResultOut
from app.services.imports import SAMPLE_CSV, ImportService

router = APIRouter(prefix="/imports", tags=["Importação"])


@router.get("/sample", response_class=PlainTextResponse)
def sample_csv():
    return PlainTextResponse(
        SAMPLE_CSV,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="finanflow-exemplo.csv"'},
    )


@router.post("/preview", response_model=ImportPreviewOut)
def preview_csv(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return ImportService(db).preview(file)
    except Exception as exc:
        raise_from_service(exc)


@router.post("/confirm", response_model=ImportResultOut)
def confirm_csv(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return ImportService(db).confirm(current_user, file)
    except Exception as exc:
        raise_from_service(exc)
