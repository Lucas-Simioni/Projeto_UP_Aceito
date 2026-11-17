"""Regras puras de orçamento, categorias e alertas (RN02–RN06, RN09, RN10, RN12, RN13)."""
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from app.services.dinheiro import ZERO, formatar_moeda, quantizar
from app.services.erros import RegraNegocioErro
from app.services.mensagens import mensagem

CATEGORIAS_PADRAO = (
    "Local",
    "Buffet",
    "Decoração",
    "Fotografia e vídeo",
    "Música",
    "Trajes",
    "Convites e papelaria",
    "Outros",
)

LIMITE_ATENCAO = Decimal("0.90")


class SituacaoCategoria:
    DENTRO = "Dentro do planejado"
    ATENCAO = "Atenção"
    ACIMA = "Acima do planejado"


# --------------------------------------------------------------------------- validações


def validar_valor_positivo(valor, campo: str) -> Decimal:
    """RN03: orçamento total e valor de despesa devem ser maiores que zero."""
    if valor is None:
        raise RegraNegocioErro("E01", campo=campo)
    valor = quantizar(valor)
    if valor <= 0:
        raise RegraNegocioErro("E06", campo=campo)
    return valor


def validar_valor_nao_negativo(valor, campo: str) -> Decimal | None:
    """RN03: valores planejados e orçados podem ser zero, nunca negativos. None = não informado."""
    if valor is None:
        return None
    valor = quantizar(valor)
    if valor < 0:
        raise RegraNegocioErro("E06", campo=campo, texto="O valor não pode ser negativo.")
    return valor


def validar_data_casamento(data_casamento: date | None, data_cadastro: date) -> date:
    """RN02: a data do casamento deve ser posterior à data do cadastro da conta."""
    if data_casamento is None:
        raise RegraNegocioErro("E01", campo="data_casamento")
    if data_casamento <= data_cadastro:
        raise RegraNegocioErro("E05", campo="data_casamento")
    return data_casamento


def validar_fornecedor_para_despesa(status_fornecedor: str, categoria_fornecedor_id: int,
                                    nome_categoria_fornecedor: str, categoria_despesa_id: int) -> None:
    """RN12 (descartado não recebe despesa) e RN13 (mesma categoria do fornecedor)."""
    from app.models.dominios import StatusFornecedor  # import local evita ciclo models <-> services

    if status_fornecedor == StatusFornecedor.DESCARTADO:
        raise RegraNegocioErro("E12", campo="fornecedor_id")
    if categoria_fornecedor_id != categoria_despesa_id:
        raise RegraNegocioErro("E07", campo="fornecedor_id", categoria=nome_categoria_fornecedor)


# --------------------------------------------------------------------------- cálculos


def situacao_categoria(contratado, planejado) -> str:
    """RN05: < 90% Dentro; 90%–100% Atenção; > 100% Acima. Planejado zero com gasto = Acima."""
    contratado, planejado = quantizar(contratado), quantizar(planejado)
    if planejado == 0:
        return SituacaoCategoria.ACIMA if contratado > 0 else SituacaoCategoria.DENTRO
    proporcao = contratado / planejado
    if proporcao > 1:
        return SituacaoCategoria.ACIMA
    if proporcao >= LIMITE_ATENCAO:
        return SituacaoCategoria.ATENCAO
    return SituacaoCategoria.DENTRO


def percentual_utilizado(contratado, planejado) -> int | None:
    """Percentual inteiro do planejado já contratado; None quando não há valor planejado."""
    planejado = quantizar(planejado)
    if planejado == 0:
        return None
    return int((quantizar(contratado) / planejado * 100).to_integral_value())


def excedente(valor, limite) -> Decimal | None:
    """Quanto `valor` passou de `limite`; None se não passou."""
    valor, limite = quantizar(valor), quantizar(limite)
    return valor - limite if valor > limite else None


def alerta_orcamento(total_contratado, orcamento_total) -> Decimal | None:
    """RN06: valor excedente quando o total contratado passa do orçamento total."""
    return excedente(total_contratado, orcamento_total)


def alerta_planejado(soma_planejado, orcamento_total) -> Decimal | None:
    """RN04: aviso (não bloqueia) quando a soma dos planejados passa do orçamento total."""
    return excedente(soma_planejado, orcamento_total)


def saldo(orcamento_total, total_contratado) -> Decimal:
    """“Quanto ainda posso gastar” = orçamento total − total contratado."""
    return quantizar(orcamento_total) - quantizar(total_contratado)


# --------------------------------------------------------------------------- alertas do painel


class Tom:
    CRITICO = "critico"
    ATENCAO = "atencao"


@dataclass(frozen=True)
class Alerta:
    codigo: str
    texto: str
    tom: str
    destino: str | None = None  # nome do endpoint Flask para "ver detalhes"


def montar_alertas(*, orcamento_total, total_contratado, soma_planejado,
                   categorias: list[tuple[str, Decimal, Decimal]], qtd_atrasadas: int,
                   qtd_apos_casamento: int) -> list[Alerta]:
    """Reúne os alertas do painel em ordem de gravidade.

    `categorias` é uma lista de (nome, contratado, planejado).
    """
    alertas: list[Alerta] = []

    estouro = alerta_orcamento(total_contratado, orcamento_total)
    if estouro is not None:
        alertas.append(Alerta("A02", mensagem("A02", valor=formatar_moeda(estouro)), Tom.CRITICO,
                              "categorias.lista"))

    if qtd_atrasadas:
        alertas.append(Alerta("A05", mensagem("A05", n=qtd_atrasadas), Tom.CRITICO, "parcelas.lista"))

    for nome, contratado, planejado in categorias:
        if situacao_categoria(contratado, planejado) == SituacaoCategoria.ACIMA:
            valor = excedente(contratado, planejado) or ZERO
            alertas.append(Alerta("A01", mensagem("A01", categoria=nome, valor=formatar_moeda(valor)),
                                  Tom.ATENCAO, "categorias.lista"))

    if qtd_apos_casamento:
        alertas.append(Alerta("A03", mensagem("A03", n=qtd_apos_casamento), Tom.ATENCAO, "parcelas.lista"))

    planejado_excedente = alerta_planejado(soma_planejado, orcamento_total)
    if planejado_excedente is not None:
        alertas.append(Alerta("A04", mensagem("A04", valor=formatar_moeda(soma_planejado),
                                              orcamento=formatar_moeda(orcamento_total)),
                              Tom.ATENCAO, "categorias.lista"))
    return alertas
