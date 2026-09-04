from sqlalchemy.orm import Session

from app.core.constants import DEFAULT_CATEGORIES
from app.core.security import create_access_token, hash_password, verify_password
from app.models.entities import Category, Company, User
from app.repositories.base import UserRepository
from app.schemas.common import LoginRequest, RegisterRequest, TokenResponse, UserOut


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.users = UserRepository(db)

    def register(self, payload: RegisterRequest) -> TokenResponse:
        if self.users.get_by_email(payload.email):
            raise ValueError("Já existe uma conta com este e-mail.")

        company = Company(name=payload.company_name.strip())
        self.db.add(company)
        self.db.flush()

        user = User(
            company_id=company.id,
            name=payload.name.strip(),
            email=payload.email.lower(),
            password_hash=hash_password(payload.password),
        )
        self.db.add(user)

        for type_, names in DEFAULT_CATEGORIES.items():
            for name in names:
                self.db.add(
                    Category(
                        company_id=company.id,
                        name=name,
                        type=type_.value,
                        is_default=True,
                    )
                )

        self.db.commit()
        self.db.refresh(user)
        return TokenResponse(access_token=create_access_token(user_id=user.id, company_id=user.company_id))

    def login(self, payload: LoginRequest) -> TokenResponse:
        user = self.users.get_by_email(payload.email)
        if user is None or not verify_password(payload.password, user.password_hash):
            raise ValueError("E-mail ou senha inválidos.")
        return TokenResponse(access_token=create_access_token(user_id=user.id, company_id=user.company_id))

    def me(self, user: User) -> UserOut:
        self.db.refresh(user)
        return UserOut.model_validate(user)
