"""Utilitários compartilhados pelos controllers: acesso ao casamento e isolamento entre contas."""
from functools import wraps
from urllib.parse import urlsplit

from flask import flash, g, redirect, request, url_for
from flask_login import current_user, login_required

from app.extensions import db
from app.models import Categoria, Convidado, Despesa, Fornecedor, Parcela
from app.services.erros import RegraNegocioErro


def casamento_obrigatorio(view):
    """Exige login e casamento configurado; disponibiliza o casamento em g.casamento.

    Sem casamento, leva para a tela Meu casamento (T03, primeiro acesso).
    """
    @wraps(view)
    def envoltorio(*args, **kwargs):
        casamento = current_user.casamento
        if casamento is None:
            flash("Antes de começar, conte um pouco sobre o casamento.", "aviso")
            return redirect(url_for("casamento.editar"))
        g.casamento = casamento
        return view(*args, **kwargs)

    return login_required(envoltorio)


# --- RNF08: cada busca por id é filtrada pelo casamento do usuário; o que não é dele vira 404.

def obter_categoria(categoria_id: int) -> Categoria:
    return db.first_or_404(db.select(Categoria).filter_by(id=categoria_id, casamento_id=g.casamento.id))


def obter_fornecedor(fornecedor_id: int) -> Fornecedor:
    return db.first_or_404(
        db.select(Fornecedor).join(Categoria)
        .where(Fornecedor.id == fornecedor_id, Categoria.casamento_id == g.casamento.id)
    )


def obter_despesa(despesa_id: int) -> Despesa:
    return db.first_or_404(
        db.select(Despesa).join(Categoria)
        .where(Despesa.id == despesa_id, Categoria.casamento_id == g.casamento.id)
    )


def obter_parcela(parcela_id: int) -> Parcela:
    return db.first_or_404(
        db.select(Parcela).join(Despesa).join(Categoria)
        .where(Parcela.id == parcela_id, Categoria.casamento_id == g.casamento.id)
    )


def obter_convidado(convidado_id: int) -> Convidado:
    return db.first_or_404(db.select(Convidado).filter_by(id=convidado_id, casamento_id=g.casamento.id))


# --- Formulários e navegação

def aplicar_erro(form, erro: RegraNegocioErro) -> None:
    """Mostra o erro ao lado do campo (UC07 4a); sem campo correspondente, no topo da página."""
    db.session.rollback()
    campo = getattr(form, erro.campo, None) if erro.campo else None
    if campo is not None:
        campo.errors = [*campo.errors, erro.mensagem]
    else:
        flash(erro.mensagem, "erro")


def destino_seguro(padrao: str) -> str:
    """Volta para a página indicada em ?proximo= (ou ?next=, usado pelo Flask-Login) somente se for interna."""
    destino = request.values.get("proximo") or request.values.get("next") or ""
    partes = urlsplit(destino)
    interno = destino.startswith("/") and not destino.startswith("//") and "\\" not in destino
    if interno and not partes.netloc and not partes.scheme:
        return destino
    return padrao


def flash_avisos(avisos: list[str]) -> None:
    for aviso in avisos:
        flash(aviso, "aviso")
