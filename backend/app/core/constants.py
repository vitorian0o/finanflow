from enum import StrEnum


class TransactionType(StrEnum):
    INCOME = "income"
    EXPENSE = "expense"


class TransactionStatus(StrEnum):
    PAID = "paid"
    PENDING = "pending"
    CANCELLED = "cancelled"


TYPE_ALIASES = {
    "income": TransactionType.INCOME,
    "receita": TransactionType.INCOME,
    "entrada": TransactionType.INCOME,
    "r": TransactionType.INCOME,
    "expense": TransactionType.EXPENSE,
    "despesa": TransactionType.EXPENSE,
    "saida": TransactionType.EXPENSE,
    "saída": TransactionType.EXPENSE,
    "d": TransactionType.EXPENSE,
}

STATUS_ALIASES = {
    "paid": TransactionStatus.PAID,
    "pago": TransactionStatus.PAID,
    "paga": TransactionStatus.PAID,
    "pending": TransactionStatus.PENDING,
    "pendente": TransactionStatus.PENDING,
    "cancelled": TransactionStatus.CANCELLED,
    "canceled": TransactionStatus.CANCELLED,
    "cancelado": TransactionStatus.CANCELLED,
    "cancelada": TransactionStatus.CANCELLED,
}

DEFAULT_CATEGORIES = {
    TransactionType.INCOME: ["Vendas", "Serviços", "Outros"],
    TransactionType.EXPENSE: [
        "Fornecedores",
        "Salários",
        "Marketing",
        "Operacional",
        "Impostos",
        "Software",
        "Outros",
    ],
}

CSV_COLUMN_ALIASES = {
    "date": {"data", "date", "dt"},
    "description": {"descricao", "descrição", "description", "desc"},
    "category": {"categoria", "category"},
    "type": {"tipo", "type"},
    "amount": {"valor", "value", "amount", "vlr"},
    "status": {"status", "situacao", "situação"},
    "due_date": {"vencimento", "due_date", "due", "data_vencimento"},
    "notes": {"observacao", "observação", "notes", "obs", "note"},
    "party_name": {"cliente", "fornecedor", "origem", "party", "party_name", "contraparte"},
}

REQUIRED_CSV_COLUMNS = ("date", "description", "category", "type", "amount", "status")
