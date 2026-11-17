# Dicionário de dados — Aceito!

“Obrig.” = o campo não aceita valor vazio (NOT NULL). Valores monetários são `NUMERIC(12,2)` (duas casas decimais, RN03).

## usuario — contas de acesso

| Campo | Tipo | Obrig. | Chave | Descrição e domínio |
|---|---|---|---|---|
| id | SERIAL | Sim | PK | Identificador gerado automaticamente. |
| nome | VARCHAR(100) | Sim | | Nome de quem usa a conta. |
| email | VARCHAR(120) | Sim | Único | E-mail de login, formato válido, gravado em minúsculas (RN17). |
| senha_hash | VARCHAR(255) | Sim | | Hash da senha; a senha original nunca é gravada (RNF06). |
| criado_em | TIMESTAMP | Sim | | Data e hora do cadastro; padrão = agora. |

## casamento — dados gerais do evento

| Campo | Tipo | Obrig. | Chave | Descrição e domínio |
|---|---|---|---|---|
| id | SERIAL | Sim | PK | Identificador. |
| usuario_id | INTEGER | Sim | FK → usuario, Único | Dono do casamento; único garante 1 casamento por conta (RN01). |
| nome_casal | VARCHAR(120) | Sim | | Ex.: “Juliana & Rafael”. |
| data_casamento | DATE | Sim | | Posterior à data do cadastro (RN02). |
| local | VARCHAR(150) | Não | | Local da cerimônia ou festa. |
| orcamento_total | NUMERIC(12,2) | Sim | | Maior que 0 (RN03). |
| convidados_estimados | INTEGER | Não | | Maior ou igual a 0; usado só como referência. |

## categoria — divisão do orçamento

| Campo | Tipo | Obrig. | Chave | Descrição e domínio |
|---|---|---|---|---|
| id | SERIAL | Sim | PK | Identificador. |
| casamento_id | INTEGER | Sim | FK → casamento | Casamento ao qual a categoria pertence. |
| nome | VARCHAR(60) | Sim | Único por casamento | Ex.: Buffet, Fotografia e vídeo. |
| valor_planejado | NUMERIC(12,2) | Sim | | Maior ou igual a 0; padrão 0. |

## fornecedor — empresas e profissionais orçados

| Campo | Tipo | Obrig. | Chave | Descrição e domínio |
|---|---|---|---|---|
| id | SERIAL | Sim | PK | Identificador. |
| categoria_id | INTEGER | Sim | FK → categoria (RESTRICT) | Categoria do serviço oferecido. |
| nome | VARCHAR(120) | Sim | | Nome do fornecedor. |
| telefone | VARCHAR(20) | Não | | Formato (99) 99999-9999. |
| email | VARCHAR(120) | Não | | Formato de e-mail válido. |
| valor_orcado | NUMERIC(12,2) | Não | | Valor do orçamento recebido; maior ou igual a 0. |
| status | VARCHAR(12) | Sim | | ORCAMENTO, CONTRATADO ou DESCARTADO; padrão ORCAMENTO (RN12). |
| observacoes | TEXT | Não | | Anotações livres (condições, o que inclui). |

## despesa — contratos e compras

| Campo | Tipo | Obrig. | Chave | Descrição e domínio |
|---|---|---|---|---|
| id | SERIAL | Sim | PK | Identificador. |
| categoria_id | INTEGER | Sim | FK → categoria (RESTRICT) | Categoria do gasto; igual à do fornecedor, se houver (RN13). |
| fornecedor_id | INTEGER | Não | FK → fornecedor (SET NULL) | Fornecedor contratado; vazio para compras avulsas. |
| descricao | VARCHAR(150) | Sim | | Ex.: “Buffet completo para 150 pessoas”. |
| valor_total | NUMERIC(12,2) | Sim | | Valor do contrato; maior que 0 (RN03). |
| data_contratacao | DATE | Sim | | Data em que a despesa foi contratada. |

## parcela — pagamentos de cada despesa

| Campo | Tipo | Obrig. | Chave | Descrição e domínio |
|---|---|---|---|---|
| id | SERIAL | Sim | PK | Identificador. |
| despesa_id | INTEGER | Sim | FK → despesa (CASCADE) | Despesa à qual a parcela pertence. |
| numero | SMALLINT | Sim | Único por despesa | De 1 a 24 (RN08). |
| valor | NUMERIC(12,2) | Sim | | Maior que 0; calculado pela RN07. |
| data_vencimento | DATE | Sim | | Vencimento mensal (RN08). |
| data_pagamento | DATE | Não | | Vazio = não paga; não pode ser futura nem anterior à contratação (RN11). |

## convidado — lista de convidados

| Campo | Tipo | Obrig. | Chave | Descrição e domínio |
|---|---|---|---|---|
| id | SERIAL | Sim | PK | Identificador. |
| casamento_id | INTEGER | Sim | FK → casamento (CASCADE) | Casamento ao qual o convidado pertence. |
| nome | VARCHAR(120) | Sim | | Nome do convidado. |
| telefone | VARCHAR(20) | Não | | Formato (99) 99999-9999. |
| email | VARCHAR(120) | Não | | Formato de e-mail válido. |
| grupo | VARCHAR(15) | Sim | | FAMILIA_NOIVA, FAMILIA_NOIVO, AMIGOS, TRABALHO ou OUTROS; padrão OUTROS. |
| acompanhantes | SMALLINT | Sim | | De 0 a 10; padrão 0 (RN16). |
| status_rsvp | VARCHAR(10) | Sim | | PENDENTE, CONFIRMADO ou RECUSADO; padrão PENDENTE. |

## Dados calculados (não gravados — 3ª forma normal)

| Informação | Como é calculada |
|---|---|
| Total contratado da categoria | Soma de `despesa.valor_total` da categoria. |
| Total pago | Soma de `parcela.valor` com `data_pagamento` preenchida. |
| Saldo (“Ainda posso gastar”) | `orcamento_total` − total contratado. |
| Situação da categoria | RN05 (contratado ÷ planejado). |
| Situação da parcela | RN10 (`data_pagamento`, `data_vencimento` e a data de hoje). |
| Número de parcelas da despesa | Contagem das parcelas. |
| Pessoas confirmadas / custo por convidado | RN15. |
