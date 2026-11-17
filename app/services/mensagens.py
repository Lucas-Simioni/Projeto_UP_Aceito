"""Mensagens padronizadas da seção 15 do documento de planejamento (E01–E15, A01–A05, S01–S04, C01)."""

MENSAGENS = {
    # Erros
    "E01": "Preencha este campo.",
    "E02": "Já existe uma conta com este e-mail. Faça login ou use outro e-mail.",
    "E03": "E-mail ou senha incorretos.",
    "E04": "A senha precisa ter pelo menos 8 caracteres, com letras e números.",
    "E05": "A data do casamento precisa ser uma data futura.",
    "E06": "Informe um valor maior que zero.",
    "E07": "Este fornecedor é da categoria {categoria}. Escolha a mesma categoria ou outro fornecedor.",
    "E08": "A data de pagamento não pode ser futura nem anterior à data de contratação.",
    "E09": "O número de acompanhantes deve ficar entre 0 e 10.",
    "E10": "Esta categoria tem fornecedores ou despesas e não pode ser excluída.",
    "E11": "Esta despesa tem parcelas pagas. Estorne os pagamentos antes de alterar o valor ou excluir.",
    "E12": "Fornecedor descartado não pode receber despesas. Altere o status dele primeiro.",
    "E13": "O número de parcelas deve ficar entre 1 e 24.",
    "E14": "Página não encontrada.",
    "E15": "Algo deu errado do nosso lado. Tente novamente em instantes.",
    # Avisos
    "A01": "{categoria} passou do planejado em {valor}.",
    "A02": "O total contratado passou do orçamento em {valor}.",
    "A03": "{n} parcela(s) vencem depois da data do casamento.",
    "A04": "A soma dos valores planejados ({valor}) é maior que o orçamento total ({orcamento}).",
    "A05": "Você tem {n} parcela(s) atrasada(s).",
    # Sucessos
    "S01": "Salvo com sucesso.",
    "S02": "Pagamento registrado.",
    "S03": "Pagamento estornado. A parcela voltou a ficar em aberto.",
    "S04": "{item} excluído.",
    # Confirmação
    "C01": "Excluir {item}? Esta ação não pode ser desfeita.",
}


def mensagem(codigo: str, **valores) -> str:
    """Devolve o texto da mensagem com os campos {…} preenchidos."""
    return MENSAGENS[codigo].format(**valores)
