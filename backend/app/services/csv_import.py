from __future__ import annotations

import io
import unicodedata
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

import pandas as pd
from dateutil import parser as date_parser

from app.core.config import get_settings
from app.core.constants import (
    CSV_COLUMN_ALIASES,
    REQUIRED_CSV_COLUMNS,
    STATUS_ALIASES,
    TYPE_ALIASES,
    TransactionStatus,
    TransactionType,
)


@dataclass
class CsvRowError:
    row: int
    field: str | None
    message: str
    raw: str | None = None


@dataclass
class ParsedCsvRow:
    date: date
    description: str
    category: str
    type: TransactionType
    amount: Decimal
    status: TransactionStatus
    due_date: date | None = None
    notes: str | None = None
    party_name: str | None = None
    source_row: int = 0


@dataclass
class CsvParseResult:
    filename: str
    total_rows: int
    valid_rows: list[ParsedCsvRow] = field(default_factory=list)
    errors: list[CsvRowError] = field(default_factory=list)

    @property
    def valid_count(self) -> int:
        return len(self.valid_rows)

    @property
    def error_count(self) -> int:
        return len(self.errors)


def _strip_accents(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    return "".join(char for char in normalized if not unicodedata.combining(char))


def _normalize_header(value: str) -> str:
    cleaned = _strip_accents(str(value).strip().lower())
    return "_".join(cleaned.replace("-", " ").split())


def _map_headers(columns: list[str]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    reverse = {alias: canonical for canonical, aliases in CSV_COLUMN_ALIASES.items() for alias in aliases}
    for original in columns:
        key = _normalize_header(original)
        canonical = reverse.get(key)
        if canonical:
            mapping[canonical] = original
    return mapping


def _cell(row: pd.Series, mapping: dict[str, str], field: str) -> str:
    column = mapping.get(field)
    if not column or column not in row.index:
        return ""
    value = row[column]
    if pd.isna(value):
        return ""
    return str(value).strip()


def parse_date(value: str) -> date:
    raw = value.strip()
    if not raw:
        raise ValueError("Data vazia.")
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%d/%m/%y"):
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
    parsed = date_parser.parse(raw, dayfirst=True)
    return parsed.date()


def parse_amount(value: str) -> Decimal:
    raw = value.strip()
    if not raw:
        raise ValueError("Valor vazio.")
    cleaned = (
        raw.replace("R$", "")
        .replace("r$", "")
        .replace(" ", "")
        .replace("\u00a0", "")
    )
    if cleaned.count(",") == 1 and cleaned.count(".") > 0:
        cleaned = cleaned.replace(".", "").replace(",", ".")
    elif cleaned.count(",") == 1 and cleaned.count(".") == 0:
        cleaned = cleaned.replace(",", ".")
    elif cleaned.count(".") > 1:
        cleaned = cleaned.replace(".", "")
    try:
        amount = Decimal(cleaned)
    except InvalidOperation as exc:
        raise ValueError("Valor numérico inválido.") from exc
    if amount <= 0:
        raise ValueError("O valor deve ser maior que zero.")
    return amount.quantize(Decimal("0.01"))


def parse_type(value: str) -> TransactionType:
    key = _normalize_header(value)
    mapped = TYPE_ALIASES.get(key)
    if mapped is None:
        raise ValueError("Tipo inválido. Use receita ou despesa.")
    return mapped


def parse_status(value: str) -> TransactionStatus:
    key = _normalize_header(value)
    mapped = STATUS_ALIASES.get(key)
    if mapped is None:
        raise ValueError("Status inválido. Use pago, pendente ou cancelado.")
    return mapped


def parse_csv_bytes(content: bytes, filename: str) -> CsvParseResult:
    settings = get_settings()
    if len(content) > settings.MAX_UPLOAD_BYTES:
        raise ValueError("O arquivo excede o tamanho máximo de 2 MB.")
    if not filename.lower().endswith(".csv"):
        raise ValueError("Envie um arquivo CSV.")

    last_error: Exception | None = None
    frame: pd.DataFrame | None = None
    for encoding in ("utf-8-sig", "utf-8", "latin-1"):
        try:
            frame = pd.read_csv(io.BytesIO(content), encoding=encoding, dtype=str, keep_default_na=False)
            break
        except UnicodeDecodeError as exc:
            last_error = exc
        except pd.errors.EmptyDataError as exc:
            raise ValueError("O arquivo CSV está vazio.") from exc
        except pd.errors.ParserError as exc:
            raise ValueError("Não foi possível ler o CSV. Verifique o formato.") from exc
    if frame is None:
        raise ValueError("Codificação do arquivo não suportada.") from last_error
    if frame.empty:
        raise ValueError("O arquivo CSV não contém registros.")
    if len(frame.index) > settings.MAX_CSV_ROWS:
        raise ValueError(f"O arquivo excede o limite de {settings.MAX_CSV_ROWS} linhas.")

    mapping = _map_headers([str(col) for col in frame.columns])
    missing = [column for column in REQUIRED_CSV_COLUMNS if column not in mapping]
    if missing:
        labels = {
            "date": "data",
            "description": "descricao",
            "category": "categoria",
            "type": "tipo",
            "amount": "valor",
            "status": "status",
        }
        readable = ", ".join(labels[column] for column in missing)
        raise ValueError(f"Colunas obrigatórias ausentes: {readable}.")

    result = CsvParseResult(filename=filename, total_rows=int(len(frame.index)))
    for index, row in frame.iterrows():
        source_row = int(index) + 2
        raw_preview = ",".join(str(value) for value in row.tolist()[:6])
        try:
            date_value = parse_date(_cell(row, mapping, "date"))
            description = _cell(row, mapping, "description")
            if len(description) < 2:
                raise ValueError("Descrição obrigatória.")
            category = _cell(row, mapping, "category")
            if not category:
                raise ValueError("Categoria obrigatória.")
            type_ = parse_type(_cell(row, mapping, "type"))
            amount = parse_amount(_cell(row, mapping, "amount"))
            status = parse_status(_cell(row, mapping, "status"))
            due_raw = _cell(row, mapping, "due_date")
            due_date = parse_date(due_raw) if due_raw else (date_value if status == TransactionStatus.PENDING else None)
            notes = _cell(row, mapping, "notes") or None
            party_name = _cell(row, mapping, "party_name") or None
            result.valid_rows.append(
                ParsedCsvRow(
                    date=date_value,
                    description=description[:255],
                    category=category[:80],
                    type=type_,
                    amount=amount,
                    status=status,
                    due_date=due_date,
                    notes=notes,
                    party_name=party_name[:160] if party_name else None,
                    source_row=source_row,
                )
            )
        except ValueError as exc:
            result.errors.append(
                CsvRowError(row=source_row, field=None, message=str(exc), raw=raw_preview)
            )
    return result
