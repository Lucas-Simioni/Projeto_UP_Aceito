"""RNF09 (desempenho com volume) e comandos de linha de comando."""
import time
from datetime import timedelta

from app.extensions import db
from app.models import Convidado, Parcela
from app.services import datas
from tests.conftest import categoria, criar_despesa

LIMITE_SEGUNDOS = 2.0


def test_rnf09_paginas_em_ate_2_segundos_com_500_convidados_e_200_parcelas(logado, casal):
    hoje = datas.hoje()
    nomes_categorias = [c.nome for c in casal.categorias]
    for i in range(20):  # 20 despesas x 10 parcelas = 200 parcelas
        criar_despesa(casal, categoria(casal, nomes_categorias[i % 8]), valor="10000", parcelas=10,
                      primeiro_vencimento=hoje + timedelta(days=i - 10), descricao=f"Despesa {i}")
    db.session.add_all(
        Convidado(casamento_id=casal.id, nome=f"Convidado {i}", acompanhantes=i % 3,
                  status_rsvp=("PENDENTE", "CONFIRMADO", "RECUSADO")[i % 3])
        for i in range(500)
    )
    db.session.commit()
    assert db.session.scalar(db.select(db.func.count(Parcela.id))) == 200

    for url in ("/painel", "/parcelas/", "/despesas/", "/convidados/", "/orcamento/",
                "/convidados/exportar.csv", "/parcelas/exportar.csv"):
        inicio = time.perf_counter()
        resposta = logado.get(url)
        duracao = time.perf_counter() - inicio
        assert resposta.status_code == 200, url
        assert duracao < LIMITE_SEGUNDOS, f"{url} levou {duracao:.2f}s"


def test_comando_popular_exemplo(app):
    runner = app.test_cli_runner()
    resultado = runner.invoke(args=["popular-exemplo", "--convidados", "40"])
    assert "Conta de exemplo criada" in resultado.output, resultado.output
    assert db.session.scalar(db.select(db.func.count(Convidado.id))) == 40
    # Uma parcela do buffet fica atrasada de propósito, para a demonstração dos alertas.
    atrasadas = [p for p in db.session.scalars(db.select(Parcela)) if p.situacao(datas.hoje()) == "Atrasada"]
    assert atrasadas

    assert "já existe" in runner.invoke(args=["popular-exemplo"]).output
    assert "senha_hash = scrypt" in runner.invoke(args=["verificar-usuario", "exemplo@aceito.app"]).output
    assert "não encontrado" in runner.invoke(args=["verificar-usuario", "x@x.com"]).output
