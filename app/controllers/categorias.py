"""UC04 Gerenciar categorias (tela T05 – Orçamento)."""
from flask import Blueprint, flash, g, redirect, render_template, url_for

from app.controllers.comum import aplicar_erro, casamento_obrigatorio, obter_categoria
from app.forms import AcaoForm, CategoriaForm
from app.services import categorias as servico
from app.services import orcamento
from app.services.dinheiro import somar
from app.services.erros import RegraNegocioErro
from app.services.mensagens import mensagem

bp = Blueprint("categorias", __name__, url_prefix="/orcamento")


@bp.route("/")
@casamento_obrigatorio
def lista():
    casamento = g.casamento
    resumos = servico.resumir(servico.carregar_categorias(casamento))
    totais = {
        "planejado": somar(r.planejado for r in resumos),
        "contratado": somar(r.contratado for r in resumos),
        "pago": somar(r.pago for r in resumos),
    }
    totais["nao_alocado"] = casamento.orcamento_total - totais["planejado"]
    return render_template(
        "categorias/lista.html",
        casamento=casamento,
        resumos=resumos,
        totais=totais,
        planejado_excedente=orcamento.alerta_planejado(totais["planejado"], casamento.orcamento_total),
        orcamento_excedente=orcamento.alerta_orcamento(totais["contratado"], casamento.orcamento_total),
    )


@bp.route("/nova", methods=["GET", "POST"])
@casamento_obrigatorio
def nova():
    return _formulario(None)


@bp.route("/<int:categoria_id>/editar", methods=["GET", "POST"])
@casamento_obrigatorio
def editar(categoria_id):
    return _formulario(obter_categoria(categoria_id))


def _formulario(categoria):
    form = CategoriaForm(obj=categoria)
    if form.validate_on_submit():
        try:
            servico.salvar_categoria(g.casamento, categoria, nome=form.nome.data,
                                     valor_planejado=form.valor_planejado.data)
        except RegraNegocioErro as erro:
            aplicar_erro(form, erro)
        else:
            flash(mensagem("S01"), "sucesso")
            return redirect(url_for("categorias.lista"))
    return render_template("categorias/form.html", form=form, categoria=categoria)


@bp.route("/<int:categoria_id>/excluir", methods=["POST"])
@casamento_obrigatorio
def excluir(categoria_id):
    categoria = obter_categoria(categoria_id)
    if AcaoForm().validate_on_submit():
        nome = categoria.nome
        try:
            servico.excluir_categoria(categoria)
        except RegraNegocioErro as erro:
            flash(erro.mensagem, "erro")
        else:
            flash(mensagem("S04", item=f"Categoria {nome}"), "sucesso")
    return redirect(url_for("categorias.lista"))
