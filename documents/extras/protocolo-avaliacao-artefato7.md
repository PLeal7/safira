# Protocolo de avaliação do Artefato 7 — critério de busca de hiperparâmetros

Material de apoio do card #238 (dupla de Métricas e Decisões, Arthur e Cássio). Registra a
escolha do critério único usado por `GridSearchCV`/`RandomizedSearchCV` para tunar os quatro
modelos candidatos do Artefato 7 (Regressão Logística, Árvore de Decisão, Random Forest e
Gradient Boosting). Este arquivo não redefine as métricas de negócio nem as metas já publicadas
na Seção 4.3.2 — ele decide qual escalar guia a busca de hiperparâmetro, e explica por que essa
escolha é compatível com o que já foi decidido ali.

## O que a Seção 4.3.2 já estabeleceu

A Seção 4.3.2 (`Métricas relacionadas ao modelo` e `Resultados do modelo candidato`), já em
`develop`, define três métricas de negócio e suas metas, medidas sobre a partição de teste
(2026-01-01 a 2026-06-30, 53.486 respostas):

| Métrica | Meta | Valor do primeiro candidato |
|---|---|---:|
| Sensibilidade (Recall) na classe Detrator | ≥ 0,70 | 0,4464 |
| Precisão Média (Average Precision) | ≥ 0,40 | 0,5213 |
| ROC-AUC | ≥ 0,75 | 0,7492 |

O falso negativo já está registrado ali como o erro mais custoso do problema: um Cliente que de
fato se tornaria Detrator e não é identificado perde a janela de recuperação antes que a
experiência negativa se concretize. É essa leitura, e não uma preferência de literatura, que
justifica dar mais peso ao recall na busca de hiperparâmetro.

A mesma seção também registra uma pendência ainda sem solução: nenhum tamanho de fila do
primeiro candidato satisfaz Sensibilidade ≥ 0,70 e Precisão Média ≥ 0,40 ao mesmo tempo — atingir
0,70 de Sensibilidade exige uma fila de 22.141 respostas (122 contatos/dia), ponto em que a
Precisão cai para 0,3452; e a Precisão só se mantém acima de 0,40 até uma fila de 16.921
respostas (93 contatos/dia), ponto em que a Sensibilidade é de apenas 0,6198. Essa pendência foi
explicitamente deixada para a Seção 4.4, e é isso que os cards 15B.1 e 18A.3 do Artefato 7
precisam responder à luz dos quatro candidatos tunados.

## Por que a busca de hiperparâmetro precisa de um critério à parte

`GridSearchCV` e `RandomizedSearchCV` escolhem, dentre uma grade de configurações, aquela que
maximiza um único valor de `scoring`. Sensibilidade, Precisão Média e ROC-AUC sozinhas não
servem a esse papel sem uma regra de desempate: otimizar só por Sensibilidade tende a escolher
hiperparâmetros que classificam quase tudo como Detrator (o mesmo problema que a Precisão Média
já existe para evitar, ver Seção 4.3.2); otimizar só por ROC-AUC ou só por Precisão Média não
prioriza recall na medida que o custo do falso negativo já registrado exige.

## Decisão: F2 (F-beta com beta=2) como critério de busca

A busca de hiperparâmetro das quatro duplas de modelagem usa o F-beta score com beta=2:

$$
F_2 = \frac{(1+2^2) \times P \times R}{(2^2 \times P) + R} = \frac{5 \times P \times R}{4P + R}
$$

Onde `P` é a precisão e `R` é o recall (Sensibilidade) sobre a classe Detrator. O termo `4P`
no denominador dá ao recall um peso quatro vezes maior que à precisão na média harmônica — a
tradução direta, para dentro da função de busca, da assimetria de custo que a Seção 4.3.2 já
registrou entre falso negativo e falso positivo.

**O que o F2 é:** o escalar que orienta `GridSearchCV`/`RandomizedSearchCV` a escolher
hiperparâmetros, calculado dentro de cada fold do `GroupKFold` por Cliente já existente
(`src/validacao.py`, issue #102).

**O que o F2 não é:** não substitui Sensibilidade, Precisão Média ou ROC-AUC na tabela
comparativa final (card 18A.1) nem nas metas de negócio da Seção 4.3.2; não define o threshold
operacional, que continua sendo derivado da capacidade de contato da equipe de Experiência do
Cliente (card 15B.1); e não é usado sozinho para recomendar o modelo final — essa recomendação
(card 18A.3) é lida sobre Sensibilidade, Precisão Média e ROC-AUC, como a Seção 4.3.2 já faz.

## Por que não acurácia

A base tem 20,44% de respostas Detratoras (Seção 4.2.1). Um classificador que sempre prevê
"não Detrator" atinge acurácia alta sem identificar nenhum caso de interesse — o mesmo motivo
que já levou a Seção 4.3.2 a preferir Precisão Média e ROC-AUC a uma métrica sensível à
proporção das classes. Acurácia segue fora tanto da tabela comparativa quanto do critério de
busca.

## Consumido por

- Cards 05A.1/05A.2 (`avaliar()` e `scorer_f2`, a implementação deste critério).
- Card 02A.3 (referência técnica consolidada, que reúne esta decisão com a de validação do card
  02A.2).
- Card 09A (texto acadêmico da Seção 4.4, que redige esta mesma decisão em prosa com citação
  ABNT — este arquivo é material de apoio, não o texto final).
