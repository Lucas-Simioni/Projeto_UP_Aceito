"""Exceção única usada pela camada de serviços para sinalizar violação de regra de negócio."""
from app.services.mensagens import mensagem


class RegraNegocioErro(Exception):
    """Violação de uma regra de negócio.

    `codigo` é o código da mensagem padronizada (ex.: "E07"), `campo` é o nome do campo
    do formulário ao qual o erro se refere (ou None para erro geral da página).
    """

    def __init__(self, codigo: str, campo: str | None = None, texto: str | None = None, **valores):
        self.codigo = codigo
        self.campo = campo
        self.mensagem = texto or mensagem(codigo, **valores)
        super().__init__(self.mensagem)
