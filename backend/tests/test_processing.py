from datetime import date
from decimal import Decimal
from io import BytesIO

from app.services.csv_import import parse_amount, parse_csv_bytes, parse_date, parse_type
from app.utils.money import as_money
from app.utils.periods import resolve_period


def test_parse_amount_brl_formats():
    assert parse_amount("1200") == Decimal("1200.00")
    assert parse_amount("1.200,50") == Decimal("1200.50")
    assert parse_amount("R$ 430,00") == Decimal("430.00")
    assert parse_amount("850.75") == Decimal("850.75")


def test_parse_date_and_type():
    assert parse_date("01/09/2026") == date(2026, 9, 1)
    assert parse_date("2026-09-02") == date(2026, 9, 2)
    assert parse_type("receita").value == "income"
    assert parse_type("despesa").value == "expense"


def test_period_this_month():
    start, end = resolve_period("this_month", None, None, date(2026, 9, 4))
    assert start == date(2026, 9, 1)
    assert end == date(2026, 9, 30)


def test_profit_and_margin_helpers():
    income = Decimal("1000")
    expense = Decimal("250")
    profit = income - expense
    assert as_money(profit) == 750.0
    assert as_money(profit / income * 100) == 75.0


def test_csv_valid_and_invalid_rows():
    content = (
        "data,descricao,categoria,tipo,valor,status\n"
        "01/09/2026,Pagamento fornecedor,Fornecedores,despesa,1200,pago\n"
        "02/09/2026,Venda #1023,Vendas,receita,850,pago\n"
        "03/09/2026,Conta de energia,Operacional,despesa,abc,pago\n"
        "bad-date,Sem valor,Vendas,receita,100,pago\n"
    ).encode("utf-8")
    result = parse_csv_bytes(content, "movimentos.csv")
    assert result.total_rows == 4
    assert result.valid_count == 2
    assert result.error_count == 2
    assert result.valid_rows[0].description == "Pagamento fornecedor"


def test_csv_missing_columns():
    content = "foo,bar\n1,2\n".encode("utf-8")
    try:
        parse_csv_bytes(content, "bad.csv")
        assert False, "should have failed"
    except ValueError as exc:
        assert "Colunas obrigatórias" in str(exc)


def test_csv_from_bytesio_filename():
    payload = BytesIO(
        "data,descricao,categoria,tipo,valor,status\n01/09/2026,Teste,Vendas,receita,10,pago\n".encode()
    )
    result = parse_csv_bytes(payload.read(), "ok.csv")
    assert result.valid_count == 1
