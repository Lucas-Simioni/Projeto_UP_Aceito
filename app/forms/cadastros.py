"""Formulários de cadastro: casamento, categoria, fornecedor, despesa, pagamento e convidado."""
from flask_wtf import FlaskForm
from wtforms import DateField, IntegerField, SelectField, StringField, TextAreaField
from wtforms.validators import Length, NumberRange, Optional

from app.forms.base import (FILTROS_TEXTO, FormularioBase, MoedaField, Obrigatorio, email_opcional,
                            telefone_opcional)
from app.models.dominios import Grupo, StatusFornecedor
from app.services.mensagens import mensagem


def _inteiro_ou_none(valor):
    try:
        return int(valor) if valor not in (None, "", "0") else None
    except (TypeError, ValueError):
        return None


class CasamentoForm(FormularioBase):
    nome_casal = StringField("Nome do casal", validators=[Obrigatorio(), Length(max=120)],
                             description="Ex.: Juliana & Rafael")
    data_casamento = DateField("Data do casamento", validators=[Obrigatorio()])
    local = StringField("Local", validators=[Optional(), Length(max=150)],
                        description="Cerimônia ou festa.")
    orcamento_total = MoedaField("Orçamento total (R$)", validators=[Obrigatorio()])
    convidados_estimados = IntegerField("Convidados estimados", validators=[
        Optional(), NumberRange(min=0, message="Informe um número igual ou maior que zero."),
    ], description="Só como referência.")


class CategoriaForm(FormularioBase):
    nome = StringField("Nome da categoria", validators=[Obrigatorio(), Length(max=60)])
    valor_planejado = MoedaField("Valor planejado (R$)", validators=[Optional()],
                                 description="Pode ser zero; deixe em branco se ainda não sabe.")


class FornecedorForm(FormularioBase):
    categoria_id = SelectField("Categoria", coerce=_inteiro_ou_none, validators=[Obrigatorio()],
                               validate_choice=False)
    nome = StringField("Nome do fornecedor", validators=[Obrigatorio(), Length(max=120)])
    telefone = StringField("Telefone", validators=telefone_opcional(), filters=FILTROS_TEXTO)
    email = StringField("E-mail", validators=email_opcional(), filters=FILTROS_TEXTO)
    valor_orcado = MoedaField("Valor orçado (R$)", validators=[Optional()])
    status = SelectField("Status", choices=StatusFornecedor.escolhas(), default=StatusFornecedor.ORCAMENTO)
    observacoes = TextAreaField("Observações", validators=[Optional()],
                                description="Condições, o que está incluído, prazos…")


class DespesaForm(FormularioBase):
    # validate_choice=False: a camada de serviços confere categoria e fornecedor e devolve
    # as mensagens específicas (E07, E12) em vez de um genérico "escolha inválida".
    categoria_id = SelectField("Categoria", coerce=_inteiro_ou_none, validators=[Obrigatorio()],
                               validate_choice=False)
    fornecedor_id = SelectField("Fornecedor", coerce=_inteiro_ou_none, validators=[Optional()],
                                validate_choice=False,
                                description="Opcional: deixe em branco para compras avulsas.")
    descricao = StringField("Descrição", validators=[Obrigatorio(), Length(max=150)],
                            description="Ex.: Buffet completo para 150 pessoas")
    valor_total = MoedaField("Valor total (R$)", validators=[Obrigatorio()])
    data_contratacao = DateField("Data da contratação", validators=[Obrigatorio()])
    num_parcelas = IntegerField("Número de parcelas", default=1, validators=[
        Obrigatorio(), NumberRange(min=1, max=24, message=mensagem("E13")),
    ])
    primeiro_vencimento = DateField("Primeiro vencimento", validators=[Obrigatorio()])


class PagamentoForm(FormularioBase):
    data_pagamento = DateField("Data do pagamento", validators=[Obrigatorio()])


class ConvidadoForm(FormularioBase):
    nome = StringField("Nome", validators=[Obrigatorio(), Length(max=120)])
    grupo = SelectField("Grupo", choices=Grupo.escolhas(), default=Grupo.OUTROS)
    telefone = StringField("Telefone", validators=telefone_opcional(), filters=FILTROS_TEXTO)
    email = StringField("E-mail", validators=email_opcional(), filters=FILTROS_TEXTO)
    acompanhantes = IntegerField("Acompanhantes", default=0, validators=[
        Obrigatorio(), NumberRange(min=0, max=10, message=mensagem("E09")),
    ], description="De 0 a 10 pessoas além do convidado.")


class AcaoForm(FlaskForm):
    """Formulário vazio: só leva o token CSRF em ações como excluir, estornar e mudar RSVP."""
