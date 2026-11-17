"""Autenticação (UC01, UC02, RN17), segurança (RNF06–RNF08) e casamento (UC03, RN01–RN03)."""
from datetime import timedelta

import pytest

from app import create_app
from app.extensions import db
from app.models import Casamento, Categoria, Usuario
from app.services import datas
from tests.conftest import SENHA, categoria, criar_casamento, criar_despesa, criar_fornecedor, criar_usuario, entrar


def _criar_conta(client, email="nova@exemplo.com", senha="abc12345", confirmar=None, nome="Nova"):
    return client.post("/criar-conta", data={
        "nome": nome, "email": email, "senha": senha, "confirmar_senha": confirmar or senha,
    })


def test_senha_gravada_apenas_como_hash(client):
    """RNF06: a senha nunca é gravada em texto puro."""
    _criar_conta(client)
    usuario = db.session.scalar(db.select(Usuario))
    assert usuario.senha_hash != "abc12345"
    assert "abc12345" not in usuario.senha_hash
    assert usuario.verificar_senha("abc12345") and not usuario.verificar_senha("errada123")


def test_email_duplicado_e02(client):
    criar_usuario("dup@exemplo.com")
    resposta = _criar_conta(client, email="DUP@exemplo.com ")
    assert resposta.status_code == 200
    assert "Já existe uma conta com este e-mail." in resposta.get_data(as_text=True)


@pytest.mark.parametrize("senha", ["abcdefgh", "ab1", "12345678"])
def test_senha_fraca_e04(client, senha):
    resposta = _criar_conta(client, senha=senha)
    assert "A senha precisa ter pelo menos 8 caracteres, com letras e números." in resposta.get_data(as_text=True)
    assert db.session.scalar(db.select(db.func.count(Usuario.id))) == 0


def test_campos_obrigatorios_e_senhas_diferentes(client):
    html = client.post("/criar-conta", data={"nome": "", "email": "x@x.com", "senha": "abc12345",
                                              "confirmar_senha": "abc99999"}).get_data(as_text=True)
    assert "Preencha este campo." in html
    assert "As senhas não são iguais." in html


def test_login_invalido_e03(client, casal):
    resposta = entrar(client, senha="outra1234")
    assert resposta.status_code == 200
    assert "E-mail ou senha incorretos." in resposta.get_data(as_text=True)
    assert "E-mail ou senha incorretos." in entrar(client, "ninguem@x.com").get_data(as_text=True)


def test_rotas_protegidas_exigem_login(client):
    for url in ("/painel", "/orcamento/", "/fornecedores/", "/despesas/", "/parcelas/", "/convidados/",
                "/meu-casamento", "/convidados/exportar.csv", "/parcelas/exportar.csv"):
        resposta = client.get(url)
        assert resposta.status_code == 302, url
        assert "/entrar" in resposta.headers["Location"]


def test_logout(logado):
    assert logado.post("/sair").status_code == 302
    assert logado.get("/painel").status_code == 302


def test_login_redireciona_para_destino_interno_apenas(client, casal):
    resposta = client.post("/entrar?proximo=/convidados/", data={"email": "juliana@exemplo.com", "senha": SENHA})
    assert resposta.headers["Location"].endswith("/convidados/")
    client.post("/sair")
    resposta = client.post("/entrar?proximo=https://malicioso.com", data={"email": "juliana@exemplo.com",
                                                                         "senha": SENHA})
    assert resposta.headers["Location"].endswith("/painel")


def test_login_volta_para_pagina_pedida_antes_do_login(client, casal):
    """Flask-Login manda para /entrar?next=...; depois do login o usuário volta para lá."""
    destino = client.get("/convidados/").headers["Location"]
    resposta = client.post(destino, data={"email": "juliana@exemplo.com", "senha": SENHA})
    assert resposta.headers["Location"].endswith("/convidados/")


def test_csrf_ativo_em_producao_de_formularios():
    """RNF07: sem token CSRF o POST é recusado (400)."""
    aplicacao = create_app("testing")
    aplicacao.config["WTF_CSRF_ENABLED"] = True
    with aplicacao.app_context():
        db.create_all()
        resposta = aplicacao.test_client().post("/entrar", data={"email": "a@a.com", "senha": "x"})
        assert resposta.status_code == 400
        assert "Não foi possível enviar o formulário" in resposta.get_data(as_text=True)
        db.drop_all()


