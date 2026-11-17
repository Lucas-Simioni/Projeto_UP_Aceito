"""Categorias de gasto (UC04, RN03, RN05, RN14)."""
from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy.orm import selectinload

from app.extensions import db
from app.models import Categoria, Despesa
from app.services import orcamento
from app.services.dinheiro import ZERO
from app.services.erros import RegraNegocioErro


@dataclass(frozen=True)
class ResumoCategoria:
    categoria: Categoria
    planejado: Decimal
    contratado: Decimal
    pago: Decimal
    situacao: str
    percentual: int | None

    @property
    def nome(self) -> str:
        return self.categoria.nome


def carregar_categorias(casamento) -> list[Categoria]:
    """Categorias com despesas, parcelas e fornecedores já carregados (evita N+1 consultas)."""
    consulta = (
        db.select(Categoria)
        .filter_by(casamento_id=casamento.id)
        .options(
            selectinload(Categoria.despesas).selectinload(Despesa.parcelas),
            selectinload(Categoria.fornecedores),
        )
        .order_by(Categoria.id)
    )
    return list(db.session.scalars(consulta))


def resumir(categorias: list[Categoria]) -> list[ResumoCategoria]:
    resumos = []
    for categoria in categorias:
        contratado = categoria.total_contratado()
        resumos.append(ResumoCategoria(
            categoria=categoria,
            planejado=categoria.valor_planejado,
            contratado=contratado,
            pago=categoria.total_pago(),
            situacao=orcamento.situacao_categoria(contratado, categoria.valor_planejado),
            percentual=orcamento.percentual_utilizado(contratado, categoria.valor_planejado),
        ))
    return resumos


def _nome_em_uso(casamento_id: int, nome: str, ignorar_id: int | None) -> bool:
    consulta = db.select(Categoria.id).where(
        Categoria.casamento_id == casamento_id,
        db.func.lower(Categoria.nome) == nome.lower(),
    )
    if ignorar_id is not None:
        consulta = consulta.where(Categoria.id != ignorar_id)
    return db.session.scalar(consulta) is not None


def salvar_categoria(casamento, categoria: Categoria | None, *, nome: str, valor_planejado) -> Categoria:
    nome = nome.strip()
    if not nome:
        raise RegraNegocioErro("E01", campo="nome")
    valor = orcamento.validar_valor_nao_negativo(valor_planejado, "valor_planejado")
    if _nome_em_uso(casamento.id, nome, categoria.id if categoria else None):
        raise RegraNegocioErro("E01", campo="nome", texto="Já existe uma categoria com este nome.")
    if categoria is None:
        categoria = Categoria(casamento_id=casamento.id)
        db.session.add(categoria)
    categoria.nome = nome
    categoria.valor_planejado = valor if valor is not None else ZERO
    db.session.commit()
    return categoria


def excluir_categoria(categoria: Categoria) -> None:
    """RN14: não exclui categoria que tenha fornecedores ou despesas (E10)."""
    if categoria.em_uso():
        raise RegraNegocioErro("E10")
    db.session.delete(categoria)
    db.session.commit()
