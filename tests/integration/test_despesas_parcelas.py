"""Despesas, parcelas e pagamentos via HTTP (UC07–UC09; RN07–RN14, RF08, RF10, RF14)."""
import csv
import io
from datetime import timedelta
from decimal import Decimal

from app.extensions import db
from app.models import Despesa, Fornecedor, Parcela
from app.services import datas, despesas
from tests.conftest import categoria, criar_despesa, criar_fornecedor


def _form(cat, **extra):
    hoje = datas.hoje()
    dados = {
        "categoria_id": cat.id, "fornecedor_id": "", "descricao": "Despesa", "valor_total": "1.000,00",
        "data_contratacao": (hoje - timedelta(days=30)).isoformat(), "num_parcelas": "2",
        "primeiro_vencimento": (hoje + timedelta(days=15)).isoformat(),
    }
    dados.update(extra)
    return dados


def test_rn13_fornecedor_de_outra_categoria_e07(logado, casal):
    fornecedor = criar_fornecedor(categoria(casal, "Música"), "Banda")
    html = logado.post("/despesas/nova", data=_form(categoria(casal), fornecedor_id=fornecedor.id)).get_data(as_text=True)
    assert "Este fornecedor é da categoria Música." in html
    assert db.session.scalar(db.select(db.func.count(Despesa.id))) == 0


def test_rn12_fornecedor_descartado_e12(logado, casal):
    buffet = categoria(casal)
    fornecedor = criar_fornecedor(buffet, "Buffet Caro", status="DESCARTADO")
    html = logado.post("/despesas/nova", data=_form(buffet, fornecedor_id=fornecedor.id)).get_data(as_text=True)
    assert "Fornecedor descartado não pode receber despesas." in html


def test_validacoes_do_formulario_de_despesa(logado, casal):
    buffet = categoria(casal)
    html = logado.post("/despesas/nova", data=_form(buffet, num_parcelas="25")).get_data(as_text=True)
    assert "O número de parcelas deve ficar entre 1 e 24." in html
    html = logado.post("/despesas/nova", data=_form(buffet, valor_total="0,00")).get_data(as_text=True)
    assert "Informe um valor maior que zero." in html
    html = logado.post("/despesas/nova", data=_form(buffet, descricao="")).get_data(as_text=True)
    assert "Preencha este campo." in html
    # UC07 4a: o formulário continua preenchido.
    assert 'value="1.000,00"' in html


def test_avisos_a01_a02_a03_apos_registrar(logado, casal):
    """UC07 fluxos 7a e 7b: a despesa é gravada e os avisos aparecem."""
    buffet = categoria(casal)
    buffet.valor_planejado = Decimal("1000")
    db.session.commit()
    vencimento = casal.data_casamento - timedelta(days=15)
    html = logado.post("/despesas/nova", data=_form(
        buffet, valor_total="70.000,00", num_parcelas="3", primeiro_vencimento=vencimento.isoformat(),
    ), follow_redirects=True).get_data(as_text=True)
    assert "Buffet passou do planejado em R$ 69.000,00." in html
    assert "O total contratado passou do orçamento em R$ 10.000,00." in html
    assert "2 parcela(s) vencem depois da data do casamento." in html
    assert db.session.scalar(db.select(db.func.count(Despesa.id))) == 1


def test_rf08_editar_regera_parcelas(logado, casal):
    buffet = categoria(casal)
    despesa = criar_despesa(casal, buffet, valor="900", parcelas=3)
    resposta = logado.post(f"/despesas/{despesa.id}/editar", data=_form(
        buffet, descricao="Buffet", valor_total="1.000,00", num_parcelas="4",
        data_contratacao=despesa.data_contratacao.isoformat(),
        primeiro_vencimento=despesa.primeiro_vencimento.isoformat(),
    ))
    assert resposta.status_code == 302
    db.session.expire_all()
    despesa = db.session.get(Despesa, despesa.id)
    assert despesa.num_parcelas == 4
    assert [p.valor for p in despesa.parcelas] == [Decimal("250.00")] * 4
    assert db.session.scalar(db.select(db.func.count(Parcela.id))) == 4


