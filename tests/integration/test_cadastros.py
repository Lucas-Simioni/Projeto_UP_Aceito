"""Categorias, fornecedores, convidados e painel via HTTP (UC04–UC06, UC10, UC11; RF04–RF06, RF11–RF13)."""
from datetime import timedelta
from decimal import Decimal

from app.extensions import db
from app.models import Categoria, Convidado, Despesa, Fornecedor
from app.services import convidados, datas, despesas
from tests.conftest import categoria, criar_despesa, criar_fornecedor


# ------------------------------------------------------------------ categorias (UC04)


def test_crud_de_categoria(logado, casal):
    assert logado.post("/orcamento/nova", data={"nome": "Lua de mel", "valor_planejado": "5.000,00"}).status_code == 302
    nova = db.session.scalar(db.select(Categoria).filter_by(nome="Lua de mel"))
    assert nova.valor_planejado == Decimal("5000.00")

    html = logado.post("/orcamento/nova", data={"nome": "lua de mel"}).get_data(as_text=True)
    assert "Já existe uma categoria com este nome." in html
    html = logado.post(f"/orcamento/{nova.id}/editar", data={"nome": "Viagem", "valor_planejado": "-5"}).get_data(as_text=True)
    assert "O valor não pode ser negativo." in html

    assert logado.post(f"/orcamento/{nova.id}/editar", data={"nome": "Viagem", "valor_planejado": "0"}).status_code == 302
    assert db.session.get(Categoria, nova.id).valor_planejado == Decimal("0.00")

    html = logado.post(f"/orcamento/{nova.id}/excluir", follow_redirects=True).get_data(as_text=True)
    assert "Categoria Viagem excluída." in html
    assert db.session.get(Categoria, nova.id) is None


def test_rn14_categoria_com_fornecedor_nao_e_excluida(logado, casal):
    musica = categoria(casal, "Música")
    criar_fornecedor(musica)
    html = logado.post(f"/orcamento/{musica.id}/excluir", follow_redirects=True).get_data(as_text=True)
    assert "não pode ser excluída" in html


def test_orcamento_mostra_situacao_e_aviso_a04(logado, casal):
    buffet = categoria(casal)
    buffet.valor_planejado = Decimal("70000")
    db.session.commit()
    criar_despesa(casal, buffet, valor="65000")
    html = logado.get("/orcamento/").get_data(as_text=True)
    assert "A soma dos valores planejados (R$ 70.000,00) é maior que o orçamento total (R$ 60.000,00)." in html
    assert "O total contratado passou do orçamento em R$ 5.000,00." in html
    assert "Atenção" in html  # 65.000 / 70.000 = 93%


# ------------------------------------------------------------------ fornecedores (UC05, UC06)


def test_crud_de_fornecedor(logado, casal):
    foto = categoria(casal, "Fotografia e vídeo")
    resposta = logado.post("/fornecedores/novo", data={
        "categoria_id": foto.id, "nome": "Estúdio Luz", "telefone": "(11) 98765-4321", "email": "luz@ex.com",
        "valor_orcado": "5.200,00", "status": "ORCAMENTO", "observacoes": "Inclui álbum",
    })
    assert resposta.status_code == 302
    fornecedor = db.session.scalar(db.select(Fornecedor))
    assert fornecedor.valor_orcado == Decimal("5200.00") and fornecedor.telefone == "(11) 98765-4321"

    html = logado.post(f"/fornecedores/{fornecedor.id}/editar", data={
        "categoria_id": foto.id, "nome": "Estúdio Luz", "telefone": "98765-432", "email": "invalido",
        "status": "ORCAMENTO",
    }).get_data(as_text=True)
    assert "Use o formato (99) 99999-9999." in html and "Informe um e-mail válido." in html

    assert "Estúdio Luz" in logado.get(f"/fornecedores/?categoria={foto.id}&status=ORCAMENTO").get_data(as_text=True)
    assert "Nenhum fornecedor com esses filtros" in logado.get("/fornecedores/?status=DESCARTADO").get_data(as_text=True)

    html = logado.post(f"/fornecedores/{fornecedor.id}/excluir", follow_redirects=True).get_data(as_text=True)
    assert "Fornecedor Estúdio Luz excluído." in html


