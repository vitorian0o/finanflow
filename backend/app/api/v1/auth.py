from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.v1.errors import raise_from_service
from app.core.deps import get_current_user, get_db
from app.models.entities import User
from app.schemas.common import LoginRequest, RegisterRequest, TokenResponse, UserOut
from app.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=TokenResponse, status_code=201)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    try:
        return AuthService(db).register(payload)
    except Exception as exc:
        raise_from_service(exc)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    try:
        return AuthService(db).login(payload)
    except Exception as exc:
        raise_from_service(exc)


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return AuthService(db).me(current_user)
