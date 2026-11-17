"""Enumerações do dicionário de dados (StatusFornecedor, Grupo, StatusRSVP).

Gravadas como texto com CHECK no banco, exatamente como no schema.sql do planejamento.
"""


class _Dominio:
    ROTULOS: dict[str, str] = {}

    @classmethod
    def rotulo(cls, valor: str) -> str:
        return cls.ROTULOS.get(valor, valor)

    @classmethod
    def escolhas(cls) -> list[tuple[str, str]]:
        return list(cls.ROTULOS.items())


class StatusFornecedor(_Dominio):
    ORCAMENTO = "ORCAMENTO"
    CONTRATADO = "CONTRATADO"
    DESCARTADO = "DESCARTADO"
    ROTULOS = {ORCAMENTO: "Orçamento", CONTRATADO: "Contratado", DESCARTADO: "Descartado"}
    VALORES = tuple(ROTULOS)


class Grupo(_Dominio):
    FAMILIA_NOIVA = "FAMILIA_NOIVA"
    FAMILIA_NOIVO = "FAMILIA_NOIVO"
    AMIGOS = "AMIGOS"
    TRABALHO = "TRABALHO"
    OUTROS = "OUTROS"
    ROTULOS = {
        FAMILIA_NOIVA: "Família da noiva",
        FAMILIA_NOIVO: "Família do noivo",
        AMIGOS: "Amigos",
        TRABALHO: "Trabalho",
        OUTROS: "Outros",
    }
    VALORES = tuple(ROTULOS)


class StatusRSVP(_Dominio):
    PENDENTE = "PENDENTE"
    CONFIRMADO = "CONFIRMADO"
    RECUSADO = "RECUSADO"
    ROTULOS = {PENDENTE: "Pendente", CONFIRMADO: "Confirmado", RECUSADO: "Recusado"}
    VALORES = tuple(ROTULOS)


def _lista_sql(valores) -> str:
    return ", ".join(f"'{v}'" for v in valores)


CHECK_STATUS_FORNECEDOR = f"status IN ({_lista_sql(StatusFornecedor.VALORES)})"
CHECK_GRUPO = f"grupo IN ({_lista_sql(Grupo.VALORES)})"
CHECK_STATUS_RSVP = f"status_rsvp IN ({_lista_sql(StatusRSVP.VALORES)})"
