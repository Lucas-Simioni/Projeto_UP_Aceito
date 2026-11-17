"""Testes unitários das regras de parcelamento (TU01–TU05, TU09, TU10)."""
from datetime import date, timedelta
from decimal import Decimal
from types import SimpleNamespace

import pytest

from app.services.erros import RegraNegocioErro
from app.services.parcelamento import (
    FiltroParcela,
    SituacaoParcela,
    dividir_valor,
    gerar_parcelas,
    gerar_vencimentos,
    parcela_atende_filtro,
    parcelas_apos_casamento,
    situacao_parcela,
    validar_data_pagamento,
)

HOJE = date(2027, 3, 10)


def test_tu01_mil_reais_em_tres_vezes():
    """TU01 / RN07: R$ 1.000,00 em 3x = 333,34 + 333,33 + 333,33."""
    parcelas = gerar_parcelas(Decimal("1000.00"), 3, date(2027, 1, 10))
    assert [p.valor for p in parcelas] == [Decimal("333.34"), Decimal("333.33"), Decimal("333.33")]
    assert sum(p.valor for p in parcelas) == Decimal("1000.00")
    assert [p.numero for p in parcelas] == [1, 2, 3]


def test_tu02_parcela_unica():
    """TU02 / RN07: R$ 500,00 em 1x = uma parcela de 500,00."""
    parcelas = gerar_parcelas(Decimal("500.00"), 1, date(2027, 1, 10))
    assert len(parcelas) == 1
    assert parcelas[0].valor == Decimal("500.00")


@pytest.mark.parametrize("quantidade", [0, 25, -1])
def test_tu03_numero_de_parcelas_fora_do_limite(quantidade):
    """TU03 / RN08: 0 ou 25 parcelas -> erro E13."""
    with pytest.raises(RegraNegocioErro) as erro:
        gerar_parcelas(Decimal("1000"), quantidade, date(2027, 1, 10))
    assert erro.value.codigo == "E13"
    assert erro.value.campo == "num_parcelas"


def test_tu04_vencimentos_no_fim_do_mes():
    """TU04 / RN08: 31/01/2027 em 3x -> 31/01, 28/02 e 31/03/2027."""
    assert gerar_vencimentos(date(2027, 1, 31), 3) == [date(2027, 1, 31), date(2027, 2, 28), date(2027, 3, 31)]


def test_vencimentos_virada_de_ano_e_ano_bissexto():
    assert gerar_vencimentos(date(2027, 12, 31), 3) == [date(2027, 12, 31), date(2028, 1, 31), date(2028, 2, 29)]


@pytest.mark.parametrize("valor,quantidade", [
    ("1000", 3), ("0.05", 3), ("12345.67", 24), ("99.99", 7), ("0.24", 24), ("60000", 11),
])
def test_soma_das_parcelas_sempre_igual_ao_total(valor, quantidade):
    valores = dividir_valor(Decimal(valor), quantidade)
    assert sum(valores) == Decimal(valor)
    assert all(v > 0 for v in valores)
    # A diferença de centavos fica só na primeira parcela.
    assert len(set(valores[1:])) <= 1
    assert valores[0] >= valores[-1]


def test_valor_menor_que_um_centavo_por_parcela():
    with pytest.raises(RegraNegocioErro) as erro:
        dividir_valor(Decimal("0.02"), 3)
    assert erro.value.codigo == "E06"


@pytest.mark.parametrize("valor", ["0", "-10"])
def test_valor_total_deve_ser_positivo(valor):
    with pytest.raises(RegraNegocioErro) as erro:
        dividir_valor(Decimal(valor), 2)
    assert erro.value.codigo == "E06"


def test_numero_de_parcelas_nao_inteiro():
    with pytest.raises(RegraNegocioErro):
        dividir_valor(Decimal("100"), "3")
    with pytest.raises(RegraNegocioErro):
        dividir_valor(Decimal("100"), True)


@pytest.mark.parametrize("vencimento,pagamento,esperado", [
    (HOJE - timedelta(days=5), HOJE - timedelta(days=6), SituacaoParcela.PAGA),
    (HOJE - timedelta(days=1), None, SituacaoParcela.ATRASADA),
    (HOJE + timedelta(days=3), None, SituacaoParcela.VENCE_EM_BREVE),
    (HOJE + timedelta(days=20), None, SituacaoParcela.PENDENTE),
])
def test_tu05_situacao_da_parcela(vencimento, pagamento, esperado):
    """TU05 / RN10: Paga / Atrasada / Vence em breve / Pendente."""
    assert situacao_parcela(vencimento, pagamento, HOJE) == esperado


def test_situacao_limites_de_sete_dias():
    assert situacao_parcela(HOJE, None, HOJE) == SituacaoParcela.VENCE_EM_BREVE
    assert situacao_parcela(HOJE + timedelta(days=7), None, HOJE) == SituacaoParcela.VENCE_EM_BREVE
    assert situacao_parcela(HOJE + timedelta(days=8), None, HOJE) == SituacaoParcela.PENDENTE


def test_tu09_parcelas_apos_o_casamento():
    """TU09 / RN09: só a parcela depois da data do casamento entra na lista."""
    casamento = date(2027, 6, 1)
    antes = SimpleNamespace(data_vencimento=date(2027, 5, 31))
    no_dia = SimpleNamespace(data_vencimento=date(2027, 6, 1))
    depois = SimpleNamespace(data_vencimento=date(2027, 6, 2))
    assert parcelas_apos_casamento([antes, no_dia, depois], casamento) == [depois]


def test_tu10_data_de_pagamento_invalida():
    """TU10 / RN11: data futura e data antes da contratação geram E08."""
    contratacao = date(2027, 1, 15)
    with pytest.raises(RegraNegocioErro) as futura:
        validar_data_pagamento(HOJE + timedelta(days=1), contratacao, HOJE)
    with pytest.raises(RegraNegocioErro) as anterior:
        validar_data_pagamento(date(2027, 1, 14), contratacao, HOJE)
    assert futura.value.codigo == anterior.value.codigo == "E08"


def test_data_de_pagamento_valida_e_ausente():
    contratacao = date(2027, 1, 15)
    assert validar_data_pagamento(HOJE, contratacao, HOJE) == HOJE
    assert validar_data_pagamento(contratacao, contratacao, HOJE) == contratacao
    with pytest.raises(RegraNegocioErro) as erro:
        validar_data_pagamento(None, contratacao, HOJE)
    assert erro.value.codigo == "E01"


@pytest.mark.parametrize("filtro,vencimento,pagamento,esperado", [
    (FiltroParcela.TODAS, HOJE, None, True),
    (FiltroParcela.PENDENTES, HOJE - timedelta(days=3), None, True),
    (FiltroParcela.PENDENTES, HOJE, HOJE, False),
    (FiltroParcela.ATRASADAS, HOJE - timedelta(days=1), None, True),
    (FiltroParcela.ATRASADAS, HOJE, None, False),
    (FiltroParcela.PAGAS, HOJE, HOJE, True),
    (FiltroParcela.PAGAS, HOJE, None, False),
    (FiltroParcela.PROXIMOS_30, HOJE + timedelta(days=30), None, True),
    (FiltroParcela.PROXIMOS_30, HOJE + timedelta(days=31), None, False),
    (FiltroParcela.PROXIMOS_30, HOJE - timedelta(days=1), None, False),
])
def test_filtros_de_parcelas(filtro, vencimento, pagamento, esperado):
    """RF10."""
    assert parcela_atende_filtro(vencimento, pagamento, filtro, HOJE) is esperado
