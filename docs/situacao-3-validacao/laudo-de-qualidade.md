# Laudo de qualidade

## Rodada 0 — validação simulada antes da publicação (17/11/2026)

> **Atenção:** esta rodada **não substitui o teste com pessoas reais**. Ela foi feita com cinco perfis de testador simulados por script, que executaram o roteiro de [formulario-de-teste.md](formulario-de-teste.md) contra a aplicação completa (rotas, formulários, telas e banco), mais capturas de tela em 390 px de largura (celular). O objetivo foi chegar à rodada com usuários reais sem defeitos óbvios. Os resultados dos testadores reais entram nas rodadas seguintes, no mesmo formato.

### Perfis simulados

| Testador | Perfil | O que fez |
|---|---|---|
| T1 – Ana | Segue o roteiro ao pé da letra, no notebook | As 7 tarefas; conferiu os números do painel. |
| T2 – Bruno | Usa o celular, digita valores de jeitos diferentes | `50000`, `R$ 50.000`, `50.000`, `50000,5`, `50 mil`; e-mail com maiúsculas e espaços; telefone só com números; campos apagados. |
| T3 – Carla | Tenta quebrar o sistema | Campos vazios, datas passadas, valores zero e negativos, 25 parcelas, 11 acompanhantes, fornecedor descartado, pagamento futuro e em duplicidade, excluir despesa paga e categoria em uso, acessar dados de outra conta. |
| T4 – Diego | Navega só pelo teclado / leitor de tela | Verificou em 17 telas: idioma da página, um único título `h1`, rótulo em todos os campos, nome acessível nos botões de ícone, hierarquia de títulos. |
| T5 – Elisa | Confere se os números batem entre as telas | Comparou painel, orçamento, despesas, parcelas, convidados e os dois CSVs; trocou fornecedor de categoria; antecipou a data do casamento. |

### Resultado geral

- Tarefas do roteiro: **7 de 7 concluídas** por todos os perfis.
- Os totais (contratado, pago, saldo, pessoas confirmadas, custo por convidado, contagem de parcelas por filtro) **coincidiram em todas as telas e nos CSVs**.
- Todas as regras testadas pela Carla foram barradas com a mensagem padronizada correta (E01–E13). O acesso a dados de outra conta retornou 404 (RNF08).
- Nenhum problema de acessibilidade encontrado pelas verificações do Diego.

### Problemas encontrados

| ID | Descrição | Quem relatou | Gravidade | Decisão | Correção feita | Evidência |
|---|---|---|---|---|---|---|
| Q01 | Mensagem de exclusão sem concordância: “Despesa “Flores” excluído.”, “Categoria Lua de mel excluído.” | T5 – Elisa | Baixa | Corrigir | `mensagem_exclusao()` aplica o feminino à S04 em despesas e categorias. | `test_q01_*` |
| Q02 | Apagar o número de acompanhantes ou de parcelas mostrava “O valor inteiro não é válido.”, texto técnico e diferente do padrão E01. | T2 – Bruno | Média | Corrigir | Novo campo `InteiroField`: acompanhantes em branco valem 0 (padrão do dicionário de dados); parcelas em branco mostram “Preencha este campo.”; número com vírgula mostra “Informe um número inteiro, sem vírgula.”. | `test_q02_*` |
| Q03 | Telefone digitado ou colado só com números (`11988887777`) era recusado quando a máscara do navegador não atuava. | T2 – Bruno | Média | Corrigir | O servidor padroniza 10 ou 11 dígitos (com ou sem +55) para `(99) 99999-9999`. | `test_q03_*` |
| Q04 | Campo de valor preenchia pelos centavos: quem digitava `4000` via `40,00` e podia gravar um valor 100 vezes menor. | T2 – Bruno | Alta | Corrigir | Digitação livre (`4000`, `4.000`, `4000,5`); ao sair do campo o valor aparece como `4.000,00`, pela mesma regra do servidor. O total da prévia de parcelas vem do servidor. | `test_q04_*`, `test_interpretar_moeda` |
| Q05 | No celular, o seletor Pendente / Confirmado / Recusado vazava para fora do cartão do convidado e cortava “Recusado”; o “(+2)” de acompanhantes ficava separado do número. | T2 – Bruno | Média | Corrigir | Confirmação ocupa uma linha inteira do cartão, com os três botões do mesmo tamanho; número e acompanhantes ficam juntos. | [evidencias/q05-convidados-celular-depois.png](evidencias/q05-convidados-celular-depois.png) |

### Observações que não viraram correção

| Observação | Motivo |
|---|---|
| Categoria com planejado R$ 0,00 e despesa aparece como “Acima do planejado”. | Comportamento definido no documento (RN05 / TU07). |
| “1 parcela(s) vencem depois da data do casamento.” | Texto exato da mensagem A03 do documento (seção 15). |
| No celular, o filtro “Todas” das parcelas começa pelas já pagas, e a lista fica longa. | Ordem por vencimento exigida pelo RF10; os filtros Pendentes e Próximos 30 dias resolvem o caso. Fica como sugestão para os testadores reais avaliarem. |
