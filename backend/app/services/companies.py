from sqlalchemy.orm import Session

from app.models.entities import Company
from app.schemas.common import CompanyOut, CompanyUpdate


class CompanyService:
    def __init__(self, db: Session):
        self.db = db

    def get(self, company_id) -> CompanyOut:
        company = self.db.get(Company, company_id)
        if company is None:
            raise LookupError("Empresa não encontrada.")
        return CompanyOut.model_validate(company)

    def update(self, company_id, payload: CompanyUpdate) -> CompanyOut:
        company = self.db.get(Company, company_id)
        if company is None:
            raise LookupError("Empresa não encontrada.")
        company.name = payload.name.strip()
        self.db.commit()
        self.db.refresh(company)
        return CompanyOut.model_validate(company)
