from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.v1.errors import raise_from_service
from app.core.deps import get_current_user, get_db
from app.models.entities import User
from app.schemas.common import MessageOut, NotificationOut
from app.services.notifications import NotificationService

router = APIRouter(prefix="/notifications", tags=["Notificações"])


@router.get("", response_model=list[NotificationOut])
def list_notifications(
    unread_only: bool = Query(False),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return NotificationService(db).list(current_user.company_id, unread_only)


@router.post("/{notification_id}/read", response_model=NotificationOut)
def mark_read(
    notification_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return NotificationService(db).mark_read(current_user.company_id, notification_id)
    except Exception as exc:
        raise_from_service(exc)


@router.post("/read-all", response_model=MessageOut)
def mark_all_read(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    NotificationService(db).mark_all_read(current_user.company_id)
    return MessageOut(message="Notificações marcadas como lidas.")
