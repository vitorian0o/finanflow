from uuid import UUID

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session, joinedload

from app.models.entities import Category, Company, Notification, Transaction, User


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_email(self, email: str) -> User | None:
        return self.db.scalar(select(User).where(func.lower(User.email) == email.lower()))

    def get(self, user_id: UUID) -> User | None:
        return self.db.get(User, user_id)


class CompanyRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, company_id: UUID) -> Company | None:
        return self.db.get(Company, company_id)

    def list_ids(self) -> list[UUID]:
        return list(self.db.scalars(select(Company.id)).all())


class CategoryRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_for_company(self, company_id: UUID, type_: str | None = None) -> list[Category]:
        stmt: Select[tuple[Category]] = select(Category).where(Category.company_id == company_id)
        if type_:
            stmt = stmt.where(Category.type == type_)
        return list(self.db.scalars(stmt.order_by(Category.type, Category.name)).all())

    def get(self, company_id: UUID, category_id: UUID) -> Category | None:
        return self.db.scalar(
            select(Category).where(Category.id == category_id, Category.company_id == company_id)
        )

    def get_by_name(self, company_id: UUID, name: str, type_: str) -> Category | None:
        return self.db.scalar(
            select(Category).where(
                Category.company_id == company_id,
                func.lower(Category.name) == name.lower(),
                Category.type == type_,
            )
        )

    def usage_count(self, category_id: UUID) -> int:
        return self.db.scalar(
            select(func.count()).select_from(Transaction).where(Transaction.category_id == category_id)
        ) or 0


class TransactionRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, company_id: UUID, transaction_id: UUID) -> Transaction | None:
        return self.db.scalar(
            select(Transaction)
            .options(joinedload(Transaction.category))
            .where(Transaction.id == transaction_id, Transaction.company_id == company_id)
        )

    def list_filtered(
        self,
        company_id: UUID,
        *,
        search: str | None = None,
        category_id: UUID | None = None,
        type_: str | None = None,
        status: str | None = None,
        date_from=None,
        date_to=None,
        due_from=None,
        due_to=None,
        pending_only: bool = False,
        page: int = 1,
        page_size: int = 20,
        order_by_due: bool = False,
    ) -> tuple[list[Transaction], int]:
        stmt = (
            select(Transaction)
            .options(joinedload(Transaction.category))
            .where(Transaction.company_id == company_id)
        )
        if search:
            pattern = f"%{search.strip()}%"
            stmt = stmt.where(
                Transaction.description.ilike(pattern) | Transaction.party_name.ilike(pattern)
            )
        if category_id:
            stmt = stmt.where(Transaction.category_id == category_id)
        if type_:
            stmt = stmt.where(Transaction.type == type_)
        if status:
            stmt = stmt.where(Transaction.status == status)
        if pending_only:
            stmt = stmt.where(Transaction.status == "pending")
        if date_from:
            stmt = stmt.where(Transaction.date >= date_from)
        if date_to:
            stmt = stmt.where(Transaction.date <= date_to)
        if due_from:
            stmt = stmt.where(Transaction.due_date >= due_from)
        if due_to:
            stmt = stmt.where(Transaction.due_date <= due_to)

        count_stmt = select(func.count()).select_from(stmt.order_by(None).subquery())
        total = self.db.scalar(count_stmt) or 0
        order_col = Transaction.due_date if order_by_due else Transaction.date
        items = list(
            self.db.scalars(
                stmt.order_by(order_col.desc(), Transaction.created_at.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            ).unique()
            .all()
        )
        return items, total

    def list_for_analysis(self, company_id: UUID) -> list[Transaction]:
        return list(
            self.db.scalars(
                select(Transaction)
                .options(joinedload(Transaction.category))
                .where(Transaction.company_id == company_id)
            ).all()
        )


class NotificationRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_for_company(self, company_id: UUID, unread_only: bool = False) -> list[Notification]:
        stmt = select(Notification).where(Notification.company_id == company_id)
        if unread_only:
            stmt = stmt.where(Notification.is_read.is_(False))
        return list(self.db.scalars(stmt.order_by(Notification.created_at.desc()).limit(50)).all())

    def get(self, company_id: UUID, notification_id: UUID) -> Notification | None:
        return self.db.scalar(
            select(Notification).where(
                Notification.id == notification_id, Notification.company_id == company_id
            )
        )
