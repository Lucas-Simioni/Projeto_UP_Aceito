"""UC09 Registrar pagamento de parcela e UC12 Exportar CSV de parcelas (tela T10)."""
from flask import Blueprint, Response, flash, g, redirect, render_template, request, url_for

from app.controllers.comum import casamento_obrigatorio, destino_seguro, obter_parcela
from app.forms import AcaoForm, PagamentoForm
from app.services import datas, exportacao
from app.services import despesas as servico
from app.services.erros import RegraNegocioErro
from app.services.mensagens import mensagem
from app.services.parcelamento import FiltroParcela, parcela_atende_filtro

bp = Blueprint("parcelas", __name__, url_prefix="/parcelas")


def _filtro_atual() -> str:
    filtro = request.args.get("filtro", FiltroParcela.TODAS)
    return filtro if filtro in FiltroParcela.ROTULOS else FiltroParcela.TODAS


@bp.route("/")
@casamento_obrigatorio
def lista():
    hoje = datas.hoje()
    filtro = _filtro_atual()
    todas = servico.listar_parcelas(g.casamento)
    contagens = {
        chave: sum(1 for p in todas if parcela_atende_filtro(p.data_vencimento, p.data_pagamento, chave, hoje))
        for chave in FiltroParcela.ROTULOS
    }
    parcelas = [p for p in todas if parcela_atende_filtro(p.data_vencimento, p.data_pagamento, filtro, hoje)]
    return render_template("parcelas/lista.html", parcelas=parcelas, filtro=filtro, contagens=contagens,
                           filtros=FiltroParcela.ROTULOS, hoje=hoje, casamento=g.casamento,
                           form_pagamento=PagamentoForm(data_pagamento=hoje))


@bp.route("/<int:parcela_id>/pagar", methods=["GET", "POST"])
@casamento_obrigatorio
def pagar(parcela_id):
    """UC09. O GET mostra a tela de pagamento; o POST grava (também usado pela janela do painel)."""
    parcela = obter_parcela(parcela_id)
    hoje = datas.hoje()
    voltar = destino_seguro(url_for("parcelas.lista"))
    if parcela.paga:
        # Diagrama de atividades: "Já está paga?" -> avisar e encerrar.
        flash("Esta parcela já foi paga.", "aviso")
        return redirect(voltar)

    form = PagamentoForm(data_pagamento=hoje)
    if form.validate_on_submit():
        try:
            servico.pagar_parcela(parcela, form.data_pagamento.data, hoje)
        except RegraNegocioErro as erro:
            form.data_pagamento.errors = [*form.data_pagamento.errors, erro.mensagem]
        else:
            flash(mensagem("S02"), "sucesso")
            if parcela.despesa.quitada():
                flash(f"Despesa “{parcela.despesa.descricao}” quitada!", "sucesso")
            return redirect(voltar)
    return render_template("parcelas/pagar.html", parcela=parcela, form=form, hoje=hoje, voltar=voltar)


@bp.route("/<int:parcela_id>/estornar", methods=["POST"])
@casamento_obrigatorio
def estornar(parcela_id):
    parcela = obter_parcela(parcela_id)
    if AcaoForm().validate_on_submit():
        try:
            servico.estornar_parcela(parcela)
        except RegraNegocioErro as erro:
            flash(erro.mensagem, "aviso")
        else:
            flash(mensagem("S03"), "sucesso")
    return redirect(destino_seguro(url_for("parcelas.lista")))


@bp.route("/exportar.csv")
@casamento_obrigatorio
def exportar():
    """RF14: exporta as parcelas do filtro atual."""
    hoje = datas.hoje()
    parcelas = servico.listar_parcelas(g.casamento, _filtro_atual(), hoje)
    conteudo = "﻿" + exportacao.csv_parcelas(parcelas, hoje)
    return Response(conteudo, mimetype="text/csv; charset=utf-8",
                    headers={"Content-Disposition": "attachment; filename=parcelas.csv"})
