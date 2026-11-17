"""Filtros e funções globais do Jinja2 (só formatação: nenhuma regra de negócio aqui)."""
from datetime import date

from flask import Flask

from app.forms import AcaoForm
from app.services.dinheiro import formatar_moeda, formatar_numero
from app.services.mensagens import mensagem

MESES = ("jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez")

# Tom visual de cada situação: ok (verde), atencao (amarelo), critico (vermelho), neutro (cinza).
TOM_SITUACAO = {
    "Paga": "ok",
    "Quitada": "ok",
    "Em dia": "neutro",
    "Dentro do planejado": "ok",
    "Confirmado": "ok",
    "Contratado": "ok",
    "Atenção": "atencao",
    "Vence em breve": "atencao",
    "Pendente": "neutro",
    "Orçamento": "neutro",
    "Atrasada": "critico",
    "Com parcela atrasada": "critico",
    "Acima do planejado": "critico",
    "Recusado": "critico",
    "Descartado": "apagado",
}


def data_br(valor: date | None) -> str:
    return valor.strftime("%d/%m/%Y") if valor else "—"


def data_curta(valor: date | None) -> str:
    return f"{valor.day:02d} {MESES[valor.month - 1]}" if valor else "—"


def moeda(valor) -> str:
    return "—" if valor is None else formatar_moeda(valor)


def registrar_auxiliares_de_template(app: Flask) -> None:
    app.jinja_env.filters.update(
        moeda=moeda,
        numero=formatar_numero,
        data_br=data_br,
        data_curta=data_curta,
        tom=lambda situacao: TOM_SITUACAO.get(situacao, "neutro"),
    )
    app.jinja_env.globals.update(mensagem=mensagem)

    @app.context_processor
    def formulario_de_acao():
        # Um formulário só com CSRF, reaproveitado pelos botões Excluir / Estornar / RSVP.
        return {"form_acao": AcaoForm()}