def test_rn14_nao_altera_valor_nem_exclui_com_parcela_paga(logado, casal):
    buffet = categoria(casal)
    despesa = criar_despesa(casal, buffet, valor="900", parcelas=3)
    despesas.pagar_parcela(despesa.parcelas[0], datas.hoje(), datas.hoje())
    form = _form(buffet, valor_total="1.200,00", num_parcelas="3",
                 data_contratacao=despesa.data_contratacao.isoformat(),
                 primeiro_vencimento=despesa.primeiro_vencimento.isoformat())
    html = logado.post(f"/despesas/{despesa.id}/editar", data=form).get_data(as_text=True)
    assert "Esta despesa tem parcelas pagas." in html

    # Descrição pode mudar mesmo com parcela paga.
    form.update(valor_total="900,00", descricao="Novo nome")
    assert logado.post(f"/despesas/{despesa.id}/editar", data=form).status_code == 302
    assert db.session.get(Despesa, despesa.id).descricao == "Novo nome"

    html = logado.post(f"/despesas/{despesa.id}/excluir", follow_redirects=True).get_data(as_text=True)
    assert "Estorne os pagamentos antes de alterar o valor ou excluir." in html
    assert db.session.get(Despesa, despesa.id) is not None


def test_excluir_despesa_apaga_parcelas(logado, casal):
    """Composição: as parcelas são excluídas junto com a despesa (CASCADE)."""
    despesa = criar_despesa(casal, categoria(casal))
    html = logado.post(f"/despesas/{despesa.id}/excluir", follow_redirects=True).get_data(as_text=True)
    assert "excluído" in html
    assert db.session.scalar(db.select(db.func.count(Parcela.id))) == 0


def test_rn11_data_de_pagamento_invalida_e08(logado, casal):
    despesa = criar_despesa(casal, categoria(casal))
    parcela = despesa.parcelas[0]
    for data in (datas.hoje() + timedelta(days=1), despesa.data_contratacao - timedelta(days=1)):
        html = logado.post(f"/parcelas/{parcela.id}/pagar", data={"data_pagamento": data.isoformat()}).get_data(as_text=True)
        assert "A data de pagamento não pode ser futura nem anterior à data de contratação." in html
    db.session.refresh(parcela)
    assert parcela.data_pagamento is None


def test_pagamento_duplicado_e_estorno_de_parcela_aberta(logado, casal):
    """Diagrama de atividades: “Já está paga?” protege contra duplo clique."""
    despesa = criar_despesa(casal, categoria(casal))
    parcela = despesa.parcelas[0]
    data = datas.hoje().isoformat()
    logado.post(f"/parcelas/{parcela.id}/pagar", data={"data_pagamento": data})
    html = logado.post(f"/parcelas/{parcela.id}/pagar", data={"data_pagamento": data},
                       follow_redirects=True).get_data(as_text=True)
    assert "Esta parcela já foi paga." in html
    outra = despesa.parcelas[1]
    html = logado.post(f"/parcelas/{outra.id}/estornar", follow_redirects=True).get_data(as_text=True)
    assert "Esta parcela não está paga." in html


def test_despesa_quitada(logado, casal):
    despesa = criar_despesa(casal, categoria(casal), valor="200", parcelas=2)
    for parcela in despesa.parcelas:
        html = logado.post(f"/parcelas/{parcela.id}/pagar", data={"data_pagamento": datas.hoje().isoformat()},
                           follow_redirects=True).get_data(as_text=True)
    assert "quitada" in html
    assert db.session.get(Despesa, despesa.id).quitada()
    assert "Quitada" in logado.get("/despesas/").get_data(as_text=True)


def test_pagar_get_mostra_formulario_e_volta_para_origem(logado, casal):
    despesa = criar_despesa(casal, categoria(casal))
    parcela = despesa.parcelas[0]
    html = logado.get(f"/parcelas/{parcela.id}/pagar?proximo=/painel").get_data(as_text=True)
    assert "Registrar pagamento" in html and datas.hoje().isoformat() in html
    resposta = logado.post(f"/parcelas/{parcela.id}/pagar?proximo=/painel",
                           data={"data_pagamento": datas.hoje().isoformat()})
    assert resposta.headers["Location"].endswith("/painel")


