"""Instâncias das extensões Flask, criadas sem aplicação (padrão application factory)."""
import sqlite3

from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect
from sqlalchemy import MetaData, event
from sqlalchemy.engine import Engine

# Nomes previsíveis para restrições: necessários para migrações estáveis (inclusive no SQLite).
NOMES_RESTRICOES = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

db = SQLAlchemy(metadata=MetaData(naming_convention=NOMES_RESTRICOES))
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()


@event.listens_for(Engine, "connect")
def _ativar_chaves_estrangeiras_sqlite(conexao, _registro):
    """O SQLite só respeita FOREIGN KEY / ON DELETE com este PRAGMA ligado."""
    if isinstance(conexao, sqlite3.Connection):
        cursor = conexao.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
