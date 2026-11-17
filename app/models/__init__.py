"""Models SQLAlchemy: uma classe por tabela do diagrama de classes de persistência (seção 8)."""
from app.models.usuario import Usuario
from app.models.casamento import Casamento
from app.models.categoria import Categoria
from app.models.fornecedor import Fornecedor
from app.models.parcela import Parcela
from app.models.despesa import Despesa, SituacaoDespesa
from app.models.convidado import Convidado

__all__ = [
    "Usuario",
    "Casamento",
    "Categoria",
    "Fornecedor",
    "Despesa",
    "SituacaoDespesa",
    "Parcela",
    "Convidado",
]