def test_rn01_um_casamento_por_conta(logado, casal):
    """RN01: salvar de novo atualiza o mesmo casamento, sem criar outro nem duplicar categorias."""
    data = (datas.hoje() + timedelta(days=100)).isoformat()
    logado.post("/meu-casamento", data={"nome_casal": "J & R", "data_casamento": data,
                                         "orcamento_total": "70.000,00"})
    assert db.session.scalar(db.select(db.func.count(Casamento.id))) == 1
    assert db.session.scalar(db.select(db.func.count(Categoria.id))) == 8
    assert db.session.scalar(db.select(Casamento)).nome_casal == "J & R"


def test_rn02_rn03_validacoes_do_casamento(client):
    criar_usuario()
    entrar(client)
    html = client.post("/meu-casamento", data={
        "nome_casal": "J & R", "data_casamento": datas.hoje().isoformat(), "orcamento_total": "0",
    }).get_data(as_text=True)
    assert "A data do casamento precisa ser uma data futura." in html
    html = client.post("/meu-casamento", data={
        "nome_casal": "J & R", "data_casamento": (datas.hoje() + timedelta(days=9)).isoformat(),
        "orcamento_total": "0,00",
    }).get_data(as_text=True)
    assert "Informe um valor maior que zero." in html
    html = client.post("/meu-casamento", data={"nome_casal": "", "data_casamento": "31/02/2027",
                                                 "orcamento_total": "abc"}).get_data(as_text=True)
    assert "Preencha este campo." in html and "Informe um valor válido" in html
    assert db.session.scalar(db.select(db.func.count(Casamento.id))) == 0


@pytest.mark.parametrize("rota", [
    "/despesas/{despesa}", "/despesas/{despesa}/editar", "/fornecedores/{fornecedor}/editar",
    "/orcamento/{categoria}/editar", "/parcelas/{parcela}/pagar", "/convidados/{convidado}/editar",
    "/fornecedores/comparar?categoria={categoria}",
])
def test_rnf08_isolamento_get(client, casal, rota):
    """RNF08: nenhum dado de outra conta é acessível pela URL."""
    ids = _dados_de(casal)
    criar_casamento(criar_usuario("intruso@exemplo.com", "Intruso"))
    entrar(client, "intruso@exemplo.com")
    assert client.get(rota.format(**ids)).status_code == 404


@pytest.mark.parametrize("rota", [
    "/despesas/{despesa}/excluir", "/fornecedores/{fornecedor}/excluir", "/orcamento/{categoria}/excluir",
    "/parcelas/{parcela}/estornar", "/parcelas/{parcela}/pagar", "/convidados/{convidado}/excluir",
    "/convidados/{convidado}/rsvp",
])
def test_rnf08_isolamento_post(client, casal, rota):
    ids = _dados_de(casal)
    criar_casamento(criar_usuario("intruso@exemplo.com", "Intruso"))
    entrar(client, "intruso@exemplo.com")
    assert client.post(rota.format(**ids), data={"status": "CONFIRMADO"}).status_code == 404


def test_rnf08_despesa_com_categoria_de_outra_conta(client, casal):
    """Formulário adulterado com categoria/fornecedor de outra conta não é aceito."""
    ids = _dados_de(casal)
    criar_casamento(criar_usuario("intruso@exemplo.com", "Intruso"))
    entrar(client, "intruso@exemplo.com")
    html = client.post("/despesas/nova", data={
        "categoria_id": ids["categoria"], "descricao": "x", "valor_total": "100", "num_parcelas": "1",
        "data_contratacao": datas.hoje().isoformat(), "primeiro_vencimento": datas.hoje().isoformat(),
    }).get_data(as_text=True)
    assert "Escolha uma categoria da lista." in html


def _dados_de(casamento):
    from app.services import convidados

    cat = categoria(casamento)
    fornecedor = criar_fornecedor(cat)
    despesa = criar_despesa(casamento, cat, fornecedor=fornecedor)
    convidado = convidados.salvar_convidado(casamento, None, nome="Ana", grupo="AMIGOS", telefone=None,
                                            email=None, acompanhantes=0)
    return {"categoria": cat.id, "fornecedor": fornecedor.id, "despesa": despesa.id,
            "parcela": despesa.parcelas[0].id, "convidado": convidado.id}
