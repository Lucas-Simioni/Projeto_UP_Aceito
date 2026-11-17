"""Despesas, parcelas e pagamentos (UC07, UC08, UC09; RN03, RN07–RN14).

Cada operação valida tudo antes de alterar qualquer objeto e grava numa única transação.
"""
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from sqlalchemy.orm import selectinload

from app.extensions import db
from app.models import Categoria, Despesa, Fornecedor, Parcela
from app.models.dominios import StatusFornecedor
from app.services import orcamento, parcelamento
from app.services.dinheiro import formatar_moeda, quantizar
from app.services.erros import RegraNegocioErro
from app.services.mensagens import mensagem


@dataclass(frozen=True)
class DadosDespesa:
    categoria_id: int
    fornecedor_id: int | None
    descricao: str
    valor_total: Decimal
    data_contratacao: date
    num_parcelas: int
    primeiro_vencimento: date


# --------------------------------------------------------------------------- consultas


def listar_despesas(casamento, categoria_id: int | None = None) -> list[Despesa]:
    consulta = (
        db.select(Despesa)
        .join(Categoria)
        .where(Categoria.casamento_id == casamento.id)
        .options(selectinload(Despesa.parcelas), selectinload(Despesa.fornecedor),
                 selectinload(Despesa.categoria))
    )
    if categoria_id:
        consulta = consulta.where(Despesa.categoria_id == categoria_id)
    return list(db.session.scalars(consulta.order_by(Categoria.id, Despesa.data_contratacao, Despesa.id)))


def listar_parcelas(casamento, filtro: str = parcelamento.FiltroParcela.TODAS,
                    hoje: date | None = None) -> list[Parcela]:
    """RF10: parcelas do casamento em ordem de vencimento, com o filtro aplicado."""
    consulta = (
        db.select(Parcela)
        .join(Despesa)
        .join(Categoria)
        .where(Categoria.casamento_id == casamento.id)
        .options(selectinload(Parcela.despesa).selectinload(Despesa.categoria),
                 selectinload(Parcela.despesa).selectinload(Despesa.parcelas))
        .order_by(Parcela.data_vencimento, Parcela.despesa_id, Parcela.numero)
    )
    parcelas = list(db.session.scalars(consulta))
    if hoje is None or filtro == parcelamento.FiltroParcela.TODAS:
        return parcelas
    return [p for p in parcelas
            if parcelamento.parcela_atende_filtro(p.data_vencimento, p.data_pagamento, filtro, hoje)]


# --------------------------------------------------------------------------- validação


def _validar(casamento, dados: DadosDespesa, despesa_atual: Despesa | None) -> tuple[Categoria, Fornecedor | None]:
    """UC07 passo 4: RN03, RN08, RN12, RN13. Não altera nada."""
    categoria = db.session.get(Categoria, dados.categoria_id) if dados.categoria_id else None
    if categoria is None or categoria.casamento_id != casamento.id:
        raise RegraNegocioErro("E01", campo="categoria_id", texto="Escolha uma categoria da lista.")
    if not (dados.descricao or "").strip():
        raise RegraNegocioErro("E01", campo="descricao")
    orcamento.validar_valor_positivo(dados.valor_total, "valor_total")
    if dados.data_contratacao is None:
        raise RegraNegocioErro("E01", campo="data_contratacao")
    if dados.primeiro_vencimento is None:
        raise RegraNegocioErro("E01", campo="primeiro_vencimento")
    parcelamento.validar_numero_parcelas(dados.num_parcelas)
    parcelamento.dividir_valor(dados.valor_total, dados.num_parcelas)  # garante parcelas > 0

    fornecedor = None
    if dados.fornecedor_id:
        fornecedor = db.session.get(Fornecedor, dados.fornecedor_id)
        if fornecedor is None or fornecedor.categoria.casamento_id != casamento.id:
            raise RegraNegocioErro("E01", campo="fornecedor_id", texto="Escolha um fornecedor da lista.")
        mesmo_fornecedor = despesa_atual is not None and despesa_atual.fornecedor_id == fornecedor.id
        status = fornecedor.status
        if mesmo_fornecedor and status == StatusFornecedor.DESCARTADO:
            # RN12 impede *novas* despesas; manter o vínculo já existente é permitido.
            status = StatusFornecedor.CONTRATADO
        orcamento.validar_fornecedor_para_despesa(status, fornecedor.categoria_id,
                                                  fornecedor.categoria.nome, categoria.id)
    return categoria, fornecedor


def _contratar(fornecedor: Fornecedor | None) -> None:
    """RN12: ao receber despesa, fornecedor em Orçamento passa a Contratado."""
    if fornecedor is not None and fornecedor.status == StatusFornecedor.ORCAMENTO:
        fornecedor.status = StatusFornecedor.CONTRATADO


