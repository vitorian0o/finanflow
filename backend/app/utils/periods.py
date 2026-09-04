from calendar import monthrange
from datetime import date

from dateutil.relativedelta import relativedelta


def month_end(value: date) -> date:
    return date(value.year, value.month, monthrange(value.year, value.month)[1])


def resolve_period(
    period: str,
    date_from: date | None,
    date_to: date | None,
    today: date,
) -> tuple[date, date]:
    period = (period or "this_month").lower()

    if period == "custom":
        if date_from is None or date_to is None:
            raise ValueError("Informe a data inicial e a data final para o período personalizado.")
        if date_from > date_to:
            raise ValueError("A data inicial não pode ser posterior à data final.")
        return date_from, date_to

    if period == "this_month":
        start = today.replace(day=1)
        return start, month_end(today)

    if period == "last_month":
        first_this_month = today.replace(day=1)
        last_month_last_day = first_this_month - relativedelta(days=1)
        return last_month_last_day.replace(day=1), last_month_last_day

    if period == "last_3_months":
        start = (today.replace(day=1) - relativedelta(months=2))
        return start, month_end(today)

    if period == "last_6_months":
        start = (today.replace(day=1) - relativedelta(months=5))
        return start, month_end(today)

    if period == "this_year":
        return date(today.year, 1, 1), date(today.year, 12, 31)

    raise ValueError("Período inválido.")
