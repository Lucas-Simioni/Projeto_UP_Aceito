"""Fixtures compartilhadas: aplicação com SQLite em memória e atalhos para montar cenários."""
from datetime import timedelta
from decimal import Decimal

import pytest

from app import create_app
from app.extensions import db
from app.models import Categoria, Fornecedor
from app.services import casamentos, contas, datas, despesas

SENHA = "senha1234"


@pytest.fixture()
def app():
    aplicacao = create_app("testing")
    with aplicacao.app_context():
        db.create_all()
        yield aplicacao
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def hoje():
    return datas.hoje()


# ------------------------------------------------------------------ fábricas de dados


def criar_usuario(email="juliana@exemplo.com", nome="Juliana"):
    return contas.criar_conta(nome, email, SENHA)


def criar_casamento(usuario, orcamento="60000", meses=10):
    casamento, _ = casamentos.salvar_casamento(
        usuario,
        nome_casal="Juliana & Rafael",
        data_casamento=datas.somar_meses(datas.hoje(), meses),
        local="Espaço Jardim",
        orcamento_total=Decimal(orcamento),
        convidados_estimados=150,
    )
    return casamento


def categoria(casamento, nome="Buffet") -> Categoria:
    return next(c for c in casamento.categorias if c.nome == nome)


def criar_fornecedor(cat: Categoria, nome="Fornecedor X", valor="1000", status="ORCAMENTO") -> Fornecedor:
    fornecedor = Fornecedor(categoria_id=cat.id, nome=nome, valor_orcado=Decimal(valor), status=status)
    db.session.add(fornecedor)
    db.session.commit()
    return fornecedor


def criar_despesa(casamento, cat: Categoria, valor="1000", parcelas=3, fornecedor=None,
                  contratacao=None, primeiro_vencimento=None, descricao="Despesa teste"):
    hoje = datas.hoje()
    contratacao = contratacao or hoje - timedelta(days=60)
    dados = despesas.DadosDespesa(
        categoria_id=cat.id,
        fornecedor_id=fornecedor.id if fornecedor else None,
        descricao=descricao,
        valor_total=Decimal(valor),
        data_contratacao=contratacao,
        num_parcelas=parcelas,
        primeiro_vencimento=primeiro_vencimento or hoje + timedelta(days=20),
    )
    despesa, _ = despesas.registrar_despesa(casamento, dados)
    return despesa


def entrar(client, email="juliana@exemplo.com", senha=SENHA):
    return client.post("/entrar", data={"email": email, "senha": senha})


@pytest.fixture()
def casal(app):
    """Usuário com casamento configurado (8 categorias padrão)."""
    usuario = criar_usuario()
    return criar_casamento(usuario)


@pytest.fixture()
def logado(client, casal):
    """Cliente HTTP autenticado como dono de `casal`."""
    resposta = entrar(client)
    assert resposta.status_code == 302
    return client
