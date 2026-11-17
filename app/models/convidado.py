from app.extensions import db
from app.models.dominios import CHECK_GRUPO, CHECK_STATUS_RSVP, Grupo, StatusRSVP


class Convidado(db.Model):
    """Pessoa convidada. O casal registra a resposta (RSVP) – o convidado não acessa o sistema."""

    __tablename__ = "convidado"
    __table_args__ = (
        db.CheckConstraint(CHECK_GRUPO, name="grupo_valido"),
        db.CheckConstraint("acompanhantes BETWEEN 0 AND 10", name="acompanhantes_intervalo"),
        db.CheckConstraint(CHECK_STATUS_RSVP, name="status_rsvp_valido"),
        db.Index("idx_convidado_casamento", "casamento_id", "status_rsvp"),
    )

    id = db.Column(db.Integer, primary_key=True)
    casamento_id = db.Column(db.Integer, db.ForeignKey("casamento.id", ondelete="CASCADE"), nullable=False)
    nome = db.Column(db.String(120), nullable=False)
    telefone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    grupo = db.Column(db.String(15), nullable=False, default=Grupo.OUTROS, server_default=Grupo.OUTROS)
    acompanhantes = db.Column(db.SmallInteger, nullable=False, default=0, server_default="0")
    status_rsvp = db.Column(db.String(10), nullable=False, default=StatusRSVP.PENDENTE,
                            server_default=StatusRSVP.PENDENTE)

    casamento = db.relationship("Casamento", back_populates="convidados")

    def total_pessoas(self) -> int:
        """O convidado mais os acompanhantes."""
        return 1 + self.acompanhantes

    @property
    def grupo_rotulo(self) -> str:
        return Grupo.rotulo(self.grupo)

    @property
    def status_rotulo(self) -> str:
        return StatusRSVP.rotulo(self.status_rsvp)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Convidado {self.id} {self.nome}>"
