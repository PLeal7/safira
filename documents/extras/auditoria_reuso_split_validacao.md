# Auditoria de reuso do split e da validação cruzada (card #239)

Registro da conferência pedida pelo card #240 (referência técnica): as quatro duplas de
modelagem reusam `split.dividir` e `validacao.criar_folds`/`criar_folds_validacao_por_cliente`,
em vez de reimplementar partição ou validação cruzada próprias.

## O que foi conferido

Para cada um dos quatro pipelines em `develop`, dois pontos: (a) o módulo referencia
`validacao.criar_folds` na própria documentação/uso, e (b) existe um teste automatizado que
falha se o módulo importar `train_test_split`, `KFold` avulso ou qualquer particionador que não
seja o do contrato.

| Candidato | Módulo | Referencia `validacao.criar_folds` | Teste-guarda contra partição própria |
|---|---|---|---|
| Regressão Logística | `src/pipeline_logistica.py` | Sim | `test_pipeline_logistica.py::test_pipeline_nao_importa_selecao_de_modelo` (e equivalentes) |
| Árvore de Decisão | `src/pipeline_arvore.py` | Sim | `test_pipeline_arvore.py::test_pipeline_nao_importa_selecao_de_modelo` |
| Random Forest | `src/busca_random_forest.py` | Sim — recusa `cv` inteiro explicitamente | `test_busca_random_forest.py::test_card_nao_cria_particao_nem_cv_inteiro` |
| Gradient Boosting | `src/busca_gradient_boosting.py` | Sim — recusa `cv` inteiro explicitamente | `test_busca_gradient_boosting.py::test_card_nao_cria_particao_nem_cv_inteiro` |

Nenhum dos quatro módulos foi encontrado reimplementando partição ou validação cruzada própria.
Random Forest e Gradient Boosting, além de referenciar `criar_folds`, ativamente **recusam**
`cv` passado como inteiro — a salvaguarda mais forte, porque um inteiro faria o
`GridSearchCV`/`RandomizedSearchCV` do scikit-learn converter sozinho para um particionador
estratificado que ignora o agrupamento por Cliente, o próprio vazamento que este card existe
para prevenir.

## Como foi conferido

`grep` nos quatro módulos por `criar_folds`, `KFold`, `train_test_split` e `cv=`, seguido da
leitura dos testes correspondentes para confirmar que a garantia é automatizada (roda a cada
`pytest`), não apenas descrita em docstring. Comando reprodutível, a partir da raiz do
repositório:

```
grep -n "criar_folds\|KFold\|train_test_split\|cv=" src/pipeline_logistica.py src/pipeline_arvore.py src/busca_random_forest.py src/busca_gradient_boosting.py
```

## Conclusão

O reuso exigido pelo card #240 está confirmado nas quatro duplas, com salvaguarda automatizada
em teste, não apenas em convenção. Nenhuma ação corretiva foi necessária.
