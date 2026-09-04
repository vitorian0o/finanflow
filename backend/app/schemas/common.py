from datetime import date as Date
from datetime import datetime as DateTime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.core.constants import TransactionStatus, TransactionType
from app.utils.money import as_money


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class RegisterRequest(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)
    company_name: str = Field(min_length=2, max_length=120)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=72)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class CompanyOut(ORMModel):
    id: UUID
    name: str


class UserOut(ORMModel):
    id: UUID
    name: str
    email: EmailStr
    company: CompanyOut


class CompanyUpdate(BaseModel):
    name: str = Field(min_length=2, max_length=120)


class CategoryCreate(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    type: TransactionType


class CategoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=80)
    type: TransactionType | None = None


class CategoryOut(ORMModel):
    id: UUID
    name: str
    type: TransactionType
    is_default: bool


class TransactionCreate(BaseModel):
    date: Date
    description: str = Field(min_length=2, max_length=255)
    type: TransactionType
    category_id: UUID
    amount: Decimal = Field(gt=0)
    status: TransactionStatus = TransactionStatus.PAID
    due_date: Date | None = None
    party_name: str | None = Field(default=None, max_length=160)
    notes: str | None = None

    @field_validator("amount")
    @classmethod
    def amount_precision(cls, value: Decimal) -> Decimal:
        return value.quantize(Decimal("0.01"))


class TransactionUpdate(BaseModel):
    date: Date | None = None
    description: str | None = Field(default=None, min_length=2, max_length=255)
    type: TransactionType | None = None
    category_id: UUID | None = None
    amount: Decimal | None = Field(default=None, gt=0)
    status: TransactionStatus | None = None
    due_date: Date | None = None
    party_name: str | None = Field(default=None, max_length=160)
    notes: str | None = None


class TransactionOut(ORMModel):
    id: UUID
    date: Date
    description: str
    type: TransactionType
    category_id: UUID
    category_name: str
    amount: float
    status: TransactionStatus
    due_date: Date | None
    paid_at: DateTime | None
    party_name: str | None
    notes: str | None

    @classmethod
    def from_entity(cls, item) -> "TransactionOut":
        return cls(
            id=item.id,
            date=item.date,
            description=item.description,
            type=item.type,
            category_id=item.category_id,
            category_name=item.category.name,
            amount=as_money(item.amount),
            status=item.status,
            due_date=item.due_date,
            paid_at=item.paid_at,
            party_name=item.party_name,
            notes=item.notes,
        )


class PaginatedTransactions(BaseModel):
    items: list[TransactionOut]
    total: int
    page: int
    page_size: int


class AccountSummary(BaseModel):
    overdue_count: int
    overdue_amount: float
    due_today_count: int
    due_today_amount: float
    due_soon_count: int
    due_soon_amount: float
    expected_inflow: float
    expected_outflow: float


class KpiPoint(BaseModel):
    label: str
    income: float = 0
    expense: float = 0
    net: float = 0
    balance: float | None = None


class CategorySlice(BaseModel):
    name: str
    amount: float


class InsightOut(BaseModel):
    type: str
    title: str
    message: str


class DashboardOut(BaseModel):
    period: str
    date_from: Date
    date_to: Date
    total_income: float
    total_expense: float
    profit: float
    margin: float
    payable_total: float
    receivable_total: float
    current_balance: float
    income_vs_expense: list[KpiPoint]
    balance_evolution: list[KpiPoint]
    income_by_category: list[CategorySlice]
    expense_by_category: list[CategorySlice]
    monthly_cash_flow: list[KpiPoint]
    insights: list[InsightOut]


class ImportErrorItem(BaseModel):
    row: int
    field: str | None = None
    message: str
    raw: str | None = None


class ImportPreviewOut(BaseModel):
    filename: str
    total_rows: int
    valid_count: int
    error_count: int
    errors: list[ImportErrorItem]
    valid_sample: list[dict]


class ImportResultOut(BaseModel):
    id: UUID
    filename: str
    total_rows: int
    imported_count: int
    error_count: int
    errors: list[ImportErrorItem]


class ReportCategoryRow(BaseModel):
    name: str
    type: str
    amount: float


class ReportOut(BaseModel):
    company_name: str
    date_from: Date
    date_to: Date
    total_income: float
    total_expense: float
    profit: float
    margin: float
    current_balance: float
    overdue_payables: float
    overdue_receivables: float
    upcoming_payables: float
    upcoming_receivables: float
    categories: list[ReportCategoryRow]
    monthly_evolution: list[KpiPoint]


class NotificationOut(ORMModel):
    id: UUID
    type: str
    title: str
    message: str
    channel: str
    is_read: bool
    created_at: DateTime


class MessageOut(BaseModel):
    message: str
