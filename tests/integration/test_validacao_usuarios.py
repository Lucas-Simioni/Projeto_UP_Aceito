"""Correções vindas da validação com testadores (docs/situacao-3-validacao/laudo-de-qualidade.md)."""
from datetime import timedelta

import pytest

from app.extensions import db
from app.forms.base import formatar_telefone
from app.models import Casamento, Convidado, Despesa, Fornecedor
from app.services import datas
from app.services.mensagens import mensagem_exclusao
from tests.conftest import categoria


# ------------------------------------------------------------------ Q01: concordância da mensagem S04


def test_q01_mensagem_de_exclusao_concorda_com_o_genero():
    assert mensagem_exclusao("Fornecedor X") == "Fornecedor X excluído."
    assert mensagem_exclusao("Categoria Viagem", feminino=True) == "Categoria Viagem excluída."


# ------------------------------------------------------------------ Q02: campos numéricos apagados


def test_q02_acompanhantes_em_branco_conta_como_zero(logado, casal):
    resposta = logado.post("/convidados/novo", data={"nome": "Primo", "grupo": "AMIGOS", "acompanhantes": ""})
    assert resposta.status_code == 302
    assert db.session.scalar(db.select(Convidado)).acompanhantes == 0


def test_q02_numero_de_parcelas_em_branco_pede_preenchimento(logado, casal):
    hoje = datas.hoje()
    html = logado.post("/despesas/nova", data={
        "categoria_id": categoria(casal).id, "descricao": "Buffet", "valor_total": "1.000,00",
        "data_contratacao": hoje.isoformat(), "num_parcelas": "", "primeiro_vencimento": hoje.isoformat(),
    }).get_data(as_text=True)
    assert "Preencha este campo." in html and "inteiro não é válido" not in html
    assert db.session.scalar(db.select(Despesa)) is None


def test_q02_numero_com_virgula_tem_mensagem_clara(logado, casal):
    html = logado.post("/convidados/novo", data={"nome": "Primo", "grupo": "AMIGOS",
                                                 "acompanhantes": "1,5"}).get_data(as_text=True)
    assert "Informe um número inteiro, sem vírgula." in html


def test_q02_convidados_estimados_em_branco_continua_opcional(logado, casal):
    resposta = logado.post("/meu-casamento", data={
        "nome_casal": "Juliana & Rafael", "data_casamento": casal.data_casamento.isoformat(),
        "orcamento_total": "60.000,00", "convidados_estimados": "",
    })
    assert resposta.status_code == 302
    assert db.session.get(Casamento, casal.id).convidados_estimados is None


# ------------------------------------------------------------------ Q03: telefone digitado sem máscara


@pytest.mark.parametrize("digitado, gravado", [
    ("11987654321", "(11) 98765-4321"),
    ("+55 11 98765-4321", "(11) 98765-4321"),
    ("(11)3456 7890", "(11) 3456-7890"),
    ("(11) 98765-4321", "(11) 98765-4321"),
    ("98765-432", "98765-432"),  # dígitos de menos: fica como veio e o validador avisa
])
def test_q03_telefone_e_padronizado(digitado, gravado):
    assert formatar_telefone(digitado) == gravado


def test_q03_telefone_sem_mascara_e_aceito_nos_cadastros(logado, casal):
    assert logado.post("/convidados/novo", data={"nome": "Tia Rosa", "grupo": "FAMILIA_NOIVO",
                                                 "acompanhantes": "1", "telefone": "11988887777"}).status_code == 302
    assert db.session.scalar(db.select(Convidado)).telefone == "(11) 98888-7777"
    assert logado.post("/fornecedores/novo", data={"categoria_id": categoria(casal).id, "nome": "Buffet Bom",
                                                   "telefone": "1134567890", "status": "ORCAMENTO"}).status_code == 302
    assert db.session.scalar(db.select(Fornecedor)).telefone == "(11) 3456-7890"


# ------------------------------------------------------------------ Q04: valor digitado sem formatação


def test_q04_previa_devolve_o_total_formatado(logado, casal):
    hoje = datas.hoje() + timedelta(days=5)
    dados = logado.get(f"/despesas/previa?valor=4000&parcelas=4&vencimento={hoje.isoformat()}").get_json()
    assert dados["ok"] and dados["total"] == "R$ 4.000,00"
    assert [p["valor"] for p in dados["parcelas"]] == ["R$ 1.000,00"] * 4
