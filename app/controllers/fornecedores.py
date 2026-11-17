"""UC05 Gerenciar fornecedores e UC06 Comparar orçamentos (telas T06 e T07)."""
from flask import Blueprint, flash, g, redirect, render_template, request, url_for

from app.controllers.comum import (aplicar_erro, casamento_obrigatorio, obter_categoria,
                                   obter_fornecedor)
from app.forms import AcaoForm, FornecedorForm
from app.models.dominios import StatusFornecedor
from app.services import fornecedores as servico
from app.services.erros import RegraNegocioErro
from app.services.mensagens import mensagem

bp = Blueprint("fornecedores", __name__, url_prefix="/fornecedores")


@bp.route("/")
@casamento_obrigatorio
def lista():
    categoria_id = request.args.get("categoria", type=int)
    status = request.args.get("status")
    fornecedores = servico.listar_fornecedores(g.casamento, categoria_id, status)
    return render_template(
        "fornecedores/lista.html",
        fornecedores=fornecedores,
        categorias=g.casamento.categorias,
        status_opcoes=StatusFornecedor.escolhas(),
        filtro_categoria=categoria_id,
        filtro_status=status if status in StatusFornecedor.VALORES else None,
    )


@bp.route("/novo", methods=["GET", "POST"])
@casamento_obrigatorio
def novo():
    return _formulario(None)


@bp.route("/<int:fornecedor_id>/editar", methods=["GET", "POST"])
@casamento_obrigatorio
def editar(fornecedor_id):
    return _formulario(obter_fornecedor(fornecedor_id))


def _formulario(fornecedor):
    form = FornecedorForm(obj=fornecedor)
    form.categoria_id.choices = [("", "Escolha a categoria")] + [(c.id, c.nome) for c in g.casamento.categorias]
    if fornecedor is None and request.method == "GET":
        form.categoria_id.data = request.args.get("categoria", type=int)
    if form.validate_on_submit():
        try:
            salvo = servico.salvar_fornecedor(
                g.casamento, fornecedor,
                categoria_id=form.categoria_id.data, nome=form.nome.data, telefone=form.telefone.data,
                email=form.email.data, valor_orcado=form.valor_orcado.data, status=form.status.data,
                observacoes=form.observacoes.data,
            )
        except RegraNegocioErro as erro:
            aplicar_erro(form, erro)
        else:
            flash(mensagem("S01"), "sucesso")
            return redirect(url_for("fornecedores.lista", categoria=salvo.categoria_id))
    return render_template("fornecedores/form.html", form=form, fornecedor=fornecedor)


@bp.route("/<int:fornecedor_id>/excluir", methods=["POST"])
@casamento_obrigatorio
def excluir(fornecedor_id):
    fornecedor = obter_fornecedor(fornecedor_id)
    if AcaoForm().validate_on_submit():
        nome = fornecedor.nome
        servico.excluir_fornecedor(fornecedor)
        flash(mensagem("S04", item=f"Fornecedor {nome}"), "sucesso")
    return redirect(url_for("fornecedores.lista"))


@bp.route("/comparar")
@casamento_obrigatorio
def comparar():
    categorias = g.casamento.categorias
    categoria_id = request.args.get("categoria", type=int)
    if categoria_id is None:
        # Abre na primeira categoria que tenha fornecedores, para a tela nunca começar vazia à toa.
        com_fornecedores = [c for c in categorias if c.fornecedores]
        categoria_id = (com_fornecedores or categorias)[0].id if categorias else None
    categoria = obter_categoria(categoria_id) if categoria_id else None
    itens = servico.comparar_orcamentos(categoria) if categoria else []
    return render_template("fornecedores/comparar.html", categorias=categorias, categoria=categoria,
                           itens=itens)
