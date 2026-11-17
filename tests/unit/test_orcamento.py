"""Testes unitários de orçamento e alertas (TU06–TU08; RN02–RN06, RN12, RN13)."""
from datetime import date
from decimal import Decimal

import pytest

from app.services import orcamento
from app.services.erros import RegraNegocioErro
from app.services.orcamento import SituacaoCategoria


@pytest.mark.parametrize("contratado,esperado", [
    ("800", SituacaoCategoria.DENTRO),    # 80%
    ("899.99", SituacaoCategoria.DENTRO),
    ("900", SituacaoCategoria.ATENCAO),   # 90%
    ("950", SituacaoCategoria.ATENCAO),   # 95%
    ("1000", SituacaoCategoria.ATENCAO),  # 100%
    ("1100", SituacaoCategoria.ACIMA),    # 110%
])
def test_tu06_situacao_da_categoria(contratado, esperado):
    """TU06 / RN05."""
    assert orcamento.situacao_categoria(Decimal(contratado), Decimal("1000")) == esperado


def test_tu07_planejado_zero_com_despesa():
    """TU07 / RN05: planejado zero com despesa fica Acima do planejado."""
    assert orcamento.situacao_categoria(Decimal("10"), Decimal("0")) == SituacaoCategoria.ACIMA
    assert orcamento.situacao_categoria(Decimal("0"), Decimal("0")) == SituacaoCategoria.DENTRO


def test_tu08_alerta_de_orcamento_estourado():
    """TU08 / RN06: alerta com o valor excedente."""
    assert orcamento.alerta_orcamento(Decimal("61500"), Decimal("60000")) == Decimal("1500.00")
    assert orcamento.alerta_orcamento(Decimal("60000"), Decimal("60000")) is None


def test_rn04_planejado_maior_que_orcamento():
    assert orcamento.alerta_planejado(Decimal("65000"), Decimal("60000")) == Decimal("5000.00")
    assert orcamento.alerta_planejado(Decimal("50000"), Decimal("60000")) is None


def test_percentual_e_saldo():
    assert orcamento.percentual_utilizado(Decimal("950"), Decimal("1000")) == 95
    assert orcamento.percentual_utilizado(Decimal("10"), Decimal("0")) is None
    assert orcamento.saldo(Decimal("60000"), Decimal("61000")) == Decimal("-1000.00")


def test_rn02_data_do_casamento_posterior_ao_cadastro():
    cadastro = date(2026, 11, 17)
    assert orcamento.validar_data_casamento(date(2026, 11, 18), cadastro) == date(2026, 11, 18)
    for invalida in (cadastro, date(2026, 1, 1)):
        with pytest.raises(RegraNegocioErro) as erro:
            orcamento.validar_data_casamento(invalida, cadastro)
        assert erro.value.codigo == "E05"
    with pytest.raises(RegraNegocioErro) as vazio:
        orcamento.validar_data_casamento(None, cadastro)
    assert vazio.value.codigo == "E01"


def test_rn03_valores():
    assert orcamento.validar_valor_positivo(Decimal("10.005"), "x") == Decimal("10.01")
    for invalido in (Decimal("0"), Decimal("-1")):
        with pytest.raises(RegraNegocioErro) as erro:
            orcamento.validar_valor_positivo(invalido, "x")
        assert erro.value.codigo == "E06"
    with pytest.raises(RegraNegocioErro):
        orcamento.validar_valor_positivo(None, "x")
    assert orcamento.validar_valor_nao_negativo(Decimal("0"), "x") == Decimal("0.00")
    assert orcamento.validar_valor_nao_negativo(None, "x") is None
    with pytest.raises(RegraNegocioErro):
        orcamento.validar_valor_nao_negativo(Decimal("-0.01"), "x")


def test_rn12_rn13_fornecedor_para_despesa():
    orcamento.validar_fornecedor_para_despesa("ORCAMENTO", 1, "Buffet", 1)
    with pytest.raises(RegraNegocioErro) as descartado:
        orcamento.validar_fornecedor_para_despesa("DESCARTADO", 1, "Buffet", 1)
    assert descartado.value.codigo == "E12"
    with pytest.raises(RegraNegocioErro) as outra:
        orcamento.validar_fornecedor_para_despesa("CONTRATADO", 1, "Buffet", 2)
    assert outra.value.codigo == "E07"
    assert "Buffet" in outra.value.mensagem


def test_montar_alertas_completo():
    alertas = orcamento.montar_alertas(
        orcamento_total=Decimal("1000"),
        total_contratado=Decimal("1200"),
        soma_planejado=Decimal("1500"),
        categorias=[("Buffet", Decimal("700"), Decimal("500")), ("Música", Decimal("500"), Decimal("1000"))],
        qtd_atrasadas=2,
        qtd_apos_casamento=1,
    )
    codigos = [a.codigo for a in alertas]
    assert codigos == ["A02", "A05", "A01", "A03", "A04"]
    assert "R$ 200,00" in alertas[0].texto
    assert alertas[2].texto == "Buffet passou do planejado em R$ 200,00."


def test_sem_alertas_quando_tudo_em_ordem():
    assert orcamento.montar_alertas(
        orcamento_total=Decimal("1000"), total_contratado=Decimal("100"), soma_planejado=Decimal("900"),
        categorias=[("Buffet", Decimal("100"), Decimal("900"))], qtd_atrasadas=0, qtd_apos_casamento=0,
    ) == []
