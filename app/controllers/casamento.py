"""UC03 Configurar casamento (tela T03)."""
from flask import Blueprint, flash, redirect, render_template, url_for
from flask_login import current_user, login_required

from app.controllers.comum import aplicar_erro
from app.forms import CasamentoForm
from app.services import casamentos
from app.services.erros import RegraNegocioErro
from app.services.mensagens import mensagem

bp = Blueprint("casamento", __name__)


@bp.route("/meu-casamento", methods=["GET", "POST"])
@login_required
def editar():
    casamento = current_user.casamento
    primeiro_acesso = casamento is None
    form = CasamentoForm(obj=casamento)
    if form.validate_on_submit():
        try:
            _, criado = casamentos.salvar_casamento(
                current_user,
                nome_casal=form.nome_casal.data,
                data_casamento=form.data_casamento.data,
                local=form.local.data,
                orcamento_total=form.orcamento_total.data,
                convidados_estimados=form.convidados_estimados.data,
            )
        except RegraNegocioErro as erro:
            aplicar_erro(form, erro)
        else:
            if criado:
                flash("Tudo pronto! Criamos oito categorias de gasto para você começar.", "sucesso")
            else:
                flash(mensagem("S01"), "sucesso")
            return redirect(url_for("painel.index"))
    return render_template("casamento/form.html", form=form, primeiro_acesso=primeiro_acesso)
