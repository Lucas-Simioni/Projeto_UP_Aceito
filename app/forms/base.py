"""Base dos formulários: mensagens em português, campo de moeda e validadores comuns."""
import re

from flask_wtf import FlaskForm
from wtforms import IntegerField, StringField
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


class InteiroField(IntegerField):
    """Número inteiro. Campo apagado vira `vazio` (None = “Preencha este campo.” se obrigatório),
    em vez do genérico “O valor inteiro não é válido.”."""

    def __init__(self, *args, vazio=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.vazio = vazio

    def process_formdata(self, valuelist):
        if not valuelist or not str(valuelist[0]).strip():
            self.data = self.vazio
            return
        try:
            self.data = int(str(valuelist[0]).strip())
        except ValueError as erro:
            self.data = None
            raise ValueError("Informe um número inteiro, sem vírgula.") from erro


def sem_espacos(valor):
    """Filtro de campo: remove espaços nas pontas (comuns ao colar ou no autocompletar do celular)."""
    return valor.strip() if isinstance(valor, str) else valor


def formatar_telefone(valor):
    """Filtro de campo: “11987654321”, “+55 11 98765-4321” ou “(11)3456 7890” viram (99) 99999-9999.

    Sem JavaScript (ou ao colar o número) o campo chega sem máscara; aqui ele é padronizado.
    Números com quantidade de dígitos inesperada ficam como vieram e o validador avisa.
    """
    if not isinstance(valor, str) or not valor.strip():
        return valor
    digitos = re.sub(r"\D", "", valor)
    if len(digitos) in (12, 13) and digitos.startswith("55"):
        digitos = digitos[2:]
    if len(digitos) == 11:
        return f"({digitos[:2]}) {digitos[2:7]}-{digitos[7:]}"
    if len(digitos) == 10:
        return f"({digitos[:2]}) {digitos[2:6]}-{digitos[6:]}"
    return valor.strip()


def telefone_opcional():
    return [Optional(), Length(max=20), Regexp(REGEX_TELEFONE, message="Use o formato (99) 99999-9999.")]


def email_opcional():
    return [Optional(), Length(max=120), Email(message="Informe um e-mail válido.")]


# Os campos de e-mail e telefone dos cadastros usam este filtro para ignorar espaços nas pontas.
FILTROS_TEXTO = [sem_espacos]
FILTROS_TELEFONE = [sem_espacos, formatar_telefone]
