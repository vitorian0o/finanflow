from datetime import date, datetime
from zoneinfo import ZoneInfo

from app.core.config import get_settings


def now_in_app_tz() -> datetime:
    return datetime.now(ZoneInfo(get_settings().TZ))


def today_in_app_tz() -> date:
    return now_in_app_tz().date()
