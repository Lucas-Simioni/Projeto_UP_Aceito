# Arquitetura e decisões de implementação

Este documento descreve como o planejamento (situação 1) virou código e registra as decisões tomadas onde o documento de planejamento era ambíguo ou silencioso.

## 1. Camadas (MVC + serviços)

```
Navegador ──► Controller (Blueprint) ──► Formulário (Flask-WTF: tipos, obrigatórios, CSRF)
                    │
                    ├──► Serviço (regras RN01–RN17, transações) ──► Models (SQLAlchemy) ──► Banco
                    │
                    └──► Template Jinja2 (só apresentação) ──► HTML
```

| Camada | Pasta | Responsabilidade |
|---|---|---|
| Model | `app/models/` | Tabelas, relacionamentos, restrições (CHECK, UNIQUE, FK) e métodos do diagrama de classes (`gerar_parcelas`, `situacao`, `pagar`, `estornar`, `total_pessoas`…). |
| Serviços | `app/services/` | Toda regra de negócio. `parcelamento.py`, `orcamento.py` e as funções de regra de `convidados.py` são **puras** (não acessam o banco); os demais módulos executam as operações com transação. |
| Controller | `app/controllers/` | Lê a requisição, valida o formulário, chama o serviço, escolhe template e mensagem. Nenhuma regra de negócio. |
| Formulários | `app/forms/` | Conversão de tipos (inclusive `R$ 1.234,56` → `Decimal`), campos obrigatórios e CSRF. |
| View | `app/templates/`, `app/static/` | HTML, CSS e JavaScript. O JavaScript é só melhoria progressiva: sem ele as telas continuam funcionando. |

### Módulos de serviço

| Módulo | Conteúdo | Regras |
|---|---|---|
| `parcelamento.py` | divisão de valores, vencimentos, situação da parcela, filtros | RN07–RN11 |
| `orcamento.py` | situação da categoria, alertas, validações de valores e datas | RN02–RN06, RN12, RN13 |
| `convidados.py` | pessoas confirmadas, custo por convidado, resumo, cadastro e RSVP | RN15, RN16 |
| `contas.py` | senha forte, e-mail único, autenticação | RN17 |
| `casamentos.py` | um casamento por conta e categorias padrão | RN01, RF04 |
| `categorias.py` / `fornecedores.py` / `despesas.py` | operações de cadastro, pagamento e estorno | RN12–RN14 |
| `painel.py` | monta os números do painel a partir do banco | RF11 |
| `exportacao.py` | CSV de convidados e parcelas | RF14 |
| `dinheiro.py`, `datas.py`, `mensagens.py`, `erros.py` | Decimal/formatação BR, fuso horário, mensagens E/A/S/C, exceção de regra | RNF02 |

O documento previa três arquivos em `services/`; a camada foi dividida em mais módulos para que cada um tenha uma única responsabilidade. Os três previstos existem com o conteúdo esperado.

## 2. Banco de dados

O esquema é o do [`schema.sql`](situacao-1-planejamento/banco/schema.sql): 7 tabelas, mesmos tipos, CHECK, UNIQUE, índices e regras ON DELETE. Ele é gerado pelos models e versionado em `migrations/` (Flask-Migrate). A 3ª forma normal foi mantida: totais, saldo, situação de parcela/categoria, número de parcelas e custo por convidado **são calculados, nunca gravados**.

No SQLite (desenvolvimento e testes), `PRAGMA foreign_keys=ON` é ligado em cada conexão para que CASCADE, RESTRICT e SET NULL funcionem como no PostgreSQL.

## 3. Segurança

| Requisito | Implementação |
|---|---|
| RNF06 | `werkzeug.security.generate_password_hash` (scrypt). |
| RNF07 | `CSRFProtect` em todas as requisições POST; consultas pelo ORM, sem SQL montado com texto do usuário. |
| RNF08 | Toda busca por id passa por `obter_*()` em `controllers/comum.py`, que filtra pelo casamento do usuário logado; o que não é dele responde 404. A camada de serviços confere de novo categoria e fornecedor recebidos em formulários. |
| Sessão | Cookies `HttpOnly`, `SameSite=Lax` e `Secure` em produção; sessão renovada no login. |
| Redirecionamento | `?proximo=`/`?next=` só aceita caminhos internos (evita *open redirect*). |
| CSV | Células que começam com `=`, `+`, `-` ou `@` recebem `'` na frente (evita injeção de fórmulas no Excel). |
| Configuração | `SECRET_KEY` e `DATABASE_URL` vêm de variáveis de ambiente; a aplicação se recusa a subir em produção sem elas. |

## 4. Decisões sobre pontos ambíguos do planejamento

