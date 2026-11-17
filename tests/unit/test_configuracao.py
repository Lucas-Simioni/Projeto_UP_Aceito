"""Credenciais por variáveis de ambiente (.env) e proteções da configuração de produção (RNF05)."""
import pytest

import config
from app import create_app

CHAVE_BOA = "a" * 64


def test_variavel_vazia_conta_como_nao_definida(monkeypatch):
    monkeypatch.setenv("ACEITO_TESTE", "   ")
    assert config.variavel("ACEITO_TESTE", "padrao") == "padrao"
    monkeypatch.setenv("ACEITO_TESTE", " valor ")
    assert config.variavel("ACEITO_TESTE", "padrao") == "valor"
    monkeypatch.delenv("ACEITO_TESTE")
    assert config.variavel("ACEITO_TESTE") is None


def test_url_do_banco_vazia_usa_sqlite_e_prefixo_antigo_e_corrigido(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "")
    assert config._url_banco("sqlite:///local.db") == "sqlite:///local.db"
    monkeypatch.setenv("DATABASE_URL", "postgres://u:s@host/banco")
    assert config._url_banco("x") == "postgresql://u:s@host/banco"


@pytest.mark.parametrize("colado", [
    "psql 'postgresql://u:s@host/banco?sslmode=require'",
    "'postgresql://u:s@host/banco?sslmode=require'",
    ' "postgresql://u:s@host/banco?sslmode=require" ',
])
def test_url_do_banco_colada_como_comando_psql_ou_com_aspas(monkeypatch, colado):
    monkeypatch.setenv("DATABASE_URL", colado)
    assert config._url_banco("x") == "postgresql://u:s@host/banco?sslmode=require"


def _producao(monkeypatch, chave, url):
    monkeypatch.setattr(config.ProductionConfig, "SECRET_KEY", chave)
    monkeypatch.setattr(config.ProductionConfig, "SQLALCHEMY_DATABASE_URI", "sqlite:///:memory:")
    if url is None:
        monkeypatch.delenv("DATABASE_URL", raising=False)
    else:
        monkeypatch.setenv("DATABASE_URL", url)
    return create_app("production")


@pytest.mark.parametrize("chave", [config.CHAVE_DESENVOLVIMENTO, "curta-demais"])
def test_producao_exige_secret_key_forte(monkeypatch, chave):
    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        _producao(monkeypatch, chave, "postgresql://u:s@host/banco")


@pytest.mark.parametrize("url", [None, ""])
def test_producao_exige_database_url(monkeypatch, url):
    with pytest.raises(RuntimeError, match="DATABASE_URL"):
        _producao(monkeypatch, CHAVE_BOA, url)


def test_producao_com_credenciais_sobe(monkeypatch):
    app = _producao(monkeypatch, CHAVE_BOA, "postgresql://u:s@host/banco")
    assert app.config["SESSION_COOKIE_SECURE"] is True


def test_database_url_invalida_nao_vaza_a_senha(monkeypatch, capsys):
    """Bloco copiado do Neon inteiro (comentário + DATABASE_URL="...") no campo da variável."""
    colado = '# Postgres\nDATABASE_URL="postgresql://dono:SENHA-SECRETA@host/banco"'
    monkeypatch.setattr(config.ProductionConfig, "SECRET_KEY", CHAVE_BOA)
    monkeypatch.setattr(config.ProductionConfig, "SQLALCHEMY_DATABASE_URI", colado)
    monkeypatch.setenv("DATABASE_URL", colado)
    with pytest.raises(RuntimeError, match="só o endereço") as erro:
        create_app("production")
    assert "SENHA-SECRETA" not in str(erro.value)
    assert erro.value.__cause__ is None and erro.value.__suppress_context__ is True


def test_app_env_invalido(monkeypatch):
    monkeypatch.setenv("APP_ENV", "producao")
    with pytest.raises(RuntimeError, match="APP_ENV"):
        create_app()
