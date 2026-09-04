from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.config import get_settings
from app.database.session import SessionLocal
from app.services.insights import InsightService

scheduler = BackgroundScheduler()


def _run_daily_insights() -> None:
    db = SessionLocal()
    try:
        InsightService(db).run_for_all_companies()
    finally:
        db.close()


def start_scheduler() -> None:
    settings = get_settings()
    if scheduler.running:
        return
    scheduler.configure(timezone=settings.TZ)
    scheduler.add_job(
        _run_daily_insights,
        CronTrigger(hour=8, minute=0, timezone=settings.TZ),
        id="daily_insights",
        replace_existing=True,
    )
    scheduler.start()


def stop_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
