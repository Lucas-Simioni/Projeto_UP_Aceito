"""Comandos de linha de comando (flask <comando>)."""
import random
from datetime import timedelta
from decimal import Decimal

import click
from flask import Flask

from app.extensions import db
from app.models import Convidado, Fornecedor, Usuario
from app.models.dominios import Grupo, StatusFornecedor, StatusRSVP
from app.services import casamentos, contas, datas, despesas
from app.services.datas import somar_meses

EMAIL_EXEMPLO = "exemplo@aceito.app"
SENHA_EXEMPLO = "aceito2026"

PLANEJADO = {
    "Local": "9000", "Buffet": "21000", "Decoração": "7000", "Fotografia e vídeo": "6000",
    "Música": "4000", "Trajes": "6000", "Convites e papelaria": "2000", "Outros": "5000",
}
FORNECEDORES = [
    # (categoria, nome, valor orçado, status)
    ("Local", "Espaço Jardim das Flores", "8500", StatusFornecedor.ORCAMENTO),
    ("Buffet", "Buffet Sabor & Arte", "22000", StatusFornecedor.ORCAMENTO),
    ("Buffet", "Buffet Bem Servir", "19800", StatusFornecedor.ORCAMENTO),
    ("Fotografia e vídeo", "Estúdio Luz Natural", "5200", StatusFornecedor.ORCAMENTO),
    ("Fotografia e vídeo", "Clique Eterno Fotografia", "6400", StatusFornecedor.ORCAMENTO),
    ("Música", "Banda Noite Feliz", "3800", StatusFornecedor.ORCAMENTO),
    ("Decoração", "Ateliê Flor de Sal", "7600", StatusFornecedor.ORCAMENTO),
    ("Decoração", "Decor Simples", "9100", StatusFornecedor.DESCARTADO),
]
DESPESAS = [
    # (fornecedor, descrição, valor, parcelas, meses atrás da contratação)
    ("Espaço Jardim das Flores", "Locação do espaço com cerimônia e festa", "8500", 5, 3),
    ("Buffet Sabor & Arte", "Buffet completo para 150 pessoas", "22000", 10, 2),
    ("Estúdio Luz Natural", "Fotografia e vídeo do dia", "5200", 4, 1),
    ("Ateliê Flor de Sal", "Decoração da cerimônia e da festa", "7600", 4, 0),
]
NOMES = ["Ana", "Bruno", "Carla", "Diego", "Elisa", "Felipe", "Gabriela", "Henrique", "Isabela", "João",
         "Larissa", "Marcos", "Natália", "Otávio", "Paula", "Rafael", "Sofia", "Tiago", "Vitória", "William"]
SOBRENOMES = ["Silva", "Souza", "Oliveira", "Santos", "Lima", "Pereira", "Costa", "Almeida", "Rocha", "Martins"]


def registrar_comandos(app: Flask) -> None:
    @app.cli.command("popular-exemplo")
    @click.option("--convidados", default=150, show_default=True, help="Quantidade de convidados.")
    def popular_exemplo(convidados: int):
        """Cria a conta de exemplo da persona (Juliana & Rafael) com dados de demonstração."""
        if contas.email_cadastrado(EMAIL_EXEMPLO):
            click.echo(f"A conta {EMAIL_EXEMPLO} já existe. Nada foi alterado.")
            return
        hoje = datas.hoje()
        usuario = contas.criar_conta("Juliana", EMAIL_EXEMPLO, SENHA_EXEMPLO)
        usuario.criado_em = usuario.criado_em - timedelta(days=120)
        casamento, _ = casamentos.salvar_casamento(
            usuario, nome_casal="Juliana & Rafael", data_casamento=somar_meses(hoje, 10),
            local="Espaço Jardim das Flores", orcamento_total=Decimal("60000"), convidados_estimados=150,
        )
        categorias = {c.nome: c for c in casamento.categorias}
        for nome, valor in PLANEJADO.items():
            categorias[nome].valor_planejado = Decimal(valor)

        fornecedores = {}
        for categoria, nome, valor, status in FORNECEDORES:
            fornecedor = Fornecedor(categoria=categorias[categoria], nome=nome, valor_orcado=Decimal(valor),
                                    status=status, telefone="(11) 99999-0000")
            db.session.add(fornecedor)
            fornecedores[nome] = fornecedor
        db.session.commit()

        for nome_fornecedor, descricao, valor, parcelas, meses in DESPESAS:
            fornecedor = fornecedores[nome_fornecedor]
            contratacao = somar_meses(hoje, -meses)
            despesa, _ = despesas.registrar_despesa(casamento, despesas.DadosDespesa(
                categoria_id=fornecedor.categoria_id, fornecedor_id=fornecedor.id, descricao=descricao,
                valor_total=Decimal(valor), data_contratacao=contratacao, num_parcelas=parcelas,
                primeiro_vencimento=contratacao + timedelta(days=10),
            ))
            # Paga as parcelas vencidas, menos uma, para o painel mostrar um atraso real.
            vencidas = [p for p in despesa.parcelas if p.data_vencimento < hoje]
            for parcela in vencidas[:-1] if meses == 2 else vencidas:
                despesas.pagar_parcela(parcela, parcela.data_vencimento, hoje)

        sorteio = random.Random(42)
        for i in range(convidados):
            db.session.add(Convidado(
                casamento_id=casamento.id,
                nome=f"{NOMES[i % len(NOMES)]} {SOBRENOMES[(i // len(NOMES)) % len(SOBRENOMES)]}",
                grupo=sorteio.choice(Grupo.VALORES),
                acompanhantes=sorteio.choice([0, 0, 0, 1, 1, 2]),
                status_rsvp=sorteio.choice([StatusRSVP.CONFIRMADO, StatusRSVP.CONFIRMADO,
                                            StatusRSVP.PENDENTE, StatusRSVP.RECUSADO]),
            ))
        db.session.commit()
        click.echo(f"Conta de exemplo criada: {EMAIL_EXEMPLO} / senha {SENHA_EXEMPLO}")

    @app.cli.command("verificar-usuario")
    @click.argument("email")
    def verificar_usuario(email: str):
        """Mostra como a senha está gravada (RNF06: deve ser um hash, nunca a senha)."""
        usuario = db.session.scalar(db.select(Usuario).filter_by(email=contas.normalizar_email(email)))
        if usuario is None:
            click.echo("Usuário não encontrado.")
            return
        click.echo(f"{usuario.email}: senha_hash = {usuario.senha_hash[:30]}…")
