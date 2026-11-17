"""Fornecedores e comparação de orçamentos (UC05, UC06, RN03, RN12, RN13)."""
from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy.orm import selectinload

from app.extensions import db
from app.models import Categoria, Fornecedor
from app.models.dominios import StatusFornecedor
from app.services import orcamento
from app.services.erros import RegraNegocioErro


def listar_fornecedores(casamento, categoria_id: int | None = None, status: str | None = None) -> list[Fornecedor]:
    consulta = (
        db.select(Fornecedor)
        .join(Categoria)
        .where(Categoria.casamento_id == casamento.id)
        .options(selectinload(Fornecedor.categoria), selectinload(Fornecedor.despesas))
    )
    if categoria_id:
        consulta = consulta.where(Fornecedor.categoria_id == categoria_id)
    if status in StatusFornecedor.VALORES:
        consulta = consulta.where(Fornecedor.status == status)
    return list(db.session.scalars(consulta.order_by(Categoria.id, db.func.lower(Fornecedor.nome))))


def _categoria_do_casamento(casamento, categoria_id) -> Categoria:
    categoria = db.session.get(Categoria, categoria_id) if categoria_id else None
    if categoria is None or categoria.casamento_id != casamento.id:
        raise RegraNegocioErro("E01", campo="categoria_id", texto="Escolha uma categoria da lista.")
    return categoria


def salvar_fornecedor(casamento, fornecedor: Fornecedor | None, *, categoria_id: int, nome: str,
                      telefone: str | None, email: str | None, valor_orcado, status: str,
                      observacoes: str | None) -> Fornecedor:
    categoria = _categoria_do_casamento(casamento, categoria_id)
    valor = orcamento.validar_valor_nao_negativo(valor_orcado, "valor_orcado")
    if status not in StatusFornecedor.VALORES:
        raise RegraNegocioErro("E01", campo="status", texto="Escolha um status da lista.")
    if fornecedor is not None and fornecedor.despesas and fornecedor.categoria_id != categoria.id:
        # Mudar a categoria deixaria as despesas dele em outra categoria, violando a RN13.
        raise RegraNegocioErro("E07", campo="categoria_id",
                               texto="Este fornecedor já tem despesas registradas; a categoria não pode mudar.")

    if fornecedor is None:
        fornecedor = Fornecedor()
        db.session.add(fornecedor)
    fornecedor.categoria_id = categoria.id
    fornecedor.nome = nome.strip()
    fornecedor.telefone = telefone or None
    fornecedor.email = email or None
    fornecedor.valor_orcado = valor
    fornecedor.status = status
    fornecedor.observacoes = (observacoes or "").strip() or None
    db.session.commit()
    return fornecedor


def excluir_fornecedor(fornecedor: Fornecedor) -> None:
    """As despesas do fornecedor são mantidas, apenas sem vínculo (ON DELETE SET NULL)."""
    for despesa in list(fornecedor.despesas):
        despesa.fornecedor_id = None
    db.session.delete(fornecedor)
    db.session.commit()


@dataclass(frozen=True)
class ItemComparacao:
    fornecedor: Fornecedor
    menor: bool
    diferenca: Decimal | None   # quanto custa a mais que o menor orçamento
    percentual: int | None      # diferença em % sobre o menor
    cabe_no_planejado: bool | None


def comparar_orcamentos(categoria: Categoria) -> list[ItemComparacao]:
    """RF06: fornecedores da categoria em ordem de valor, com o menor orçamento em destaque.

    Fornecedores descartados aparecem no fim e não disputam o “menor valor”. Fornecedores sem
    valor orçado aparecem depois dos que têm valor.
    """
    ativos = [f for f in categoria.fornecedores if f.status != StatusFornecedor.DESCARTADO]
    descartados = [f for f in categoria.fornecedores if f.status == StatusFornecedor.DESCARTADO]

    def chave(f: Fornecedor):
        return (f.valor_orcado is None, f.valor_orcado or 0, f.nome.lower())

    ativos.sort(key=chave)
    descartados.sort(key=chave)
    valores = [f.valor_orcado for f in ativos if f.valor_orcado is not None]
    menor_valor = min(valores) if valores else None
    planejado = categoria.valor_planejado

    itens = []
    for fornecedor in ativos + descartados:
        valor = fornecedor.valor_orcado
        disputa = fornecedor.status != StatusFornecedor.DESCARTADO and valor is not None
        menor = disputa and valor == menor_valor
        diferenca = percentual = None
        if disputa and menor_valor is not None and not menor:
            diferenca = valor - menor_valor
            percentual = int((diferenca / menor_valor * 100).to_integral_value()) if menor_valor else None
        cabe = None if valor is None or not planejado else valor <= planejado
        itens.append(ItemComparacao(fornecedor, menor, diferenca, percentual, cabe))
    return itens
