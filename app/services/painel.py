"""Montagem do painel (UC10, RF11): todos os números vêm do banco, nada é gravado (3FN)."""
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from app.models import Convidado, Parcela
from app.extensions import db
from app.services import categorias as servico_categorias
from app.services import convidados as servico_convidados
from app.services import orcamento, parcelamento
from app.services.dinheiro import somar

QTD_PROXIMAS_PARCELAS = 5


@dataclass(frozen=True)
class Painel:
    dias_restantes: int
    orcamento_total: Decimal
    total_planejado: Decimal
    total_contratado: Decimal
    total_pago: Decimal
    saldo: Decimal
    alertas: list[orcamento.Alerta]
    categorias: list[servico_categorias.ResumoCategoria]
    proximas_parcelas: list[Parcela]
    total_parcelas_abertas: int
    convidados: servico_convidados.ResumoConvidados
    custo_por_convidado: Decimal | None

    @property
    def grafico(self) -> dict:
        """Dados do gráfico “Gastos por categoria” (planejado × contratado)."""
        return {
            "rotulos": [c.nome for c in self.categorias],
            "planejado": [float(c.planejado) for c in self.categorias],
            "contratado": [float(c.contratado) for c in self.categorias],
        }

    @property
    def tem_gastos(self) -> bool:
        return any(c.planejado or c.contratado for c in self.categorias)


def montar_painel(casamento, hoje: date) -> Painel:
    categorias = servico_categorias.carregar_categorias(casamento)
    resumos = servico_categorias.resumir(categorias)
    parcelas = [p for c in categorias for d in c.despesas for p in d.parcelas]

    total_planejado = somar(r.planejado for r in resumos)
    total_contratado = somar(r.contratado for r in resumos)
    total_pago = somar(r.pago for r in resumos)

    abertas = sorted((p for p in parcelas if not p.paga), key=lambda p: (p.data_vencimento, p.numero))
    atrasadas = [p for p in abertas if p.situacao(hoje) == parcelamento.SituacaoParcela.ATRASADA]
    apos_casamento = parcelamento.parcelas_apos_casamento(parcelas, casamento.data_casamento)

    convidados = list(db.session.scalars(db.select(Convidado).filter_by(casamento_id=casamento.id)))
    resumo_convidados = servico_convidados.resumo_convidados(convidados)

    alertas = orcamento.montar_alertas(
        orcamento_total=casamento.orcamento_total,
        total_contratado=total_contratado,
        soma_planejado=total_planejado,
        categorias=[(r.nome, r.contratado, r.planejado) for r in resumos],
        qtd_atrasadas=len(atrasadas),
        qtd_apos_casamento=len(apos_casamento),
    )

    return Painel(
        dias_restantes=casamento.dias_restantes(hoje),
        orcamento_total=casamento.orcamento_total,
        total_planejado=total_planejado,
        total_contratado=total_contratado,
        total_pago=total_pago,
        saldo=orcamento.saldo(casamento.orcamento_total, total_contratado),
        alertas=alertas,
        categorias=resumos,
        proximas_parcelas=abertas[:QTD_PROXIMAS_PARCELAS],
        total_parcelas_abertas=len(abertas),
        convidados=resumo_convidados,
        custo_por_convidado=servico_convidados.custo_por_convidado(
            total_contratado, resumo_convidados.pessoas_confirmadas
        ),
    )
