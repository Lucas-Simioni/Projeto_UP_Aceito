"""Regras puras de parcelamento e situação de parcelas (RN07, RN08, RN09, RN10, RN11).

Nenhuma função deste módulo acessa o banco: todas recebem os dados e devolvem o resultado,
o que permite testá-las isoladamente (testes TU01–TU05, TU09 e TU10).
"""
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import ROUND_DOWN, Decimal

from app.services.datas import somar_meses
from app.services.dinheiro import CENTAVO, quantizar
from app.services.erros import RegraNegocioErro

MIN_PARCELAS = 1
MAX_PARCELAS = 24
DIAS_VENCE_EM_BREVE = 7
DIAS_PROXIMOS = 30


class SituacaoParcela:
    PAGA = "Paga"
    ATRASADA = "Atrasada"
    VENCE_EM_BREVE = "Vence em breve"
    PENDENTE = "Pendente"


@dataclass(frozen=True)
class ParcelaCalculada:
    numero: int
    valor: Decimal
    data_vencimento: date


def validar_numero_parcelas(quantidade) -> int:
    """RN08: de 1 a 24 parcelas."""
    if isinstance(quantidade, bool) or not isinstance(quantidade, int):
        raise RegraNegocioErro("E13", campo="num_parcelas")
    if not MIN_PARCELAS <= quantidade <= MAX_PARCELAS:
        raise RegraNegocioErro("E13", campo="num_parcelas")
    return quantidade


def dividir_valor(valor_total, quantidade: int) -> list[Decimal]:
    """RN07: divide e arredonda para baixo em centavos; a sobra vai para a primeira parcela.

    Exemplo: 1.000,00 em 3x -> [333,34, 333,33, 333,33]. A soma é sempre igual ao total.
    """
    validar_numero_parcelas(quantidade)
    total = quantizar(valor_total)
    if total <= 0:
        raise RegraNegocioErro("E06", campo="valor_total")
    if total < CENTAVO * quantidade:
        # Sem esta checagem, R$ 0,02 em 3x geraria parcelas de R$ 0,00.
        raise RegraNegocioErro(
            "E06", campo="valor_total", texto="O valor total precisa ser de pelo menos R$ 0,01 por parcela."
        )
    base = (total / quantidade).quantize(CENTAVO, rounding=ROUND_DOWN)
    primeira = total - base * (quantidade - 1)
    return [primeira] + [base] * (quantidade - 1)


def gerar_vencimentos(primeiro_vencimento: date, quantidade: int) -> list[date]:
    """RN08: vencimentos mensais no mesmo dia do primeiro; se o mês não tem o dia, usa o último.

    Cada data é calculada a partir do primeiro vencimento (não da anterior), então
    31/01 -> 28/02 -> 31/03, e não 31/01 -> 28/02 -> 28/03.
    """
    validar_numero_parcelas(quantidade)
    dia = primeiro_vencimento.day
    return [somar_meses(primeiro_vencimento, i, dia) for i in range(quantidade)]


def gerar_parcelas(valor_total, quantidade: int, primeiro_vencimento: date) -> list[ParcelaCalculada]:
    """UC08: combina a divisão do valor (RN07) com o calendário de vencimentos (RN08)."""
    valores = dividir_valor(valor_total, quantidade)
    vencimentos = gerar_vencimentos(primeiro_vencimento, quantidade)
    return [
        ParcelaCalculada(numero=i, valor=valor, data_vencimento=vencimento)
        for i, (valor, vencimento) in enumerate(zip(valores, vencimentos), start=1)
    ]


def situacao_parcela(data_vencimento: date, data_pagamento: date | None, hoje: date) -> str:
    """RN10: Paga > Atrasada > Vence em breve (hoje até 7 dias) > Pendente."""
    if data_pagamento is not None:
        return SituacaoParcela.PAGA
    if data_vencimento < hoje:
        return SituacaoParcela.ATRASADA
    if data_vencimento <= hoje + timedelta(days=DIAS_VENCE_EM_BREVE):
        return SituacaoParcela.VENCE_EM_BREVE
    return SituacaoParcela.PENDENTE


def validar_data_pagamento(data_pagamento: date | None, data_contratacao: date, hoje: date) -> date:
    """RN11: a data de pagamento não pode ser futura nem anterior à contratação."""
    if data_pagamento is None:
        raise RegraNegocioErro("E01", campo="data_pagamento")
    if data_pagamento > hoje or data_pagamento < data_contratacao:
        raise RegraNegocioErro("E08", campo="data_pagamento")
    return data_pagamento


def parcelas_apos_casamento(parcelas, data_casamento: date) -> list:
    """RN09: parcelas cujo vencimento cai depois da data do casamento."""
    return [p for p in parcelas if p.data_vencimento > data_casamento]


class FiltroParcela:
    TODAS = "todas"
    PENDENTES = "pendentes"
    ATRASADAS = "atrasadas"
    PAGAS = "pagas"
    PROXIMOS_30 = "proximos-30-dias"

    ROTULOS = {
        TODAS: "Todas",
        PENDENTES: "Pendentes",
        ATRASADAS: "Atrasadas",
        PAGAS: "Pagas",
        PROXIMOS_30: "Próximos 30 dias",
    }


def parcela_atende_filtro(data_vencimento: date, data_pagamento: date | None, filtro: str, hoje: date) -> bool:
    """RF10. "Pendentes" = todas as parcelas em aberto (ainda não pagas, atrasadas ou não)."""
    paga = data_pagamento is not None
    if filtro == FiltroParcela.PENDENTES:
        return not paga
    if filtro == FiltroParcela.ATRASADAS:
        return not paga and data_vencimento < hoje
    if filtro == FiltroParcela.PAGAS:
        return paga
    if filtro == FiltroParcela.PROXIMOS_30:
        return not paga and hoje <= data_vencimento <= hoje + timedelta(days=DIAS_PROXIMOS)
    return True
