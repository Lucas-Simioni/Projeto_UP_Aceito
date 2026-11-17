from datetime import date

from app.extensions import db
from app.services import parcelamento
from app.services.erros import RegraNegocioErro


class Parcela(db.Model):
    """Pagamento de uma despesa. A situação não é gravada: é calculada (RN10, 3ª forma normal)."""

    __tablename__ = "parcela"
    __table_args__ = (
        db.UniqueConstraint("despesa_id", "numero", name="uq_parcela_numero"),
        db.CheckConstraint("numero BETWEEN 1 AND 24", name="numero_intervalo"),
        db.CheckConstraint("valor > 0", name="valor_positivo"),
        db.Index("idx_parcela_vencimento", "data_vencimento"),
    )

    id = db.Column(db.Integer, primary_key=True)
    despesa_id = db.Column(db.Integer, db.ForeignKey("despesa.id", ondelete="CASCADE"), nullable=False)
    numero = db.Column(db.SmallInteger, nullable=False)
    valor = db.Column(db.Numeric(12, 2), nullable=False)
    data_vencimento = db.Column(db.Date, nullable=False)
    data_pagamento = db.Column(db.Date)

    despesa = db.relationship("Despesa", back_populates="parcelas")

    @property
    def paga(self) -> bool:
        return self.data_pagamento is not None

    def situacao(self, hoje: date) -> str:
        return parcelamento.situacao_parcela(self.data_vencimento, self.data_pagamento, hoje)

    def pagar(self, data_pagamento: date | None, hoje: date) -> None:
        """UC09: grava o pagamento depois de validar a data (RN11). Recusa pagamento duplicado."""
        if self.paga:
            raise RegraNegocioErro("E08", texto="Esta parcela já foi paga.")
        self.data_pagamento = parcelamento.validar_data_pagamento(
            data_pagamento, self.despesa.data_contratacao, hoje
        )

    def estornar(self) -> None:
        """UC09 A1: apaga a data de pagamento; a parcela volta a Pendente ou Atrasada."""
        if not self.paga:
            raise RegraNegocioErro("E08", texto="Esta parcela não está paga.")
        self.data_pagamento = None

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Parcela {self.despesa_id}/{self.numero}>"
