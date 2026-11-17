"""Configurações da aplicação, selecionadas pela variável de ambiente APP_ENV (RNF05)."""
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
# Credenciais ficam no arquivo .env (fora do Git) ou nas variáveis de ambiente do servidor.
# override=False: uma variável já definida no sistema (ex.: no painel do Render) vale mais que o .env.
load_dotenv(BASE_DIR / ".env", override=False)

CHAVE_DESENVOLVIMENTO = "dev-chave-insegura-troque-em-producao"


def variavel(nome: str, padrao: str | None = None) -> str | None:
    """Lê uma variável de ambiente; valor vazio (ex.: `SECRET_KEY=` no .env) conta como não definido."""
    valor = os.environ.get(nome, "").strip()
    return valor or padrao


def _url_banco(padrao: str) -> str:
    url = variavel("DATABASE_URL", padrao)
    # Alguns provedores ainda entregam o prefixo antigo "postgres://".
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return url


class Config:
    SECRET_KEY = variavel("SECRET_KEY", CHAVE_DESENVOLVIMENTO)
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
