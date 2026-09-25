# Matrizes de confusão dos candidatos tunados (card #250)

Matrizes no limiar por capacidade de contato, sobre a partição de teste (2026-01-01 a
2026-06-30, **53.486 respostas, 10.919 Detratores, 20,41%** — mesma partição de
`documents/extras/comparativo-modelos.md`).

**Origem dos números.** A execução completa dos seis modelos (issue #259, MR !136) reportou
Sensibilidade e tamanho de fila por modelo, mas não publicou as quatro contagens da matriz
(verdadeiro positivo, falso positivo, falso negativo, verdadeiro negativo) nem um artefato
versionado com elas. Este documento **deriva** essas quatro contagens a partir de duas
identidades que já bastam para reconstruí-las sem ambiguidade, dado que o total de Detratores
no teste (10.919) e o total de respostas (53.486) já são conhecidos:

- `Sensibilidade = VP / Detratores reais` → `VP = round(Sensibilidade × 10.919)`
- `Fila = VP + FP` (a fila de contato é exatamente quem o modelo selecionou) → `FP = Fila − VP`
- `FN = Detratores reais − VP`, `VN = (53.486 − 10.919) − FP`

O único arredondamento é o de `VP` (a Sensibilidade reportada tem 4 casas decimais); as demais
três contagens saem por subtração exata a partir daí, então o erro possível em qualquer célula
é de no máximo ±1 resposta. **Isto substitui, não dispensa, a matriz gerada de verdade quando
alguém rodar `matrizes_confusao_candidatos.gerar_matrizes` (#250) sobre os scores reais** — a
função já está pronta e testada em `develop`; falta só os scores brutos, que não existem fora
do ambiente com a base da Azul.

O Random Forest usa hiperparâmetros **padrão** (não tunados): a busca do card #189 tem toda a
infraestrutura pronta em `develop`, mas nunca foi executada de fato contra a base real —
`assets/hiperparametros_random_forest.json` não existe no repositório. A matriz dele aqui é a
do modelo *sem* tuning, não o resultado final esperado para #189.

## Gradient Boosting (tunado) — vencedor por Precisão Média e ROC-AUC

| | fora da fila | na fila de contato |
|---|---:|---:|
| **não Detrator** | 38.400 | 4.167 |
| **Detrator** | **6.036** | 4.883 |

Sensibilidade = 4.883 / 10.919 = 0,4472. Fila = 9.050.

## Regressão Logística (tunada)

| | fora da fila | na fila de contato |
|---|---:|---:|
| **não Detrator** | 38.294 | 4.273 |
| **Detrator** | **6.142** | 4.777 |

Sensibilidade = 4.777 / 10.919 = 0,4375. Fila = 9.050.

## Árvore de Decisão (tunada, max_depth=5)

| | fora da fila | na fila de contato |
|---|---:|---:|
| **não Detrator** | 38.133 | 4.434 |
| **Detrator** | **6.090** | 4.829 |

Sensibilidade = 4.829 / 10.919 = 0,4423. Fila = 9.263 (acima de 9.050 — a issue #259 já registra
que filas acima do orçamento pedido refletem empate de score, não escolha deliberada).

## Random Forest (padrão, hiperparâmetros da biblioteca — #189 pendente)

| | fora da fila | na fila de contato |
|---|---:|---:|
| **não Detrator** | 37.819 | 4.748 |
| **Detrator** | **6.511** | 4.408 |

Sensibilidade = 4.408 / 10.919 = 0,4037. Fila = 9.156.

## Leitura

Os falsos negativos (linha "Detrator", coluna "fora da fila" — em negrito) são a categoria mais
custosa segundo o protocolo do ART.7 (card #238): um Cliente que de fato se tornaria Detrator e
não é identificado perde a janela de recuperação. Nessa leitura, o Gradient Boosting deixa
passar **6.036** Detratores na mesma capacidade de contato em que a Regressão Logística deixa
passar 6.142 e a Árvore de Decisão 6.090 — uma diferença de poucas centenas entre os três
modelos genuinamente tunados, todos na mesma ordem de grandeza. O Random Forest sem tuning
deixa passar 6.511, o pior dos quatro nesta leitura — mas essa comparação não é definitiva
enquanto ele não passar pela busca de hiperparâmetros do #189.

Nenhum dos quatro modelos resolve a pendência já registrada na Seção 4.3.2 (Sensibilidade ≥ 0,70
e Precisão Média ≥ 0,40 simultaneamente): mesmo o líder (Gradient Boosting) fica em 0,4472 de
Sensibilidade nesta capacidade, menos da metade da meta de 0,70.
