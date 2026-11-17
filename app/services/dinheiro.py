"""Valores monetários: sempre Decimal com duas casas (RN03), formato brasileiro R$ 1.234,56 (RNF02)."""
import re
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

CENTAVO = Decimal("0.01")
ZERO = Decimal("0.00")

_SOMENTE_MILHAR = re.compile(r"-?\d{1,3}(\.\d{3})+")
_NUMERO = re.compile(r"-?\d+(\.\d{0,2})?")  # "4," (vírgula sem centavos) vale 4,00


def quantizar(valor) -> Decimal:
    """Converte para Decimal com duas casas. Floats passam por str() para não herdar imprecisão."""
    if valor is None:
        return ZERO
    if isinstance(valor, float):
        valor = str(valor)
    return Decimal(valor).quantize(CENTAVO, rounding=ROUND_HALF_UP)


def somar(valores) -> Decimal:
    return sum((quantizar(v) for v in valores), ZERO)


def interpretar_moeda(texto: str) -> Decimal:
    """Lê um valor digitado pelo usuário: "1.234,56", "1234,56", "1234.56" ou "R$ 1.234,56".

    Levanta ValueError se o texto não for um valor válido com até duas casas decimais.
    """
    limpo = (texto or "").replace("R$", "").replace(" ", "").replace(" ", "").strip()
    if not limpo:
        raise ValueError("Informe um valor.")
    if "," in limpo:
        limpo = limpo.replace(".", "").replace(",", ".")
    elif _SOMENTE_MILHAR.fullmatch(limpo):
        limpo = limpo.replace(".", "")
    if not _NUMERO.fullmatch(limpo):
        raise ValueError("Informe um valor válido, por exemplo 1.234,56.")
    try:
        return quantizar(limpo)
    except InvalidOperation as erro:  # pragma: no cover - regex já garante formato
        raise ValueError("Informe um valor válido, por exemplo 1.234,56.") from erro


def formatar_numero(valor) -> str:
    """1234.5 -> "1.234,50" (sem símbolo, usado para preencher campos de formulário)."""
    valor = quantizar(valor)
    sinal = "-" if valor < 0 else ""
    inteiro, centavos = f"{abs(valor):.2f}".split(".")
    return f"{sinal}{int(inteiro):,}".replace(",", ".") + f",{centavos}"


def formatar_moeda(valor) -> str:
    """1234.5 -> "R$ 1.234,50"; negativos ficam "-R$ 1.234,50"."""
    texto = formatar_numero(valor)
    if texto.startswith("-"):
        return f"-R$ {texto[1:]}"
    return f"R$ {texto}"
