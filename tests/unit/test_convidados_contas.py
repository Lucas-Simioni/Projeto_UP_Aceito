"""Testes unitários de convidados (TU11, TU12, RN16) e contas (TU13)."""
from decimal import Decimal
from types import SimpleNamespace

import pytest

from app.services import convidados
from app.services.contas import normalizar_email, validar_senha
from app.services.erros import RegraNegocioErro


def _convidado(status, acompanhantes=0):
    return SimpleNamespace(status_rsvp=status, acompanhantes=acompanhantes)


def test_tu11_total_de_pessoas_confirmadas():
    """TU11 / RN15: 3 confirmados com 0, 1 e 2 acompanhantes + 1 recusado = 6 pessoas."""
    lista = [
        _convidado("CONFIRMADO", 0),
        _convidado("CONFIRMADO", 1),
        _convidado("CONFIRMADO", 2),
        _convidado("RECUSADO", 3),
    ]
    assert convidados.total_pessoas_confirmadas(lista) == 6


def test_tu12_custo_por_convidado_sem_confirmados():
    """TU12 / RN15: sem confirmados não há valor (a tela exibe “—”)."""
    assert convidados.custo_por_convidado(Decimal("30000"), 0) is None


def test_custo_por_convidado():
    assert convidados.custo_por_convidado(Decimal("1000"), 3) == Decimal("333.33")


def test_resumo_de_convidados():
    resumo = convidados.resumo_convidados([
        _convidado("CONFIRMADO", 1), _convidado("PENDENTE", 2), _convidado("RECUSADO", 0), _convidado("PENDENTE"),
    ])
    assert (resumo.cadastrados, resumo.confirmados, resumo.pendentes, resumo.recusados) == (4, 1, 2, 1)
    assert resumo.pessoas_confirmadas == 2
    assert resumo.pessoas_convidadas == 2 + 3 + 1


@pytest.mark.parametrize("valor", [0, 10])
def test_rn16_acompanhantes_validos(valor):
    assert convidados.validar_acompanhantes(valor) == valor


@pytest.mark.parametrize("valor", [-1, 11, "2", True])
def test_rn16_acompanhantes_invalidos(valor):
    with pytest.raises(RegraNegocioErro) as erro:
        convidados.validar_acompanhantes(valor)
    assert erro.value.codigo == "E09"


def test_rn16_acompanhantes_vazio():
    with pytest.raises(RegraNegocioErro) as erro:
        convidados.validar_acompanhantes(None)
    assert erro.value.codigo == "E01"


@pytest.mark.parametrize("senha,valida", [
    ("abc12345", True),   # TU13: válida
    ("abcdefgh", False),  # TU13: sem número
    ("ab1", False),       # TU13: curta
    ("12345678", False),  # sem letra
    ("", False),
    (None, False),
    ("çãoé1234", True),
])
def test_tu13_validar_senha(senha, valida):
    """TU13 / RN17."""
    assert validar_senha(senha) is valida


def test_normalizar_email():
    assert normalizar_email("  Juliana@Exemplo.COM ") == "juliana@exemplo.com"
