from app.extensions import db
from app.models.dominios import CHECK_STATUS_FORNECEDOR, StatusFornecedor


class Fornecedor(db.Model):
    """Empresa ou profissional orçado em uma categoria."""

    __tablename__ = "fornecedor"
    __table_args__ = (
        db.CheckConstraint("valor_orcado >= 0", name="orcado_nao_negativo"),
        db.CheckConstraint(CHECK_STATUS_FORNECEDOR, name="status_valido"),
        db.Index("idx_fornecedor_categoria", "categoria_id"),
    )

    id = db.Column(db.Integer, primary_key=True)
    categoria_id = db.Column(db.Integer, db.ForeignKey("categoria.id", ondelete="RESTRICT"), nullable=False)
    nome = db.Column(db.String(120), nullable=False)
    telefone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    valor_orcado = db.Column(db.Numeric(12, 2))
    status = db.Column(db.String(12), nullable=False, default=StatusFornecedor.ORCAMENTO,
                       server_default=StatusFornecedor.ORCAMENTO)
    observacoes = db.Column(db.Text)

    categoria = db.relationship("Categoria", back_populates="fornecedores")
    # Excluir o fornecedor mantém as despesas e só remove o vínculo (ON DELETE SET NULL).
    despesas = db.relationship("Despesa", back_populates="fornecedor", passive_deletes=True)

    def aceita_despesa(self) -> bool:
        """RN12: fornecedor descartado não recebe novas despesas."""
        return self.status != StatusFornecedor.DESCARTADO

    @property
    def status_rotulo(self) -> str:
        return StatusFornecedor.rotulo(self.status)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Fornecedor {self.id} {self.nome}>"