def test_excluir_fornecedor_mantem_despesas(logado, casal):
    buffet = categoria(casal)
    fornecedor = criar_fornecedor(buffet)
    despesa = criar_despesa(casal, buffet, fornecedor=fornecedor)
    logado.post(f"/fornecedores/{fornecedor.id}/excluir")
    db.session.expire_all()
    assert db.session.get(Despesa, despesa.id).fornecedor_id is None


def test_fornecedor_com_despesa_nao_muda_de_categoria(logado, casal):
    buffet = categoria(casal)
    fornecedor = criar_fornecedor(buffet)
    criar_despesa(casal, buffet, fornecedor=fornecedor)
    html = logado.post(f"/fornecedores/{fornecedor.id}/editar", data={
        "categoria_id": categoria(casal, "Música").id, "nome": fornecedor.nome, "status": "CONTRATADO",
    }).get_data(as_text=True)
    assert "a categoria não pode mudar" in html


def test_rf06_comparar_orcamentos_destaca_o_menor(logado, casal):
    buffet = categoria(casal)
    buffet.valor_planejado = Decimal("20000")
    db.session.commit()
    criar_fornecedor(buffet, "Caro", "22000")
    criar_fornecedor(buffet, "Barato", "19800")
    criar_fornecedor(buffet, "Descartado mais barato", "10000", status="DESCARTADO")
    criar_fornecedor(buffet, "Sem valor", "0").valor_orcado = None
    db.session.commit()

    from app.services.fornecedores import comparar_orcamentos

    itens = comparar_orcamentos(db.session.get(Categoria, buffet.id))
    assert [i.fornecedor.nome for i in itens] == ["Barato", "Caro", "Sem valor", "Descartado mais barato"]
    assert [i.menor for i in itens] == [True, False, False, False]
    assert itens[1].diferenca == Decimal("2200.00") and itens[1].percentual == 11
    assert itens[0].cabe_no_planejado is True and itens[1].cabe_no_planejado is False

    html = logado.get(f"/fornecedores/comparar?categoria={buffet.id}").get_data(as_text=True)
    assert "Menor orçamento" in html and html.index("Barato") < html.index("Caro")
    assert logado.get("/fornecedores/comparar").status_code == 200


# ------------------------------------------------------------------ convidados (UC11)


def test_crud_e_rsvp_de_convidados(logado, casal):
    resposta = logado.post("/convidados/novo", data={"nome": "Ana", "grupo": "FAMILIA_NOIVA", "acompanhantes": "2",
                                                      "telefone": "(11) 91234-5678", "continuar": "1"})
    assert resposta.headers["Location"].endswith("/convidados/novo")
    convidado = db.session.scalar(db.select(Convidado))
    assert convidado.status_rsvp == "PENDENTE"

    html = logado.post("/convidados/novo", data={"nome": "Bia", "grupo": "AMIGOS", "acompanhantes": "11"}).get_data(as_text=True)
    assert "O número de acompanhantes deve ficar entre 0 e 10." in html

    resposta = logado.post(f"/convidados/{convidado.id}/rsvp", data={"status": "CONFIRMADO", "filtro_grupo": "FAMILIA_NOIVA"})
    assert resposta.headers["Location"].endswith(f"/convidados/?grupo=FAMILIA_NOIVA#convidado-{convidado.id}")
    assert db.session.get(Convidado, convidado.id).status_rsvp == "CONFIRMADO"
    html = logado.post(f"/convidados/{convidado.id}/rsvp", data={"status": "TALVEZ"}, follow_redirects=True).get_data(as_text=True)
    assert "Status de confirmação inválido." in html

    assert logado.post(f"/convidados/{convidado.id}/editar", data={"nome": "Ana Maria", "grupo": "AMIGOS",
                                                                   "acompanhantes": "1"}).status_code == 302
    convidado = db.session.get(Convidado, convidado.id)
    assert (convidado.nome, convidado.acompanhantes, convidado.status_rsvp) == ("Ana Maria", 1, "CONFIRMADO")

    html = logado.get("/convidados/?status=CONFIRMADO&grupo=AMIGOS").get_data(as_text=True)
    assert "Ana Maria" in html
    html = logado.post(f"/convidados/{convidado.id}/excluir", follow_redirects=True).get_data(as_text=True)
    assert "Convidado Ana Maria excluído." in html


