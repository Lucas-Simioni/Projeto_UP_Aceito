# Aceito!

Sistema web para o casal organizar o **orçamento, os fornecedores, as despesas parceladas e a lista de convidados** do casamento num só lugar. O painel mostra a qualquer momento quanto foi planejado, contratado e pago, o que vence nos próximos dias e quantas pessoas confirmaram presença.

> Projeto Integrador Transdisciplinar em Engenharia de Software II — Lucas Simioni
> Documento de planejamento: [`docs/situacao-1-planejamento/`](docs/situacao-1-planejamento/)

| | |
|---|---|
| Sistema publicado | _[link do Render — preencher após a publicação]_ |
| Vídeo de apresentação | [`docs/situacao-2-desenvolvimento/video-1.md`](docs/situacao-2-desenvolvimento/) |
| Manual de uso | [`docs/situacao-2-desenvolvimento/manual-de-uso.md`](docs/situacao-2-desenvolvimento/manual-de-uso.md) |
| Arquitetura e decisões | [`docs/arquitetura.md`](docs/arquitetura.md) |

## Funcionalidades

- Conta com login e logout; senha guardada só como hash.
- Dados do casamento e **oito categorias de gasto** criadas automaticamente.
- Orçamento por categoria com situação **Dentro do planejado / Atenção / Acima do planejado**.
- Fornecedores com status, **comparação de orçamentos** e destaque do menor valor.
- Despesas com **parcelamento automático** (1 a 24 parcelas, centavos na 1ª parcela, vencimento no último dia do mês quando necessário) e pré-visualização antes de salvar.
- Pagamento e **estorno** de parcelas, com filtros (pendentes, atrasadas, pagas, próximos 30 dias).
- **Painel** com contagem regressiva, totais, gráfico por categoria, alertas e próximas parcelas.
- Convidados com grupo, acompanhantes, **RSVP com um clique** e custo por convidado.
- Exportação de convidados e parcelas em **CSV** (abre direto no Excel).

## Tecnologias

Python 3.12 · Flask 3 · Flask-SQLAlchemy · Flask-Migrate · Flask-Login · Flask-WTF · Jinja2 · HTML5/CSS3/JavaScript · Chart.js · PostgreSQL (produção) · SQLite (desenvolvimento e testes) · pytest · pytest-cov · Gunicorn · Render.

## Como executar localmente

Pré-requisito: Python 3.12 ou superior (testado também com 3.13).

```bash
# 1. Ambiente virtual e dependências
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux / macOS
pip install -r requirements-dev.txt

# 2. Configuração (opcional em desenvolvimento)
copy .env.example .env          # Windows  (cp no Linux/macOS)

# 3. Banco de dados (cria instance/aceito.db com as migrações)
flask --app run db upgrade

# 4. (Opcional) Conta de demonstração com os dados da persona Juliana & Rafael
flask --app run popular-exemplo
#    e-mail: exemplo@aceito.app   senha: aceito2026

# 5. Servidor de desenvolvimento
flask --app run run
```

Acesse <http://127.0.0.1:5000>.

## Testes

```bash
pytest                                        # 154 testes (unitários e de integração)
pytest --cov=app/services --cov-report=term   # cobertura da camada de regras de negócio
```

Resultado atual: **154 testes passando**, cobertura de **97% em `app/services`** (mínimo exigido: 80%, RNF11). Relatórios em [`docs/situacao-2-desenvolvimento/testes/`](docs/situacao-2-desenvolvimento/testes/).

## Publicação (Render + Neon/Supabase)

1. Crie um banco PostgreSQL gratuito no [Neon](https://neon.tech) ou no [Supabase](https://supabase.com) e copie a *connection string* (`postgresql://...?sslmode=require`).
2. No [Render](https://render.com), crie um **Blueprint** apontando para este repositório; o arquivo [`render.yaml`](render.yaml) já define o serviço.
3. Informe a variável `DATABASE_URL` com a connection string do passo 1. `SECRET_KEY` é gerada pelo próprio Render.
4. A cada deploy o Render executa `flask db upgrade` (migrações) e sobe o Gunicorn. O HTTPS é fornecido pelo Render.

Variáveis de ambiente:

| Variável | Uso |
|---|---|
| `APP_ENV` | `development` (padrão) ou `production` |
| `SECRET_KEY` | assina sessão e tokens CSRF — obrigatória em produção |
| `DATABASE_URL` | PostgreSQL em produção; vazio = SQLite local |

## Estrutura

```
app/
├── __init__.py        create_app(): configura extensões, blueprints e erros
├── models/            MODEL — 7 classes SQLAlchemy (uma por tabela)
├── controllers/       CONTROLLER — blueprints (auth, painel, casamento, categorias,
│                      fornecedores, despesas, parcelas, convidados)
├── services/          REGRAS DE NEGÓCIO — parcelamento, orçamento, convidados, painel…
├── forms/             Flask-WTF (validação e CSRF)
├── templates/         VIEW — Jinja2
└── static/            css/, js/, img/
migrations/            Flask-Migrate (Alembic)
tests/unit/            regras de negócio isoladas (TU01–TU13 e mais)
tests/integration/     HTTP + banco (TI01–TI07, isolamento, segurança, desempenho)
docs/                  documentação das três situações da disciplina
```
