"""UC10 Consultar painel (tela T04)."""
from flask import Blueprint, g, redirect, render_template, url_for
from flask_login import current_user

from app.controllers.comum import casamento_obrigatorio
from app.forms import PagamentoForm
from app.services import datas
from app.services.painel import montar_painel

bp = Blueprint("painel", __name__)


@bp.route("/")
def inicio():
    if current_user.is_authenticated:
        return redirect(url_for("painel.index"))
    return redirect(url_for("auth.entrar"))


@bp.route("/painel")
@casamento_obrigatorio
def index():
    hoje = datas.hoje()
    painel = montar_painel(g.casamento, hoje)
    return render_template("painel/index.html", casamento=g.casamento, painel=painel, hoje=hoje,
                           form_pagamento=PagamentoForm(data_pagamento=hoje))
