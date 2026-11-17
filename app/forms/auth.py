from wtforms import EmailField, PasswordField, StringField
from wtforms.validators import Email, EqualTo, Length

from app.forms.base import FormularioBase, Obrigatorio, sem_espacos


class CriarContaForm(FormularioBase):
    nome = StringField("Seu nome", validators=[Obrigatorio(), Length(max=100)], filters=[sem_espacos])
    email = EmailField("E-mail", filters=[sem_espacos], validators=[
        Obrigatorio(), Length(max=120), Email(message="Informe um e-mail válido."),
    ])
    senha = PasswordField("Senha", validators=[Obrigatorio()])
    confirmar_senha = PasswordField("Confirme a senha", validators=[
        Obrigatorio(), EqualTo("senha", message="As senhas não são iguais."),
    ])


class EntrarForm(FormularioBase):
    email = EmailField("E-mail", validators=[Obrigatorio(), Length(max=120)], filters=[sem_espacos])
    senha = PasswordField("Senha", validators=[Obrigatorio()])
