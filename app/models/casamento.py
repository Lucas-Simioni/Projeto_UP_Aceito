from datetime import date
from decimal import Decimal

from app.extensions import db
from app.services import orcamento
from app.services.dinheiro import somar


class Casamento(db.Model):
    """Dados gerais do evento. Cada usuário tem exatamente um casamento (RN01: usuario_id único)."""

    __tablename__ = "casamento"
    __table_args__ = (
        db.CheckConstraint("orcamento_total > 0", name="orcamento_positivo"),
        db.CheckConstraint("convidados_estimados >= 0", name="convidados_nao_negativo"),
    )

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuario.id"), nullable=False, unique=True)
    nome_casal = db.Column(db.String(120), nullable=False)
    data_casamento = db.Column(db.Date, nullable=False)
    local = db.Column(db.String(150))
    orcamento_total = db.Column(db.Numeric(12, 2), nullable=False)
    convidados_estimados = db.Column(db.Integer)

    usuario = db.relationship("Usuario", back_populates="casamento")
    categorias = db.relationship("Categoria", back_populates="casamento", order_by="Categoria.id")
    convidados = db.relationship("Convidado", back_populates="casamento",
                                 cascade="all, delete-orphan", passive_deletes=True)

    def dias_restantes(self, hoje: date) -> int:
        return (self.data_casamento - hoje).days

    def total_planejado(self) -> Decimal:
        return somar(c.valor_planejado for c in self.categorias)

    def total_contratado(self) -> Decimal:
        return somar(c.total_contratado() for c in self.categorias)

    def total_pago(self) -> Decimal:
        return somar(c.total_pago() for c in self.categorias)

    def saldo(self) -> Decimal:
        return orcamento.saldo(self.orcamento_total, self.total_contratado())

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Casamento {self.id} {self.nome_casal}>"
