from decimal import Decimal

from app.extensions import db
from app.services import orcamento
from app.services.dinheiro import somar


class Categoria(db.Model):
    """Divisão do orçamento (Local, Buffet, ...). Nome único dentro do casamento."""

    __tablename__ = "categoria"
    __table_args__ = (
        db.UniqueConstraint("casamento_id", "nome", name="uq_categoria_nome"),
        db.CheckConstraint("valor_planejado >= 0", name="planejado_nao_negativo"),
        db.Index("idx_categoria_casamento", "casamento_id"),
    )

    id = db.Column(db.Integer, primary_key=True)
    casamento_id = db.Column(db.Integer, db.ForeignKey("casamento.id"), nullable=False)
    nome = db.Column(db.String(60), nullable=False)
    valor_planejado = db.Column(db.Numeric(12, 2), nullable=False, default=Decimal("0.00"),
                                server_default="0")

    casamento = db.relationship("Casamento", back_populates="categorias")
    fornecedores = db.relationship("Fornecedor", back_populates="categoria", passive_deletes="all")
    despesas = db.relationship("Despesa", back_populates="categoria", passive_deletes="all")

    def total_contratado(self) -> Decimal:
        """Soma das despesas da categoria."""
        return somar(d.valor_total for d in self.despesas)

    def total_pago(self) -> Decimal:
        return somar(d.total_pago() for d in self.despesas)

    def situacao(self) -> str:
        """RN05."""
        return orcamento.situacao_categoria(self.total_contratado(), self.valor_planejado)

    def percentual(self) -> int | None:
        return orcamento.percentual_utilizado(self.total_contratado(), self.valor_planejado)

    def em_uso(self) -> bool:
        """RN14: categoria com fornecedores ou despesas não pode ser excluída."""
        return bool(self.fornecedores or self.despesas)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Categoria {self.id} {self.nome}>"
