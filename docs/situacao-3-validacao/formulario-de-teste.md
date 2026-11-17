# Roteiro e formulário de teste com usuários

Cada testador recebe o link do sistema publicado, executa o roteiro **sem ajuda** e depois preenche o formulário (Google Forms) com os campos abaixo.

## Roteiro de tarefas

1. Criar uma conta e configurar um casamento com orçamento de R$ 50.000,00.
2. Definir o valor planejado de três categorias.
3. Cadastrar dois fornecedores de Fotografia e vídeo e comparar os orçamentos.
4. Registrar uma despesa de R$ 4.000,00 em 4x com um desses fornecedores.
5. Marcar a primeira parcela como paga e depois estornar o pagamento.
6. Cadastrar cinco convidados, confirmar três e recusar um.
7. Voltar ao painel e conferir se os números fazem sentido.

## Campos do formulário

| Campo | Tipo de resposta |
|---|---|
| Nome de quem testou | Texto curto |
| Data do teste | Data |
| Dispositivo e navegador usados | Texto curto |
| O que testou e funcionou | Caixas de seleção com as 7 tarefas + texto livre |
| O que testou e não funcionou – o que deve ser corrigido | Texto longo |
| Funcionalidade não testada (faltou ou não foi implementada) e por quê | Texto longo |
| Sugestões de melhoria | Texto longo |
| Facilidade de uso (1 = muito difícil, 5 = muito fácil) | Escala de 1 a 5 |
| Print da tela com erro | Upload de arquivo (opcional) |

Cada problema relatado vira uma linha no laudo de qualidade (`laudo-de-qualidade.md`): ID, descrição, quem relatou, gravidade (alta, média, baixa), decisão (corrigir ou não, com justificativa), correção feita e evidência (print antes e depois, em `evidencias/`).
