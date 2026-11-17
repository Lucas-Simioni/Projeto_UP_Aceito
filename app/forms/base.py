"""Base dos formulários: mensagens em português, campo de moeda e validadores comuns."""
from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import Email, Length, Optional, Regexp, StopValidation

from app.services.dinheiro import formatar_numero, interpretar_moeda
from app.services.mensagens import mensagem

MSG_OBRIGATORIO = mensagem("E01")
REGEX_TELEFONE = r"^\(\d{2}\) \d{4,5}-\d{4}$"


class FormularioBase(FlaskForm):
    class Meta:
        locales = ("pt_BR", "pt")


class Obrigatorio:
    """Como DataRequired, mas aceita 0 (Decimal("0") é falso em Python)."""

    field_flags = {"required": True}

    def __call__(self, form, field):
        if field.process_errors:
            # Valor digitado mas inválido (ex.: data malformada): mantém só esse erro.
            raise StopValidation()
        vazio = field.data is None or (isinstance(field.data, str) and not field.data.strip())
        if vazio:
            field.errors[:] = []
            raise StopValidation(MSG_OBRIGATORIO)


class MoedaField(StringField):
    """Campo de valor em reais. Aceita "1.234,56", "1234,56" ou "1234.56" e devolve Decimal."""

    def process_formdata(self, valuelist):
        self.data = None
        if valuelist and valuelist[0] and valuelist[0].strip():
            try:
                self.data = interpretar_moeda(valuelist[0])
            except ValueError as erro:
                raise ValueError(str(erro)) from erro

    def _value(self):
        if self.raw_data:
            return self.raw_data[0]
        return formatar_numero(self.data) if self.data is not None else ""


def sem_espacos(valor):
    """Filtro de campo: remove espaços nas pontas (comuns ao colar ou no autocompletar do celular)."""
    return valor.strip() if isinstance(valor, str) else valor


def telefone_opcional():
    return [Optional(), Length(max=20), Regexp(REGEX_TELEFONE, message="Use o formato (99) 99999-9999.")]


def email_opcional():
    return [Optional(), Length(max=120), Email(message="Informe um e-mail válido.")]


# Os campos de e-mail e telefone dos cadastros usam este filtro para ignorar espaços nas pontas.
FILTROS_TEXTO = [sem_espacos]
