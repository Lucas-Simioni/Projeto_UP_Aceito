"""UC07 Registrar despesa e UC08 Gerar parcelas (telas T08 e T09)."""
from datetime import date
from itertools import groupby

from flask import Blueprint, flash, g, jsonify, redirect, render_template, request, url_for

from app.controllers.comum import (aplicar_erro, casamento_obrigatorio, flash_avisos,
                                   obter_despesa)
from app.forms import AcaoForm, DespesaForm, PagamentoForm
from app.models.dominios import StatusFornecedor
from app.services import datas
from app.services import despesas as servico
from app.services.dinheiro import formatar_moeda, interpretar_moeda, somar
from app.services.erros import RegraNegocioErro
from app.services.mensagens import mensagem, mensagem_exclusao

bp = Blueprint("despesas", __name__, url_prefix="/despesas")


@bp.route("/")
@casamento_obrigatorio
def lista():
    categoria_id = request.args.get("categoria", type=int)
    despesas = servico.listar_despesas(g.casamento, categoria_id)
    grupos = [
        (categoria, itens, somar(d.valor_total for d in itens))
        for categoria, itens in ((c, list(i)) for c, i in groupby(despesas, key=lambda d: d.categoria))
    ]
    return render_template("despesas/lista.html", grupos=grupos, categorias=g.casamento.categorias,
                           filtro_categoria=categoria_id, hoje=datas.hoje(),
                           total=somar(d.valor_total for d in despesas))


@bp.route("/<int:despesa_id>")
@casamento_obrigatorio
def detalhe(despesa_id):
    despesa = obter_despesa(despesa_id)
    hoje = datas.hoje()
    return render_template("despesas/detalhe.html", despesa=despesa, hoje=hoje, casamento=g.casamento,
                           form_pagamento=PagamentoForm(data_pagamento=hoje))


@bp.route("/nova", methods=["GET", "POST"])
@casamento_obrigatorio
def nova():
    return _formulario(None)


@bp.route("/<int:despesa_id>/editar", methods=["GET", "POST"])
@casamento_obrigatorio
def editar(despesa_id):
    return _formulario(obter_despesa(despesa_id))


def _preparar_escolhas(form, despesa):
    casamento = g.casamento
    form.categoria_id.choices = [("", "Escolha a categoria")] + [(c.id, c.nome) for c in casamento.categorias]
    # UC07 passo 2: fornecedores descartados não aparecem (exceto o já vinculado a esta despesa).
    fornecedores = [
        f for c in casamento.categorias for f in c.fornecedores
        if f.status != StatusFornecedor.DESCARTADO or (despesa and despesa.fornecedor_id == f.id)
    ]
    form.fornecedor_id.choices = [("", "Sem fornecedor (compra avulsa)")] + [
        (f.id, f.nome) for f in sorted(fornecedores, key=lambda f: f.nome.lower())
    ]
    # Categoria de cada fornecedor, para o JavaScript filtrar a lista conforme a categoria (RN13).
    return {f.id: f.categoria_id for f in fornecedores}


def _formulario(despesa):
    form = DespesaForm(obj=despesa)
    categoria_por_fornecedor = _preparar_escolhas(form, despesa)
    if request.method == "GET":
        if despesa is not None:
            form.num_parcelas.data = despesa.num_parcelas
            form.primeiro_vencimento.data = despesa.primeiro_vencimento
        else:
            form.data_contratacao.data = datas.hoje()
            form.categoria_id.data = request.args.get("categoria", type=int)
            fornecedor_id = request.args.get("fornecedor", type=int)
            if fornecedor_id in categoria_por_fornecedor:
                form.fornecedor_id.data = fornecedor_id
                form.categoria_id.data = categoria_por_fornecedor[fornecedor_id]

    if form.validate_on_submit():
        dados = servico.DadosDespesa(
            categoria_id=form.categoria_id.data,
            fornecedor_id=form.fornecedor_id.data,
            descricao=form.descricao.data,
            valor_total=form.valor_total.data,
            data_contratacao=form.data_contratacao.data,
            num_parcelas=form.num_parcelas.data,
            primeiro_vencimento=form.primeiro_vencimento.data,
        )
        try:
            if despesa is None:
                salva, avisos = servico.registrar_despesa(g.casamento, dados)
            else:
                salva, avisos = servico.atualizar_despesa(g.casamento, despesa, dados)
        except RegraNegocioErro as erro:
            aplicar_erro(form, erro)
        else:
            flash(mensagem("S01"), "sucesso")
            flash_avisos(avisos)
            return redirect(url_for("despesas.detalhe", despesa_id=salva.id))

    return render_template(
        "despesas/form.html", form=form, despesa=despesa,
        bloqueada=despesa is not None and despesa.tem_parcela_paga(),
        categoria_por_fornecedor=categoria_por_fornecedor,
        data_casamento=g.casamento.data_casamento.isoformat(),
    )


@bp.route("/<int:despesa_id>/excluir", methods=["POST"])
@casamento_obrigatorio
def excluir(despesa_id):
    despesa = obter_despesa(despesa_id)
    if AcaoForm().validate_on_submit():
        descricao = despesa.descricao
        try:
            servico.excluir_despesa(despesa)
        except RegraNegocioErro as erro:
            flash(erro.mensagem, "erro")
            return redirect(url_for("despesas.detalhe", despesa_id=despesa_id))
        flash(mensagem_exclusao(f"Despesa “{descricao}”", feminino=True), "sucesso")
    return redirect(url_for("despesas.lista"))


@bp.route("/previa")
@casamento_obrigatorio
def previa():
    """T08: pré-visualização das parcelas (JSON) com a mesma regra usada ao salvar."""
    try:
        valor = interpretar_moeda(request.args.get("valor", ""))
        quantidade = int(request.args.get("parcelas", ""))
        primeiro = date.fromisoformat(request.args.get("vencimento", ""))
        parcelas = servico.previa_parcelas(valor, quantidade, primeiro)
    except RegraNegocioErro as erro:
        return jsonify(ok=False, erro=erro.mensagem)
    except ValueError:
        return jsonify(ok=False, erro=None)
    data_casamento = g.casamento.data_casamento
    return jsonify(ok=True, total=formatar_moeda(valor), parcelas=[
        {
            "numero": p.numero,
            "valor": formatar_moeda(p.valor),
            "vencimento": p.data_vencimento.strftime("%d/%m/%Y"),
            "apos_casamento": p.data_vencimento > data_casamento,
        }
        for p in parcelas
    ])
