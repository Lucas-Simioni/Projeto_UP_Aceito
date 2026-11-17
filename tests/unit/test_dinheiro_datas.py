"""Testes unitários de formatação de dinheiro (RNF02), datas e exportação CSV."""
import csv
import io
from datetime import date
from decimal import Decimal
from types import SimpleNamespace

import pytest

from app.services import exportacao
from app.services.datas import hoje, somar_meses
from app.services.dinheiro import formatar_moeda, formatar_numero, interpretar_moeda, quantizar, somar
from app.services.mensagens import mensagem


@pytest.mark.parametrize("texto,esperado", [
    ("1.234,56", "1234.56"),
    ("1234,56", "1234.56"),
    ("1234.56", "1234.56"),
    ("R$ 60.000,00", "60000.00"),
    ("1.000", "1000.00"),
    ("1.000.000", "1000000.00"),
    ("0,5", "0.50"),
    ("15", "15.00"),
    ("-10,00", "-10.00"),
])
def test_interpretar_moeda(texto, esperado):
    assert interpretar_moeda(texto) == Decimal(esperado)


@pytest.mark.parametrize("texto", ["", "abc", "1,234,56", "12,345", "1.2.3"])
def test_interpretar_moeda_invalida(texto):
    with pytest.raises(ValueError):
        interpretar_moeda(texto)


def test_formatar_moeda():
    assert formatar_moeda(Decimal("1234.56")) == "R$ 1.234,56"
    assert formatar_moeda(Decimal("60000")) == "R$ 60.000,00"
    assert formatar_moeda(Decimal("0.5")) == "R$ 0,50"
    assert formatar_moeda(Decimal("-1500")) == "-R$ 1.500,00"
    assert formatar_numero(Decimal("1234567.8")) == "1.234.567,80"


def test_quantizar_e_somar():
    assert quantizar(None) == Decimal("0.00")
    assert quantizar(0.1 + 0.2) == Decimal("0.30")
    assert somar([Decimal("0.10"), Decimal("0.20")]) == Decimal("0.30")


def test_somar_meses():
    assert somar_meses(date(2027, 1, 31), 1) == date(2027, 2, 28)
    assert somar_meses(date(2027, 3, 15), -3) == date(2026, 12, 15)
    assert isinstance(hoje(), date)


def test_mensagens_padronizadas():
    assert mensagem("A01", categoria="Buffet", valor="R$ 10,00") == "Buffet passou do planejado em R$ 10,00."
    assert mensagem("E01") == "Preencha este campo."


def test_csv_neutraliza_formulas():
    convidado = SimpleNamespace(nome="=HYPERLINK(\"x\")", grupo_rotulo="Amigos", telefone=None, email=None,
                                acompanhantes=0, total_pessoas=lambda: 1, status_rotulo="Pendente")
    linhas = list(csv.reader(io.StringIO(exportacao.csv_convidados([convidado])), delimiter=";"))
    assert linhas[0][:2] == ["Nome", "Grupo"]
    assert linhas[1][0] == "'=HYPERLINK(\"x\")"
