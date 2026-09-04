from decimal import Decimal, ROUND_HALF_UP

TWOPLACES = Decimal("0.01")


def as_money(value: Decimal | int | float | str | None) -> float:
    if value is None:
        return 0.0
    quantized = Decimal(str(value)).quantize(TWOPLACES, rounding=ROUND_HALF_UP)
    return float(quantized)


def to_decimal(value: Decimal | int | float | str) -> Decimal:
    return Decimal(str(value)).quantize(TWOPLACES, rounding=ROUND_HALF_UP)
