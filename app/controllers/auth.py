"""UC01 Criar conta e UC02 Fazer login / logout (telas T01 e T02)."""
from flask import Blueprint, flash, redirect, render_template, session, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app.controllers.comum import aplicar_erro, destino_seguro
from app.forms import AcaoForm, CriarContaForm, EntrarForm
from app.services import contas
from app.services.erros import RegraNegocioErro
from app.services.mensagens import mensagem

bp = Blueprint("auth", __name__)


@bp.route("/entrar", methods=["GET", "POST"])
def entrar():
    if current_user.is_authenticated:
        return redirect(url_for("painel.index"))
    form = EntrarForm()
    if form.validate_on_submit():
        usuario = contas.autenticar(form.email.data, form.senha.data)
        if usuario is None:
            flash(mensagem("E03"), "erro")
        else:
            session.clear()  # evita fixação de sessão
            login_user(usuario)
            return redirect(destino_seguro(url_for("painel.index")))
    return render_template("auth/entrar.html", form=form)


@bp.route("/criar-conta", methods=["GET", "POST"])
def criar_conta():
    if current_user.is_authenticated:
        return redirect(url_for("painel.index"))
    form = CriarContaForm()
    if form.validate_on_submit():
        try:
            usuario = contas.criar_conta(form.nome.data, form.email.data, form.senha.data)
        except RegraNegocioErro as erro:
            aplicar_erro(form, erro)
        else:
            session.clear()
            login_user(usuario)
            flash("Conta criada! Agora conte um pouco sobre o casamento.", "sucesso")
            return redirect(url_for("casamento.editar"))
    return render_template("auth/criar_conta.html", form=form)


@bp.route("/sair", methods=["POST"])
@login_required
def sair():
    if AcaoForm().validate_on_submit():
        logout_user()
        flash("Você saiu da sua conta.", "sucesso")
    return redirect(url_for("auth.entrar"))
