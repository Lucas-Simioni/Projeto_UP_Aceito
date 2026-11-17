"""Cenários de integração TI01–TI07 do plano de testes (seção 16)."""
import csv
import io
from datetime import timedelta
from decimal import Decimal

from app.extensions import db
from app.models import Despesa, Fornecedor, Parcela
from app.services import datas
from tests.conftest import categoria, criar_casamento, criar_despesa, criar_fornecedor, criar_usuario, entrar


def test_ti01_criar_conta_login_configurar_casamento_e_abrir_painel(client):
    """TI01: criar conta -> login -> configurar casamento -> painel com 8 categorias padrão (RF04)."""
    resposta = client.post("/criar-conta", data={
        "nome": "Juliana", "email": "ju@exemplo.com", "senha": "abc12345", "confirmar_senha": "abc12345",
    })
    assert resposta.status_code == 302 and resposta.headers["Location"].endswith("/meu-casamento")

    # Sem casamento configurado, o painel leva para T03 (primeiro acesso).
    assert client.get("/painel").headers["Location"].endswith("/meu-casamento")

    client.post("/sair")
    assert entrar(client, "ju@exemplo.com", "abc12345").status_code == 302

    data = (datas.hoje() + timedelta(days=300)).isoformat()
    resposta = client.post("/meu-casamento", data={
        "nome_casal": "Juliana & Rafael", "data_casamento": data, "local": "Jardim",
        "orcamento_total": "60.000,00", "convidados_estimados": "150",
    })
    assert resposta.status_code == 302

    pagina = client.get("/orcamento/").get_data(as_text=True)
    for nome in ("Local", "Buffet", "Decoração", "Fotografia e vídeo", "Música", "Trajes",
                 "Convites e papelaria", "Outros"):
        assert nome in pagina
    painel = client.get("/painel")
    assert painel.status_code == 200
    html = painel.get_data(as_text=True)
    assert "Juliana &amp; Rafael" in html and "R$ 60.000,00" in html and "300" in html


def test_ti02_registrar_despesa_de_mil_em_tres_vezes(logado, casal):
    """TI02: 1 despesa e 3 parcelas gravadas; soma = 1.000,00."""
    buffet = categoria(casal)
    resposta = logado.post("/despesas/nova", data={
        "categoria_id": buffet.id, "fornecedor_id": "", "descricao": "Sinal do buffet",
        "valor_total": "1.000,00", "data_contratacao": datas.hoje().isoformat(), "num_parcelas": "3",
        "primeiro_vencimento": (datas.hoje() + timedelta(days=10)).isoformat(),
    })
    assert resposta.status_code == 302
    despesas = db.session.scalars(db.select(Despesa)).all()
    assert len(despesas) == 1
    parcelas = db.session.scalars(db.select(Parcela).order_by(Parcela.numero)).all()
    assert [p.valor for p in parcelas] == [Decimal("333.34"), Decimal("333.33"), Decimal("333.33")]
    assert sum(p.valor for p in parcelas) == Decimal("1000.00")
    # Mostra a despesa com as parcelas (UC07 passo 7) e a mensagem S01.
    detalhe = logado.get(resposta.headers["Location"]).get_data(as_text=True)
    assert "Salvo com sucesso." in detalhe and "R$ 333,34" in detalhe


def test_ti03_usuario_nao_acessa_dados_de_outro(client, casal):
    """TI03 / RNF08: usuário A tenta abrir a despesa do usuário B pela URL -> 404."""
    despesa_b = criar_despesa(casal, categoria(casal))
    criar_casamento(criar_usuario("a@exemplo.com", "Ana"))
    entrar(client, "a@exemplo.com")
    resposta = client.get(f"/despesas/{despesa_b.id}")
    assert resposta.status_code == 404
    assert "Página não encontrada" in resposta.get_data(as_text=True)


def test_ti04_excluir_categoria_com_despesa(logado, casal):
    """TI04 / RN14: exclusão bloqueada com a mensagem E10."""
    buffet = categoria(casal)
    criar_despesa(casal, buffet)
    resposta = logado.post(f"/orcamento/{buffet.id}/excluir", follow_redirects=True)
    assert "Esta categoria tem fornecedores ou despesas e não pode ser excluída." in resposta.get_data(as_text=True)
    assert db.session.get(type(buffet), buffet.id) is not None


def test_ti05_pagar_e_estornar_parcela(logado, casal):
    """TI05: situação muda para Paga e depois volta para Pendente ou Atrasada."""
    despesa = criar_despesa(casal, categoria(casal))
    parcela = despesa.parcelas[0]
    hoje = datas.hoje()

    resposta = logado.post(f"/parcelas/{parcela.id}/pagar", data={"data_pagamento": hoje.isoformat()},
                           follow_redirects=True)
    assert "Pagamento registrado." in resposta.get_data(as_text=True)
    db.session.refresh(parcela)
    assert parcela.situacao(hoje) == "Paga"

    resposta = logado.post(f"/parcelas/{parcela.id}/estornar", follow_redirects=True)
    assert "Pagamento estornado." in resposta.get_data(as_text=True)
    db.session.refresh(parcela)
    assert parcela.data_pagamento is None
    assert parcela.situacao(hoje) in ("Pendente", "Atrasada", "Vence em breve")


def test_ti06_despesa_para_fornecedor_em_orcamento_vira_contratado(logado, casal):
    """TI06 / RN12: status do fornecedor muda para Contratado."""
    foto = categoria(casal, "Fotografia e vídeo")
    fornecedor = criar_fornecedor(foto, "Estúdio Luz", "5000")
    logado.post("/despesas/nova", data={
        "categoria_id": foto.id, "fornecedor_id": fornecedor.id, "descricao": "Fotos",
        "valor_total": "4.000,00", "data_contratacao": datas.hoje().isoformat(), "num_parcelas": "4",
        "primeiro_vencimento": (datas.hoje() + timedelta(days=5)).isoformat(),
    })
    assert db.session.get(Fornecedor, fornecedor.id).status == "CONTRATADO"


def test_ti07_exportar_convidados_csv(logado, casal):
    """TI07: arquivo com cabeçalho e uma linha por convidado."""
    for nome in ("Ana Souza", "Bruno Lima", "Carla Dias"):
        logado.post("/convidados/novo", data={"nome": nome, "grupo": "AMIGOS", "acompanhantes": "1"})
    resposta = logado.get("/convidados/exportar.csv")
    assert resposta.status_code == 200
    assert resposta.mimetype == "text/csv"
    assert "attachment" in resposta.headers["Content-Disposition"]
    texto = resposta.get_data(as_text=True).lstrip("﻿")
    linhas = list(csv.reader(io.StringIO(texto), delimiter=";"))
    assert linhas[0] == ["Nome", "Grupo", "Telefone", "E-mail", "Acompanhantes", "Total de pessoas", "Confirmação"]
    assert len(linhas) == 4
    assert linhas[1][:2] == ["Ana Souza", "Amigos"]
