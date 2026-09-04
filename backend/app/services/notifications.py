from uuid import UUID

from sqlalchemy.orm import Session

from app.models.entities import Notification
from app.repositories.base import NotificationRepository
from app.schemas.common import NotificationOut


class NotificationService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = NotificationRepository(db)

    def list(self, company_id: UUID, unread_only: bool = False) -> list[NotificationOut]:
        return [NotificationOut.model_validate(item) for item in self.repo.list_for_company(company_id, unread_only)]

    def mark_read(self, company_id: UUID, notification_id: UUID) -> NotificationOut:
        item = self.repo.get(company_id, notification_id)
        if item is None:
            raise LookupError("Notificação não encontrada.")
        item.is_read = True
        self.db.commit()
        self.db.refresh(item)
        return NotificationOut.model_validate(item)

    def mark_all_read(self, company_id: UUID) -> None:
        (
            self.db.query(Notification)
            .filter(Notification.company_id == company_id, Notification.is_read.is_(False))
            .update({"is_read": True})
        )
        self.db.commit()
