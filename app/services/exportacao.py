"""Exportação CSV (RF14).

Separador ";" e vírgula decimal, para o arquivo abrir direto no Excel em português.
O BOM UTF-8 é acrescentado pelo controller, para os acentos aparecerem corretamente.
"""
import csv
import io
from datetime import date

from app.services.dinheiro import formatar_numero


def _data(valor: date | None) -> str:
    return valor.strftime("%d/%m/%Y") if valor else ""


_INICIO_FORMULA = ("=", "+", "-", "@", "\t", "\r")


def _celula(valor):
    """Neutraliza texto que o Excel interpretaria como fórmula (injeção de CSV)."""
    if isinstance(valor, str) and valor.startswith(_INICIO_FORMULA):
        return "'" + valor
    return valor


def _gerar(cabecalho: list[str], linhas) -> str:
    saida = io.StringIO()
    escritor = csv.writer(saida, delimiter=";", lineterminator="\r\n")
    escritor.writerow(cabecalho)
    escritor.writerows([_celula(v) for v in linha] for linha in linhas)
    return saida.getvalue()


def csv_convidados(convidados) -> str:
    cabecalho = ["Nome", "Grupo", "Telefone", "E-mail", "Acompanhantes", "Total de pessoas", "Confirmação"]
    linhas = (
        [c.nome, c.grupo_rotulo, c.telefone or "", c.email or "", c.acompanhantes, c.total_pessoas(),
         c.status_rotulo]
        for c in convidados
    )
    return _gerar(cabecalho, linhas)


def csv_parcelas(parcelas, hoje: date) -> str:
    cabecalho = ["Despesa", "Categoria", "Parcela", "Valor (R$)", "Vencimento", "Pagamento", "Situação"]
    linhas = (
        [p.despesa.descricao, p.despesa.categoria.nome, f"{p.numero}/{p.despesa.num_parcelas}",
         formatar_numero(p.valor), _data(p.data_vencimento), _data(p.data_pagamento), p.situacao(hoje)]
        for p in parcelas
    )
    return _gerar(cabecalho, linhas)
