from fastapi import APIRouter

from app.api.v1.accounts import router as accounts_router
from app.api.v1.auth import router as auth_router
from app.api.v1.categories import router as categories_router
from app.api.v1.dashboard import company_router, router as dashboard_router
from app.api.v1.imports import router as imports_router
from app.api.v1.notifications import router as notifications_router
from app.api.v1.reports import insights_router, router as reports_router
from app.api.v1.transactions import router as transactions_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(dashboard_router)
api_router.include_router(company_router)
api_router.include_router(categories_router)
api_router.include_router(transactions_router)
api_router.include_router(accounts_router)
api_router.include_router(imports_router)
api_router.include_router(reports_router)
api_router.include_router(insights_router)
api_router.include_router(notifications_router)
