"""UC11 Gerenciar convidados e UC12 Exportar CSV de convidados (telas T11 e T12)."""
from flask import Blueprint, Response, flash, g, redirect, render_template, request, url_for

from app.controllers.comum import aplicar_erro, casamento_obrigatorio, obter_convidado
from app.forms import AcaoForm, ConvidadoForm
from app.models.dominios import Grupo, StatusRSVP
from app.services import convidados as servico
from app.services import exportacao
from app.services.erros import RegraNegocioErro
from app.services.mensagens import mensagem

bp = Blueprint("convidados", __name__, url_prefix="/convidados")


def _filtros() -> dict:
    grupo = request.args.get("grupo")
    status = request.args.get("status")
    return {
        "grupo": grupo if grupo in Grupo.VALORES else None,
        "status": status if status in StatusRSVP.VALORES else None,
    }


@bp.route("/")
@casamento_obrigatorio
def lista():
    filtros = _filtros()
    todos = servico.listar_convidados(g.casamento)
    convidados = servico.listar_convidados(g.casamento, **filtros) if any(filtros.values()) else todos
    resumo = servico.resumo_convidados(todos)
    custo = servico.custo_por_convidado(g.casamento.total_contratado(), resumo.pessoas_confirmadas)
    return render_template("convidados/lista.html", convidados=convidados, resumo=resumo, custo=custo,
                           filtros=filtros, grupos=Grupo.escolhas(), status_opcoes=StatusRSVP.escolhas(),
                           estimados=g.casamento.convidados_estimados)


@bp.route("/novo", methods=["GET", "POST"])
@casamento_obrigatorio
def novo():
    return _formulario(None)


@bp.route("/<int:convidado_id>/editar", methods=["GET", "POST"])
@casamento_obrigatorio
def editar(convidado_id):
    return _formulario(obter_convidado(convidado_id))


def _formulario(convidado):
    form = ConvidadoForm(obj=convidado)
    if form.validate_on_submit():
        try:
            servico.salvar_convidado(
                g.casamento, convidado, nome=form.nome.data, grupo=form.grupo.data,
                telefone=form.telefone.data, email=form.email.data, acompanhantes=form.acompanhantes.data,
            )
        except RegraNegocioErro as erro:
            aplicar_erro(form, erro)
        else:
            flash(mensagem("S01"), "sucesso")
            if convidado is None and request.form.get("continuar"):
                return redirect(url_for("convidados.novo"))
            return redirect(url_for("convidados.lista"))
    return render_template("convidados/form.html", form=form, convidado=convidado)


@bp.route("/<int:convidado_id>/rsvp", methods=["POST"])
@casamento_obrigatorio
def rsvp(convidado_id):
    """Troca de status com um clique, direto na lista (UC11)."""
    convidado = obter_convidado(convidado_id)
    if AcaoForm().validate_on_submit():
        try:
            servico.alterar_status(convidado, request.form.get("status", ""))
        except RegraNegocioErro as erro:
            flash(erro.mensagem, "erro")
    destino = url_for("convidados.lista", **{k: v for k, v in _filtros_do_formulario().items() if v})
    return redirect(f"{destino}#convidado-{convidado_id}")


def _filtros_do_formulario() -> dict:
    grupo, status = request.form.get("filtro_grupo"), request.form.get("filtro_status")
    return {
        "grupo": grupo if grupo in Grupo.VALORES else None,
        "status": status if status in StatusRSVP.VALORES else None,
    }


@bp.route("/<int:convidado_id>/excluir", methods=["POST"])
@casamento_obrigatorio
def excluir(convidado_id):
    convidado = obter_convidado(convidado_id)
    if AcaoForm().validate_on_submit():
        nome = convidado.nome
        servico.excluir_convidado(convidado)
        flash(mensagem("S04", item=f"Convidado {nome}"), "sucesso")
    return redirect(url_for("convidados.lista"))


@bp.route("/exportar.csv")
@casamento_obrigatorio
def exportar():
    convidados = servico.listar_convidados(g.casamento, **_filtros())
    conteudo = "﻿" + exportacao.csv_convidados(convidados)
    return Response(conteudo, mimetype="text/csv; charset=utf-8",
                    headers={"Content-Disposition": "attachment; filename=convidados.csv"})
