from datetime import date
from decimal import Decimal

from app.extensions import db
from app.models.parcela import Parcela
from app.services import parcelamento
from app.services.dinheiro import somar


class SituacaoDespesa:
    QUITADA = "Quitada"
    ATRASADA = "Com parcela atrasada"
    EM_DIA = "Em dia"


class Despesa(db.Model):
    """Contrato ou compra. É composta pelas suas parcelas (de 1 a 24)."""

    __tablename__ = "despesa"
    __table_args__ = (
        db.CheckConstraint("valor_total > 0", name="valor_positivo"),
        db.Index("idx_despesa_categoria", "categoria_id"),
    )

    id = db.Column(db.Integer, primary_key=True)
    categoria_id = db.Column(db.Integer, db.ForeignKey("categoria.id", ondelete="RESTRICT"), nullable=False)
    fornecedor_id = db.Column(db.Integer, db.ForeignKey("fornecedor.id", ondelete="SET NULL"))
    descricao = db.Column(db.String(150), nullable=False)
    valor_total = db.Column(db.Numeric(12, 2), nullable=False)
    data_contratacao = db.Column(db.Date, nullable=False)

    categoria = db.relationship("Categoria", back_populates="despesas")
    fornecedor = db.relationship("Fornecedor", back_populates="despesas")
    # Composição: as parcelas não existem sem a despesa e são excluídas junto (ON DELETE CASCADE).
    parcelas = db.relationship("Parcela", back_populates="despesa", order_by="Parcela.numero",
                               cascade="all, delete-orphan", passive_deletes=True)

    def gerar_parcelas(self, quantidade: int, primeiro_vencimento: date) -> list[Parcela]:
        """UC08: cria as parcelas a partir do valor total (RN07, RN08). A despesa não pode ter parcelas."""
        if self.parcelas:
            raise ValueError("Remova as parcelas atuais antes de gerar novas.")
        calculadas = parcelamento.gerar_parcelas(self.valor_total, quantidade, primeiro_vencimento)
        self.parcelas = [
            Parcela(numero=p.numero, valor=p.valor, data_vencimento=p.data_vencimento) for p in calculadas
        ]
        return self.parcelas

    @property
    def num_parcelas(self) -> int:
        return len(self.parcelas)

    @property
    def parcelas_pagas(self) -> int:
        return sum(1 for p in self.parcelas if p.paga)

    @property
    def primeiro_vencimento(self) -> date | None:
        return self.parcelas[0].data_vencimento if self.parcelas else None

    def tem_parcela_paga(self) -> bool:
        return self.parcelas_pagas > 0

    def total_pago(self) -> Decimal:
        return somar(p.valor for p in self.parcelas if p.paga)

    def quitada(self) -> bool:
        return bool(self.parcelas) and all(p.paga for p in self.parcelas)

    def situacao(self, hoje: date) -> str:
        if self.quitada():
            return SituacaoDespesa.QUITADA
        if any(p.situacao(hoje) == parcelamento.SituacaoParcela.ATRASADA for p in self.parcelas):
            return SituacaoDespesa.ATRASADA
        return SituacaoDespesa.EM_DIA

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Despesa {self.id} {self.descricao}>"
