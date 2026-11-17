# Relatórios de testes

| Arquivo | Conteúdo |
|---|---|
| `relatorio-pytest.txt` | Saída do `pytest -v` com a tabela de cobertura por arquivo. |
| `resultado-pytest.xml` | Resultado em formato JUnit (lido por ferramentas de CI). |
| `cobertura-html/index.html` | Relatório de cobertura navegável (abra no navegador). |

## Resultado (17/11/2026)

- **168 testes, todos passando** (unitários e de integração), incluindo os das correções da validação simulada (`tests/integration/test_validacao_usuarios.py`, ver `docs/situacao-3-validacao/laudo-de-qualidade.md`).
- Cobertura da camada de serviços (`app/services`): **98%** — meta do RNF11: 80%.
- Cobertura da aplicação inteira (`app`): 97%.

## Como gerar de novo

```bash
pytest -v --cov=app --cov-report=term-missing \
       --cov-report=html:docs/situacao-2-desenvolvimento/testes/cobertura-html \
       --junitxml=docs/situacao-2-desenvolvimento/testes/resultado-pytest.xml
pytest --cov=app/services --cov-report=term      # critério do RNF11
```

## Mapa dos testes do plano (seção 16)

| ID | Arquivo / teste |
|---|---|
| TU01–TU05, TU09, TU10 | `tests/unit/test_parcelamento.py` |
| TU06–TU08 | `tests/unit/test_orcamento.py` |
| TU11–TU13 | `tests/unit/test_convidados_contas.py` |
| TI01–TI07 | `tests/integration/test_cenarios_ti.py` |
| RNF06–RNF08 (segurança e isolamento) | `tests/integration/test_auth_seguranca.py` |
| RNF09 (500 convidados, 200 parcelas, < 2 s) | `tests/integration/test_desempenho_comandos.py` |
| Q01–Q04 (laudo de qualidade, rodada 0) | `tests/integration/test_validacao_usuarios.py` |
