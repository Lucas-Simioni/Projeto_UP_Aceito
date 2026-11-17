"""Datas no fuso do casal (o servidor de produção roda em UTC)."""
import calendar
from datetime import date, datetime
from zoneinfo import ZoneInfo

FUSO_HORARIO = ZoneInfo("America/Sao_Paulo")


def agora() -> datetime:
    """Data e hora atuais em Brasília, sem informação de fuso (como é gravado no banco)."""
    return datetime.now(FUSO_HORARIO).replace(tzinfo=None)


def hoje() -> date:
    return agora().date()


def somar_meses(data: date, meses: int, dia_base: int | None = None) -> date:
    """Soma meses mantendo o dia; se o mês não tiver esse dia, usa o último dia do mês (RN08)."""
    dia_base = dia_base or data.day
    indice = data.month - 1 + meses
    ano, mes = data.year + indice // 12, indice % 12 + 1
    ultimo_dia = calendar.monthrange(ano, mes)[1]
    return date(ano, mes, min(dia_base, ultimo_dia))
