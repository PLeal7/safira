# Busca de hiperparametros da Arvore de Decisao (card #231/#232)

> **DESATUALIZADO (fix/#232):** os numeros abaixo foram gerados com `scoring='average_precision'`. O card #231 foi corrigido para `scoring=scorer_f2` (protocolo #238/#242), o mesmo criterio das outras tres duplas — esta tabela precisa ser regenerada rodando a celula do GridSearchCV de novo antes do card #232 fechar. `max_depth=4` pode deixar de ser o vencedor com F2 em vez de Precisao Media.

48 combinacoes, GridSearchCV com validacao cruzada agrupada por Cliente (5 folds), scoring=average_precision (Precisao Media) — **valor antigo, ver aviso acima**. Tempo real da busca: 1048s (~17,5min).

## Top 10 combinacoes

| Rank | class_weight | criterion | max_depth | min_samples_leaf | Precisao Media | desvio |
|---|---|---|---|---|---|---|
| 1 | balanced | gini | 6 | 200 | 0.4585 | 0.0042 |
| 2 | balanced | gini | 6 | 50 | 0.4585 | 0.0037 |
| 3 | balanced | gini | 6 | 100 | 0.4582 | 0.0041 |
| 4 | balanced | entropy | 6 | 100 | 0.4573 | 0.0039 |
| 5 | balanced | entropy | 6 | 200 | 0.4571 | 0.0042 |
| 6 | balanced | entropy | 6 | 50 | 0.4570 | 0.0035 |
| 7 | nan | entropy | 6 | 100 | 0.4563 | 0.0052 |
| 8 | nan | entropy | 6 | 50 | 0.4558 | 0.0048 |
| 9 | nan | entropy | 6 | 200 | 0.4556 | 0.0054 |
| 10 | nan | gini | 6 | 100 | 0.4505 | 0.0047 |

## Melhor Precisao Media por profundidade

| max_depth | melhor Precisao Media |
|---|---|
| 3 | 0.4002 |
| 4 | 0.4220 |
| 5 | 0.4392 |
| 6 | 0.4585 |

## Decisao final

Modelo final usa **max_depth=4** (Precisao Media 0,4220, 16 folhas), nao o vencedor puro por metrica (max_depth=6, Precisao Media 0,4585, 60 folhas). Com profundidade 6 a arvore deixa de ser legivel como explicabilidade intrinseca do ART.7 — 60 folhas nao e um numero de regras que a operacao consegue ler. Com profundidade 3 a Precisao Media (0,4002) fica sem folga sobre a meta de negocio de 0,40. Profundidade 4 equilibra as duas exigencias: folga confortavel sobre a meta e arvore ainda legivel.
