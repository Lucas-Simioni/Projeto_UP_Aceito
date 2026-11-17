"""Application factory do Aceito!."""
import logging
import os

from flask import Flask, render_template, request
from flask_wtf.csrf import CSRFError
from werkzeug.middleware.proxy_fix import ProxyFix

from config import CHAVE_DESENVOLVIMENTO, configs, variavel
from app.extensions import csrf, db, login_manager, migrate

TAMANHO_MINIMO_CHAVE = 32


def create_app(nome_config: str | None = None) -> Flask:
    nome_config = nome_config or variavel("APP_ENV", "development")
    if nome_config not in configs:
        raise RuntimeError(f"APP_ENV inválido: {nome_config!r}. Use development, testing ou production.")
    app = Flask(__name__)
    app.config.from_object(configs[nome_config])
    _validar_configuracao_producao(app, nome_config)
    os.makedirs(app.instance_path, exist_ok=True)

    db.init_app(app)
    migrate.init_app(app, db, render_as_batch=True)
    csrf.init_app(app)
    _configurar_login(app)

    if nome_config == "production":
        # O Render termina o HTTPS no proxy; isto faz o Flask enxergar o esquema/host reais.
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    from app import models  # noqa: F401 - registra os models no SQLAlchemy

    _registrar_blueprints(app)
    _registrar_filtros(app)
    _registrar_erros(app)

    from app.comandos import registrar_comandos
    registrar_comandos(app)
    return app


def _validar_configuracao_producao(app: Flask, nome_config: str) -> None:
    if nome_config != "production":
        return
    chave = app.config["SECRET_KEY"]
    if chave == CHAVE_DESENVOLVIMENTO or len(chave) < TAMANHO_MINIMO_CHAVE:
        raise RuntimeError("Defina a variável de ambiente SECRET_KEY em produção "
                           f"(valor aleatório com pelo menos {TAMANHO_MINIMO_CHAVE} caracteres).")
    if not variavel("DATABASE_URL"):
        raise RuntimeError("Defina a variável de ambiente DATABASE_URL em produção.")


def _configurar_login(app: Flask) -> None:
    from app.models import Usuario

    login_manager.init_app(app)
    login_manager.login_view = "auth.entrar"
    login_manager.login_message = "Entre na sua conta para continuar."
    login_manager.login_message_category = "aviso"
    login_manager.session_protection = "basic"

    @login_manager.user_loader
    def carregar_usuario(usuario_id: str):
        return db.session.get(Usuario, int(usuario_id))


def _registrar_blueprints(app: Flask) -> None:
    from app.controllers import (auth, casamento, categorias, convidados, despesas, fornecedores,
                                 painel, parcelas)

    for modulo in (auth, painel, casamento, categorias, fornecedores, despesas, parcelas, convidados):
        app.register_blueprint(modulo.bp)


def _registrar_filtros(app: Flask) -> None:
    from app.views import registrar_auxiliares_de_template

    registrar_auxiliares_de_template(app)


def _registrar_erros(app: Flask) -> None:
    @app.errorhandler(404)
    def nao_encontrado(_erro):
        return render_template("erros/404.html"), 404

    @app.errorhandler(CSRFError)
    def csrf_invalido(_erro):
        return render_template("erros/400.html"), 400

    @app.errorhandler(500)
    def erro_interno(erro):
        db.session.rollback()
        logging.getLogger(__name__).exception("Erro inesperado em %s", request.path, exc_info=erro)
        return render_template("erros/500.html"), 500
