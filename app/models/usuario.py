from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db
from app.services.datas import agora


class Usuario(UserMixin, db.Model):
    """Conta de acesso. A senha nunca é gravada, só o hash (RNF06)."""

    __tablename__ = "usuario"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False, unique=True)
    senha_hash = db.Column(db.String(255), nullable=False)
    criado_em = db.Column(db.DateTime, nullable=False, default=agora, server_default=db.func.current_timestamp())

    casamento = db.relationship("Casamento", back_populates="usuario", uselist=False)

    def definir_senha(self, senha: str) -> None:
        self.senha_hash = generate_password_hash(senha)

    def verificar_senha(self, senha: str) -> bool:
        return check_password_hash(self.senha_hash, senha)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Usuario {self.id} {self.email}>"