def test_rf10_filtros_e_csv_de_parcelas(logado, casal):
    hoje = datas.hoje()
    buffet = categoria(casal)
    atrasada = criar_despesa(casal, buffet, valor="100", parcelas=1, primeiro_vencimento=hoje - timedelta(days=5),
                             descricao="Atrasada")
    criar_despesa(casal, buffet, valor="100", parcelas=1, primeiro_vencimento=hoje + timedelta(days=10),
                  descricao="Proxima")
    criar_despesa(casal, buffet, valor="100", parcelas=1, primeiro_vencimento=hoje + timedelta(days=90),
                  descricao="Distante")
    paga = criar_despesa(casal, buffet, valor="100", parcelas=1, primeiro_vencimento=hoje, descricao="Quitada")
    despesas.pagar_parcela(paga.parcelas[0], hoje, hoje)

    def nomes(filtro):
        html = logado.get(f"/parcelas/?filtro={filtro}").get_data(as_text=True)
        return {n for n in ("Atrasada", "Proxima", "Distante", "Quitada") if f">{n}</a>" in html}

    assert nomes("todas") == {"Atrasada", "Proxima", "Distante", "Quitada"}
    assert nomes("pendentes") == {"Atrasada", "Proxima", "Distante"}
    assert nomes("atrasadas") == {"Atrasada"}
    assert nomes("pagas") == {"Quitada"}
    assert nomes("proximos-30-dias") == {"Proxima"}
    assert nomes("invalido") == nomes("todas")

    texto = logado.get("/parcelas/exportar.csv?filtro=atrasadas").get_data(as_text=True).lstrip("﻿")
    linhas = list(csv.reader(io.StringIO(texto), delimiter=";"))
    assert linhas[0] == ["Despesa", "Categoria", "Parcela", "Valor (R$)", "Vencimento", "Pagamento", "Situação"]
    assert linhas[1] == ["Atrasada", "Buffet", "1/1", "100,00", (hoje - timedelta(days=5)).strftime("%d/%m/%Y"),
                         "", "Atrasada"]
    assert len(linhas) == 2 and atrasada.parcelas


def test_previa_de_parcelas_json(logado, casal):
    vencimento = (datas.hoje() + timedelta(days=5)).isoformat()
    dados = logado.get(f"/despesas/previa?valor=1.000,00&parcelas=3&vencimento={vencimento}").get_json()
    assert dados["ok"] and [p["valor"] for p in dados["parcelas"]] == ["R$ 333,34", "R$ 333,33", "R$ 333,33"]
    erro = logado.get(f"/despesas/previa?valor=100&parcelas=30&vencimento={vencimento}").get_json()
    assert erro == {"ok": False, "erro": "O número de parcelas deve ficar entre 1 e 24."}
    assert logado.get("/despesas/previa?valor=x").get_json()["ok"] is False


def test_trocar_fornecedor_na_edicao_contrata_o_novo(logado, casal):
    buffet = categoria(casal)
    primeiro = criar_fornecedor(buffet, "A")
    segundo = criar_fornecedor(buffet, "B")
    despesa = criar_despesa(casal, buffet, fornecedor=primeiro)
    logado.post(f"/despesas/{despesa.id}/editar", data=_form(
        buffet, fornecedor_id=segundo.id, valor_total="1.000,00", num_parcelas="3",
        data_contratacao=despesa.data_contratacao.isoformat(),
        primeiro_vencimento=despesa.primeiro_vencimento.isoformat(),
    ))
    assert db.session.get(Fornecedor, segundo.id).status == "CONTRATADO"
    assert db.session.get(Despesa, despesa.id).num_parcelas == 3


def test_formularios_de_despesa_renderizam(logado, casal):
    fornecedor = criar_fornecedor(categoria(casal))
    despesa = criar_despesa(casal, categoria(casal), fornecedor=fornecedor)
    html = logado.get(f"/despesas/nova?fornecedor={fornecedor.id}").get_data(as_text=True)
    assert f'<option selected value="{fornecedor.id}">' in html
    despesas.pagar_parcela(despesa.parcelas[0], datas.hoje(), datas.hoje())
    html = logado.get(f"/despesas/{despesa.id}/editar").get_data(as_text=True)
    assert "readonly" in html and "Esta despesa tem parcelas pagas" in html
