"""Contas de acesso (RN17, RNF06)."""
import re

from app.extensions import db
from app.models import Usuario
from app.services.erros import RegraNegocioErro

TAMANHO_MINIMO_SENHA = 8
_TEM_LETRA = re.compile(r"[A-Za-zÀ-ÿ]")
_TEM_NUMERO = re.compile(r"\d")


def normalizar_email(email: str) -> str:
    return (email or "").strip().lower()


def validar_senha(senha: str | None) -> bool:
    """RN17: pelo menos 8 caracteres, com ao menos uma letra e um número."""
    if not senha or len(senha) < TAMANHO_MINIMO_SENHA:
        return False
    return bool(_TEM_LETRA.search(senha) and _TEM_NUMERO.search(senha))


def email_cadastrado(email: str) -> bool:
    return db.session.scalar(db.select(Usuario.id).filter_by(email=normalizar_email(email))) is not None


def criar_conta(nome: str, email: str, senha: str) -> Usuario:
    """UC01: cria a conta. E-mail único (E02) e senha forte (E04)."""
    email = normalizar_email(email)
    if email_cadastrado(email):
        raise RegraNegocioErro("E02", campo="email")
    if not validar_senha(senha):
        raise RegraNegocioErro("E04", campo="senha")
    usuario = Usuario(nome=nome.strip(), email=email)
    usuario.definir_senha(senha)
    db.session.add(usuario)
    db.session.commit()
    return usuario


def autenticar(email: str, senha: str) -> Usuario | None:
    """UC02: devolve o usuário se e-mail e senha conferem; senão None (a tela mostra E03)."""
    usuario = db.session.scalar(db.select(Usuario).filter_by(email=normalizar_email(email)))
    if usuario is None or not usuario.verificar_senha(senha or ""):
        return None
    return usuario
