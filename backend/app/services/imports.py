import json
from datetime import datetime, timezone

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.entities import ImportBatch, Notification, Transaction, User
from app.schemas.common import ImportErrorItem, ImportPreviewOut, ImportResultOut
from app.services.categories import CategoryService
from app.services.csv_import import CsvParseResult, parse_csv_bytes


SAMPLE_CSV = """data,descricao,categoria,tipo,valor,status,vencimento,cliente,observacao
03/09/2026,Projeto site institucional,Serviços,receita,4800,pago,,,Fechamento sprint 2
05/09/2026,Mensalidade cliente Norte,Serviços,receita,2200,pendente,10/09/2026,Norte Alimentos,
08/09/2026,Licença design,Software,despesa,189,pago,,,
10/09/2026,Pagamento fornecedor de mídia,Marketing,despesa,1500,pendente,12/09/2026,Agência Ponto,
12/09/2026,Venda de pacote avulso,Vendas,receita,850,pago,,,
"""


def _errors_out(result: CsvParseResult) -> list[ImportErrorItem]:
    return [
        ImportErrorItem(row=item.row, field=item.field, message=item.message, raw=item.raw)
        for item in result.errors
    ]


class ImportService:
    def __init__(self, db: Session):
        self.db = db
        self.categories = CategoryService(db)

    def _read_upload(self, file: UploadFile) -> tuple[bytes, str]:
        settings = get_settings()
        filename = file.filename or "import.csv"
        content = file.file.read(settings.MAX_UPLOAD_BYTES + 1)
        if len(content) > settings.MAX_UPLOAD_BYTES:
            raise ValueError("O arquivo excede o tamanho máximo de 2 MB.")
        if not content:
            raise ValueError("O arquivo está vazio.")
        return content, filename

    def preview(self, file: UploadFile) -> ImportPreviewOut:
        content, filename = self._read_upload(file)
        result = parse_csv_bytes(content, filename)
        sample = [
            {
                "date": row.date.isoformat(),
                "description": row.description,
                "category": row.category,
                "type": row.type.value,
                "amount": float(row.amount),
                "status": row.status.value,
            }
            for row in result.valid_rows[:20]
        ]
        return ImportPreviewOut(
            filename=filename,
            total_rows=result.total_rows,
            valid_count=result.valid_count,
            error_count=result.error_count,
            errors=_errors_out(result),
            valid_sample=sample,
        )

    def confirm(self, user: User, file: UploadFile) -> ImportResultOut:
        content, filename = self._read_upload(file)
        result = parse_csv_bytes(content, filename)
        batch = ImportBatch(
            company_id=user.company_id,
            filename=filename,
            total_rows=result.total_rows,
            imported_count=0,
            error_count=result.error_count,
            errors=json.dumps([item.__dict__ for item in result.errors], ensure_ascii=False),
        )
        self.db.add(batch)
        self.db.flush()

        imported = 0
        now = datetime.now(timezone.utc)
        for row in result.valid_rows:
            category = self.categories.get_or_create(user.company_id, row.category, row.type)
            self.db.add(
                Transaction(
                    company_id=user.company_id,
                    category_id=category.id,
                    import_batch_id=batch.id,
                    type=row.type.value,
                    status=row.status.value,
                    amount=row.amount,
                    date=row.date,
                    due_date=row.due_date,
                    paid_at=now if row.status.value == "paid" else None,
                    party_name=row.party_name,
                    description=row.description,
                    notes=row.notes,
                )
            )
            imported += 1

        batch.imported_count = imported
        self.db.add(
            Notification(
                company_id=user.company_id,
                type="import_completed",
                title="Importação concluída",
                message=(
                    f"{result.total_rows} registros encontrados. "
                    f"{imported} importados. {result.error_count} com erro."
                ),
                channel="in_app",
            )
        )
        self.db.commit()
        self.db.refresh(batch)
        return ImportResultOut(
            id=batch.id,
            filename=batch.filename,
            total_rows=batch.total_rows,
            imported_count=batch.imported_count,
            error_count=batch.error_count,
            errors=_errors_out(result),
        )