def test_rf13_resumo_e_custo_por_convidado(logado, casal):
    criar_despesa(casal, categoria(casal), valor="6000")
    for nome, acompanhantes, status in (("A", 0, "CONFIRMADO"), ("B", 1, "CONFIRMADO"), ("C", 2, "CONFIRMADO"),
                                        ("D", 3, "RECUSADO"), ("E", 0, "PENDENTE")):
        c = convidados.salvar_convidado(casal, None, nome=nome, grupo="AMIGOS", telefone=None, email=None,
                                        acompanhantes=acompanhantes)
        convidados.alterar_status(c, status)
    html = logado.get("/convidados/").get_data(as_text=True)
    assert "R$ 1.000,00" in html  # 6.000 / 6 pessoas confirmadas
    painel = logado.get("/painel").get_data(as_text=True)
    assert "R$ 1.000,00" in painel and "pessoas confirmadas" in painel


# ------------------------------------------------------------------ painel (UC10)


def test_rf11_painel_com_dados_reais(logado, casal):
    hoje = datas.hoje()
    buffet = categoria(casal)
    buffet.valor_planejado = Decimal("1000")
    db.session.commit()
    despesa = criar_despesa(casal, buffet, valor="1500", parcelas=3, primeiro_vencimento=hoje - timedelta(days=40))
    despesas.pagar_parcela(despesa.parcelas[0], hoje, hoje)

    html = logado.get("/painel").get_data(as_text=True)
    assert "R$ 1.500,00" in html                    # contratado
    assert "R$ 500,00" in html                      # pago
    assert "R$ 58.500,00" in html                   # ainda posso gastar
    assert "Buffet passou do planejado em R$ 500,00." in html          # A01
    assert "Você tem 1 parcela(s) atrasada(s)." in html                 # A05
    assert 'id="grafico-categorias"' in html and "Próximas parcelas" in html


def test_painel_vazio_mostra_estados_vazios(logado):
    html = logado.get("/painel").get_data(as_text=True)
    assert "Nenhuma parcela em aberto" in html
    assert "Defina quanto quer gastar em cada categoria" in html
    assert "—" in html  # custo por convidado sem confirmados


def test_todas_as_telas_renderizam(logado, casal):
    """Fumaça: as 12 telas e as páginas auxiliares respondem 200."""
    fornecedor = criar_fornecedor(categoria(casal))
    despesa = criar_despesa(casal, categoria(casal), fornecedor=fornecedor)
    convidado = convidados.salvar_convidado(casal, None, nome="Ana", grupo="AMIGOS", telefone=None, email=None,
                                            acompanhantes=0)
    cat = categoria(casal)
    for url in ("/painel", "/meu-casamento", "/orcamento/", "/orcamento/nova", f"/orcamento/{cat.id}/editar",
                "/fornecedores/", "/fornecedores/novo", f"/fornecedores/{fornecedor.id}/editar",
                "/fornecedores/comparar", "/despesas/", f"/despesas/?categoria={cat.id}", "/despesas/nova",
                f"/despesas/{despesa.id}", f"/despesas/{despesa.id}/editar", "/parcelas/",
                f"/parcelas/{despesa.parcelas[0].id}/pagar", "/convidados/", "/convidados/novo",
                f"/convidados/{convidado.id}/editar"):
        assert logado.get(url).status_code == 200, url
    assert logado.get("/").headers["Location"].endswith("/painel")
    assert logado.get("/entrar").status_code == 302
    assert logado.get("/criar-conta").status_code == 302
    assert logado.get("/nao-existe").status_code == 404


def test_paginas_publicas(client):
    assert client.get("/").headers["Location"].endswith("/entrar")
    assert client.get("/entrar").status_code == 200
    assert client.get("/criar-conta").status_code == 200