def alertas_da_despesa(despesa: Despesa) -> list[str]:
    """UC07 passo 7 (fluxos 7a e 7b): avisos A01, A02 e A03 depois de gravar."""
    categoria = despesa.categoria
    casamento = categoria.casamento
    avisos = []
    contratado_categoria = categoria.total_contratado()
    if orcamento.situacao_categoria(contratado_categoria, categoria.valor_planejado) == \
            orcamento.SituacaoCategoria.ACIMA:
        valor = orcamento.excedente(contratado_categoria, categoria.valor_planejado)
        avisos.append(mensagem("A01", categoria=categoria.nome, valor=formatar_moeda(valor)))
    estouro = orcamento.alerta_orcamento(casamento.total_contratado(), casamento.orcamento_total)
    if estouro is not None:
        avisos.append(mensagem("A02", valor=formatar_moeda(estouro)))
    apos = parcelamento.parcelas_apos_casamento(despesa.parcelas, casamento.data_casamento)
    if apos:
        avisos.append(mensagem("A03", n=len(apos)))
    return avisos


# --------------------------------------------------------------------------- operações


def registrar_despesa(casamento, dados: DadosDespesa) -> tuple[Despesa, list[str]]:
    """UC07: valida, gera as parcelas (UC08) e grava tudo numa transação."""
    categoria, fornecedor = _validar(casamento, dados, None)
    despesa = Despesa(
        categoria=categoria,
        fornecedor=fornecedor,
        descricao=dados.descricao.strip(),
        valor_total=quantizar(dados.valor_total),
        data_contratacao=dados.data_contratacao,
    )
    despesa.gerar_parcelas(dados.num_parcelas, dados.primeiro_vencimento)
    _contratar(fornecedor)
    db.session.add(despesa)
    db.session.commit()
    return despesa, alertas_da_despesa(despesa)


def atualizar_despesa(casamento, despesa: Despesa, dados: DadosDespesa) -> tuple[Despesa, list[str]]:
    """RF08: altera a despesa. Mudou valor, nº de parcelas ou 1º vencimento -> regera as parcelas.

    Com parcela paga (RN14) só descrição, categoria e fornecedor podem mudar; mexer em valor,
    parcelas, vencimento ou data de contratação exige estornar os pagamentos antes (E11).
    """
    categoria, fornecedor = _validar(casamento, dados, despesa)
    valor_total = quantizar(dados.valor_total)
    mudou_parcelamento = (
        valor_total != despesa.valor_total
        or dados.num_parcelas != despesa.num_parcelas
        or dados.primeiro_vencimento != despesa.primeiro_vencimento
    )
    if despesa.tem_parcela_paga() and (mudou_parcelamento or dados.data_contratacao != despesa.data_contratacao):
        raise RegraNegocioErro("E11", campo="valor_total")

    fornecedor_novo = fornecedor is not None and fornecedor.id != despesa.fornecedor_id
    despesa.categoria = categoria
    despesa.fornecedor = fornecedor
    despesa.descricao = dados.descricao.strip()
    despesa.valor_total = valor_total
    despesa.data_contratacao = dados.data_contratacao
    if mudou_parcelamento:
        despesa.parcelas.clear()
        db.session.flush()  # apaga as antigas antes de inserir as novas (número é único por despesa)
        despesa.gerar_parcelas(dados.num_parcelas, dados.primeiro_vencimento)
    if fornecedor_novo:
        _contratar(fornecedor)
    db.session.commit()
    return despesa, alertas_da_despesa(despesa)


def excluir_despesa(despesa: Despesa) -> None:
    """RN14: despesa com parcela paga não pode ser excluída (E11). As parcelas vão junto."""
    if despesa.tem_parcela_paga():
        raise RegraNegocioErro("E11")
    db.session.delete(despesa)
    db.session.commit()


def pagar_parcela(parcela: Parcela, data_pagamento: date | None, hoje: date) -> Parcela:
    """UC09: confere de novo se já está paga (duplo clique / duas abas) e valida a data (RN11)."""
    parcela.pagar(data_pagamento, hoje)
    db.session.commit()
    return parcela


def estornar_parcela(parcela: Parcela) -> Parcela:
    """UC09 A1."""
    parcela.estornar()
    db.session.commit()
    return parcela


def previa_parcelas(valor_total, num_parcelas: int, primeiro_vencimento: date) -> list[parcelamento.ParcelaCalculada]:
    """T08: pré-visualização antes de salvar — usa exatamente a mesma regra do registro."""
    return parcelamento.gerar_parcelas(valor_total, num_parcelas, primeiro_vencimento)
