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
| D16 | Cor amarela (#B26A00) em texto | Usada em barras, ícones e bordas; o texto dos selos usa um tom mais escuro (#7A4A00, ver seção 6). | #B26A00 sobre fundo claro tem contraste 4,2:1, abaixo do mínimo AA de 4,5:1 (RNF03). |
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

## 6. Identidade visual: evolução da seção 15

A primeira versão seguia a seção 15 ao pé da letra (verde-sálvia #5E7D63, fundo #FAF8F5, texto #2B2B2B, fonte Inter).
Funcionava, mas tinha cara de painel administrativo genérico: nada dizia "casamento". A revisão mantém o verde como
cor principal e as cores de situação, e dá ao app uma identidade de **papelaria de casamento**, inspirada no convite
impresso: papel bom, tinta escura e um único acento.

### Paleta

| Papel | Antes (seção 15) | Agora | Motivo |
|---|---|---|---|
| Cor principal (botões, links, foco) | Sálvia #5E7D63 | Eucalipto #4F6B55 | O mesmo verde, mais escuro. Com texto branco o contraste sobe de 4,6:1 (no limite do AA) para 5,9:1. O sálvia #5E7D63 continua em ícones e preenchimentos. |
| Fundo da página | #FAF8F5 (creme) | Névoa #F3F5F1 | Papel frio, levemente esverdeado, que combina com o eucalipto. O creme com serifa é o visual mais repetido em sites de casamento. |
| Texto | #2B2B2B | Tinta #263027 | Tinta verde-escura, coerente com a cor principal (contraste de 12,5:1 sobre o fundo). |
| Fios e bordas | #E7E2DA | Linho #DCE1D8 | Separam o conteúdo como num impresso. Os campos de formulário usam #8A958C (3,1:1, WCAG 1.4.11). |
| Acento | — | Malva #8A5A72 | Tom de flor seca. Usado **só** na contagem regressiva, no "!" da marca, no fio do convite e no código das páginas de erro. |
| Situações | #2E7D32 / #B26A00 / #C62828 | #2E7D32 / #B26A00 / #B3261E | Os mesmos tons nas barras e nos botões. O texto dos selos usa versões mais escuras (#276C2B, #7A4A00, #A3221B) para passar AA sobre o fundo claro de cada selo. |

Todos os pares de texto e fundo foram conferidos pela fórmula de contraste da WCAG 2.1. O menor contraste de
texto é 4,77:1 (texto apagado sobre o fundo) e o dos fios de foco e controles é ≥ 3:1.

### Tipografia

- **Marcellus** (serifa de inspiração lapidar, que lembra a gravação de um convite), só em títulos `h1`, na marca, na
  contagem regressiva, no dia das próximas parcelas e no código das páginas de erro.
- **Hanken Grotesk** no lugar da Inter para todo o resto. Foi escolhida porque os algarismos já vêm com largura fixa
  (tabulares), o que deixa as colunas de valores em R$ alinhadas. Outras candidatas (como Albert Sans) têm algarismos
  proporcionais e não oferecem a variante tabular.
- Os cabeçalhos de tabela deixaram de usar caixa alta: rótulos em caixa normal são mais fáceis de ler.

### Componentes e acessibilidade

- **Convite do painel:** nomes do casal, data, local e contagem regressiva dentro de um fio duplo. O fio duplo aparece
  só onde está "o evento": o convite do painel, o painel lateral de entrar/criar conta e as páginas de erro.
- **Extrato:** os números principais (painel, orçamento, convidados) ficam numa folha só, dividida por fios, em vez de
  cartões soltos e iguais.
- **Selos de situação:** o texto continua escrito no selo ("Paga", "Atrasada", "Acima do planejado"…), e cada tom ganha
  uma forma própria: ✓ ok, triângulo atenção, "!" crítico, anel neutro, traço descartado. A situação não depende só da cor.
- **Gráfico:** o planejado é uma barra vazada com contorno (3,7:1) e o contratado uma barra cheia. As séries se
  distinguem pela forma, e a tabela acessível com os mesmos dados continua no painel.
- **Foco:** contorno de 2 px em eucalipto (`outline`, não `box-shadow`, para aparecer no modo de alto contraste do Windows).
- **Sem JavaScript:** o menu do celular só recolhe quando a página marca `<html class="js">`. Sem JavaScript, ele aparece
  aberto, empilhado abaixo da marca. Formulários, o botão Pagar (link para a tela de pagamento) e os filtros (botão
  Filtrar em `<noscript>`) funcionam normalmente.
- **Movimento:** as animações (mensagens e janela de diálogo) só rodam com `prefers-reduced-motion: no-preference`.