| # | Ponto | Decisão | Motivo |
|---|---|---|---|
| D1 | RN02 — “posterior à data do cadastro” | Compara com a data de criação da conta (`usuario.criado_em`), também ao editar. | Segue a regra ao pé da letra; no primeiro acesso equivale a “data futura” (E05). |
| D2 | RN10 — parcela que vence **hoje** | “Vence em breve” (ainda não passou). Atrasada = vencimento anterior a hoje. | “Já passou” só é verdade a partir do dia seguinte. |
| D3 | RF10 — filtro “pendentes” | Todas as parcelas **em aberto** (inclui as atrasadas). | É o uso esperado do filtro; o selo de situação continua seguindo a RN10. |
| D4 | RN14 — o que pode mudar numa despesa com parcela paga | Só descrição, categoria e fornecedor. Valor, nº de parcelas, 1º vencimento e data de contratação exigem estorno (E11). | Mudar a data de contratação poderia invalidar pagamentos já registrados (RN11). |
| D5 | RF08 — quando regerar parcelas | Quando muda valor, número de parcelas ou primeiro vencimento, e nenhuma está paga. | Os três determinam as parcelas (RN07/RN08). |
| D6 | RN07 — valor menor que R$ 0,01 por parcela | Recusado com mensagem própria. | Geraria parcela de R$ 0,00, proibida pelo CHECK `valor > 0`. |
| D7 | RN13 — trocar a categoria de um fornecedor que já tem despesas | Bloqueado. | Deixaria despesas com categoria diferente da do fornecedor. |
| D8 | RN12 — editar despesa cujo fornecedor foi descartado depois | Permitido manter o vínculo; só não aceita *novas* despesas. | A regra fala em “novas despesas”. |
| D9 | RF06 — fornecedores descartados na comparação | Aparecem no fim, esmaecidos, e não concorrem ao “menor valor”. | Um orçamento descartado não é uma opção real. |
| D10 | Saldo / “Ainda posso gastar” | Orçamento total − total contratado. | Coerente com RN06 e com `Casamento.saldo()` do diagrama. |
| D11 | RN09 — parcelas já pagas após o casamento | Continuam contando no aviso A03, como diz a regra. | Fidelidade ao texto da RN09. |
| D12 | Situação da despesa (além de “Quitada”) | “Em dia” ou “Com parcela atrasada”. | O documento só define “Quitada”; a lista T09 pede uma situação para todas. |
| D13 | Situação de categoria com planejado e contratado zerados | “Dentro do planejado”. | Não há gasto acima de nada. |
| D14 | Fuso horário | “Hoje” é calculado em America/Sao_Paulo. | O servidor do Render roda em UTC; à noite as datas mudariam de dia. |
| D15 | CSV | Separador `;`, vírgula decimal e BOM UTF-8. | Abre corretamente no Excel em português. |
| D16 | Cor amarela (#B26A00) em texto | Usada em barras, ícones e bordas; o texto dos selos usa um tom mais escuro (#8A5300). | #B26A00 sobre fundo claro tem contraste 4,2:1, abaixo do mínimo AA de 4,5:1 (RNF03). |
| D17 | Validação de nome de categoria duplicado | Comparação sem diferenciar maiúsculas/minúsculas. | Evita “Buffet” e “buffet” como categorias diferentes. |

## 5. Rastreabilidade (requisito → código → teste)

| Requisito | Onde | Testes |
|---|---|---|
| RF01–RF02 | `controllers/auth.py`, `services/contas.py` | `test_auth_seguranca.py`, TI01 |
| RF03 | `controllers/casamento.py`, `services/casamentos.py` | TI01, `test_rn01_*`, `test_rn02_rn03_*` |
| RF04 | `services/categorias.py`, `services/casamentos.py` | TI01, TI04, `test_crud_de_categoria` |
| RF05–RF06 | `services/fornecedores.py` | `test_crud_de_fornecedor`, `test_rf06_*` |
| RF07–RF08 | `services/despesas.py`, `services/parcelamento.py` | TU01–TU04, TI02, `test_rf08_*`, `test_rn14_*` |
| RF09–RF10 | `services/despesas.py`, `controllers/parcelas.py` | TU05, TU10, TI05, `test_rf10_*` |
| RF11 | `services/painel.py`, `templates/painel/` | `test_rf11_*`, `test_painel_vazio_*` |
| RF12–RF13 | `services/convidados.py` | TU11, TU12, `test_crud_e_rsvp_*`, `test_rf13_*` |
| RF14 | `services/exportacao.py` | TI07, `test_rf10_filtros_e_csv_*` |
| RF15 | `templates/_macros.html` (`botao_excluir`), `static/js/app.js` | inspeção manual (janela de confirmação C01) |
| RNF08 | `controllers/comum.py` | TI03, `test_rnf08_*` (14 casos) |
| RNF09 | consultas com carregamento antecipado (`selectinload`) | `test_rnf09_*` (500 convidados, 200 parcelas) |
