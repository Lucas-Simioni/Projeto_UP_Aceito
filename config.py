"""Configurações da aplicação, selecionadas pela variável de ambiente APP_ENV (RNF05)."""
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

CHAVE_DESENVOLVIMENTO = "dev-chave-insegura-troque-em-producao"


def _url_banco(padrao: str) -> str:
    url = os.environ.get("DATABASE_URL", padrao)
    # Alguns provedores ainda entregam o prefixo antigo "postgres://".
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return url


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", CHAVE_DESENVOLVIMENTO)
    SQLALCHEMY_DATABASE_URI = _url_banco(f"sqlite:///{BASE_DIR / 'instance' / 'aceito.db'}")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}

    # Token CSRF vale enquanto durar a sessão (evita erro em formulários abertos há muito tempo).
    WTF_CSRF_TIME_LIMIT = None
    # Mensagens de validação do WTForms em português (traduções embutidas do WTForms).
    WTF_I18N_ENABLED = False

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    REMEMBER_COOKIE_HTTPONLY = True


class DevelopmentConfig(Config):
    DEBUG = True


class TestingConfig(Config):
    TESTING = True
    SECRET_KEY = "chave-de-teste"
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False


class ProductionConfig(Config):
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True
    PREFERRED_URL_SCHEME = "https"


configs = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}
