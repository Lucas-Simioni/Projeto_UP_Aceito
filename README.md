# Aceito!

Sistema web para o casal organizar o **orçamento, os fornecedores, as despesas parceladas e a lista de convidados** do casamento num só lugar. O painel mostra a qualquer momento quanto foi planejado, contratado e pago, o que vence nos próximos dias e quantas pessoas confirmaram presença.

> Projeto Integrador Transdisciplinar em Engenharia de Software II · Lucas Batista Simioni
> Documento de planejamento: [`documento-de-planejamento.pdf`](docs/situacao-1-planejamento/documento-de-planejamento.pdf)

| | |
|---|---|
| Sistema publicado | https://aceito-ym5f.onrender.com |
| Vídeo de apresentação | [`docs/situacao-2-desenvolvimento/video-1.md`](docs/situacao-2-desenvolvimento/video-1.md) |
| Vídeo das correções | [`docs/situacao-3-validacao/video-2.md`](docs/situacao-3-validacao/video-2.md) |
| Laudo de qualidade | [`docs/situacao-3-validacao/laudo-de-qualidade.md`](docs/situacao-3-validacao/laudo-de-qualidade.md) |
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
pytest                                        # 180 testes (unitários e de integração)
pytest --cov=app/services --cov-report=term   # cobertura da camada de regras de negócio
```

Resultado atual: **180 testes passando**, cobertura de **98% em `app/services`** (mínimo exigido: 80%, RNF11). Relatórios em [`docs/situacao-2-desenvolvimento/testes/`](docs/situacao-2-desenvolvimento/testes/).

## Publicação (Render + Neon/Supabase)

1. Crie um banco PostgreSQL gratuito no [Neon](https://neon.tech) ou no [Supabase](https://supabase.com) e copie a *connection string* (`postgresql://...?sslmode=require`).
2. No [Render](https://render.com), crie um **Blueprint** apontando para este repositório; o arquivo [`render.yaml`](render.yaml) já define o serviço.
3. Informe a variável `DATABASE_URL` com a connection string do passo 1. `SECRET_KEY` é gerada pelo próprio Render.
4. A cada deploy o Render executa `flask db upgrade` (migrações) e sobe o Gunicorn. O HTTPS é fornecido pelo Render.

### Credenciais e variáveis de ambiente

As credenciais nunca ficam no código. A aplicação lê tudo de variáveis de ambiente ([`config.py`](config.py)):

- **No computador:** num arquivo `.env` na raiz do projeto, criado a partir do modelo [`.env.example`](.env.example). O `.gitignore` impede que qualquer `.env` vá para o GitHub; só o modelo, sem valores, é versionado.
- **No Render:** no painel do serviço (*Environment*). Uma variável definida no sistema tem prioridade sobre o `.env`.

| Variável | Uso |
|---|---|
| `APP_ENV` | `development` (padrão) ou `production` |
| `SECRET_KEY` | assina sessão e tokens CSRF; em produção é obrigatória, com pelo menos 32 caracteres |
| `DATABASE_URL` | PostgreSQL (Neon/Supabase); em branco no desenvolvimento = SQLite local |

Em produção a aplicação **não sobe** sem `SECRET_KEY` forte e sem `DATABASE_URL`, para nunca rodar com a chave de desenvolvimento.

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
