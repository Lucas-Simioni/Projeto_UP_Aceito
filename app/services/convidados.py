"""Regras da lista de convidados (RN15, RN16) e operações de cadastro / RSVP."""
from dataclasses import dataclass
from decimal import Decimal

from app.extensions import db
from app.models import Convidado
from app.models.dominios import Grupo, StatusRSVP
from app.services.dinheiro import quantizar
from app.services.erros import RegraNegocioErro

MIN_ACOMPANHANTES = 0
MAX_ACOMPANHANTES = 10


# --------------------------------------------------------------------------- regras puras


def validar_acompanhantes(quantidade) -> int:
    """RN16: de 0 a 10 acompanhantes."""
    if quantidade is None:
        raise RegraNegocioErro("E01", campo="acompanhantes")
    if isinstance(quantidade, bool) or not isinstance(quantidade, int):
        raise RegraNegocioErro("E09", campo="acompanhantes")
    if not MIN_ACOMPANHANTES <= quantidade <= MAX_ACOMPANHANTES:
        raise RegraNegocioErro("E09", campo="acompanhantes")
    return quantidade


def total_pessoas_confirmadas(convidados) -> int:
    """RN15: soma de (1 + acompanhantes) dos convidados com status Confirmado."""
    return sum(1 + c.acompanhantes for c in convidados if c.status_rsvp == StatusRSVP.CONFIRMADO)


def custo_por_convidado(total_contratado, pessoas_confirmadas: int) -> Decimal | None:
    """RN15: total contratado ÷ pessoas confirmadas. Sem confirmados devolve None (exibido “—”)."""
    if pessoas_confirmadas <= 0:
        return None
    return quantizar(quantizar(total_contratado) / pessoas_confirmadas)


@dataclass(frozen=True)
class ResumoConvidados:
    cadastrados: int
    confirmados: int
    pendentes: int
    recusados: int
    pessoas_confirmadas: int
    pessoas_convidadas: int  # todos os convites com acompanhantes, exceto recusados


def resumo_convidados(convidados) -> ResumoConvidados:
    """RF13: contagens por status e total de pessoas."""
    convidados = list(convidados)
    por_status = {status: 0 for status in StatusRSVP.VALORES}
    for convidado in convidados:
        por_status[convidado.status_rsvp] += 1
    return ResumoConvidados(
        cadastrados=len(convidados),
        confirmados=por_status[StatusRSVP.CONFIRMADO],
        pendentes=por_status[StatusRSVP.PENDENTE],
        recusados=por_status[StatusRSVP.RECUSADO],
        pessoas_confirmadas=total_pessoas_confirmadas(convidados),
        pessoas_convidadas=sum(1 + c.acompanhantes for c in convidados
                               if c.status_rsvp != StatusRSVP.RECUSADO),
    )


# --------------------------------------------------------------------------- operações


def listar_convidados(casamento, grupo: str | None = None, status: str | None = None) -> list[Convidado]:
    consulta = db.select(Convidado).filter_by(casamento_id=casamento.id)
    if grupo in Grupo.VALORES:
        consulta = consulta.filter_by(grupo=grupo)
    if status in StatusRSVP.VALORES:
        consulta = consulta.filter_by(status_rsvp=status)
    return list(db.session.scalars(consulta.order_by(db.func.lower(Convidado.nome))))


def salvar_convidado(casamento, convidado: Convidado | None, *, nome: str, grupo: str,
                     telefone: str | None, email: str | None, acompanhantes) -> Convidado:
    """Inclui (convidado=None) ou altera um convidado. Novo convidado começa como Pendente (UC11)."""
    acompanhantes = validar_acompanhantes(acompanhantes)
    if grupo not in Grupo.VALORES:
        raise RegraNegocioErro("E01", campo="grupo", texto="Escolha um grupo da lista.")
    if convidado is None:
        convidado = Convidado(casamento_id=casamento.id, status_rsvp=StatusRSVP.PENDENTE)
        db.session.add(convidado)
    convidado.nome = nome.strip()
    convidado.grupo = grupo
    convidado.telefone = telefone or None
    convidado.email = email or None
    convidado.acompanhantes = acompanhantes
    db.session.commit()
    return convidado


def alterar_status(convidado: Convidado, status: str) -> Convidado:
    if status not in StatusRSVP.VALORES:
        raise RegraNegocioErro("E01", campo="status", texto="Status de confirmação inválido.")
    convidado.status_rsvp = status
    db.session.commit()
    return convidado


def excluir_convidado(convidado: Convidado) -> None:
    db.session.delete(convidado)
    db.session.commit()
