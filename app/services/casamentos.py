"""Configuração do casamento (UC03, RN01–RN03) e criação das categorias padrão (RF04)."""
from app.extensions import db
from app.models import Casamento, Categoria
from app.services import orcamento
from app.services.erros import RegraNegocioErro


def salvar_casamento(usuario, *, nome_casal: str, data_casamento, local: str | None,
                     orcamento_total, convidados_estimados: int | None) -> tuple[Casamento, bool]:
    """Cria (primeiro acesso) ou atualiza o casamento da conta.

    Devolve (casamento, criado). Ao criar, gera as oito categorias padrão com valor planejado zero.
    """
    data_cadastro = usuario.criado_em.date()
    orcamento.validar_data_casamento(data_casamento, data_cadastro)
    orcamento_total = orcamento.validar_valor_positivo(orcamento_total, "orcamento_total")
    if convidados_estimados is not None and convidados_estimados < 0:
        raise RegraNegocioErro("E06", campo="convidados_estimados",
                               texto="O número de convidados não pode ser negativo.")

    casamento = usuario.casamento
    criado = casamento is None
    if criado:  # RN01: no máximo um casamento por conta
        casamento = Casamento(usuario_id=usuario.id)
        db.session.add(casamento)

    casamento.nome_casal = nome_casal.strip()
    casamento.data_casamento = data_casamento
    casamento.local = (local or "").strip() or None
    casamento.orcamento_total = orcamento_total
    casamento.convidados_estimados = convidados_estimados

    if criado:
        db.session.flush()  # obtém o id para as categorias
        for nome in orcamento.CATEGORIAS_PADRAO:
            db.session.add(Categoria(casamento_id=casamento.id, nome=nome))
    db.session.commit()
    return casamento, criado
