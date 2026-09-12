# Tabela comparativa entre o modelo candidato e os pisos

Material de apoio do card #108, pronto para a redação do item (d) da Seção 4.3 e para a Seção 4.4.
Este arquivo não redige a seção: entrega a tabela já gerada pela seção 9 de
`notebooks/modelagem.ipynb`, sem valor digitado à mão, para que a prosa seja escrita ao redor.

Todos os números saem da **partição de teste** (2026-01-01 a 2026-06-30, 53.486 respostas, 10.919
Detratores, 20,41%). Nenhum vem dos folds de validação das seções 3 e 5.

## Tabela comparativa

| Modelo | Precisão média | ROC-AUC | Brier | Limiar | Fila | Precisão no topo | Cobertura | F1 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| classe majoritária | 0,2041 | 0,5000 | 0,2041 | 0,0000 | 53.486 | 0,2041 | 1,0000 | 0,3391 |
| regressão logística | 0,5019 | 0,7442 | 0,1877 | 0,5993 | 9.050 | 0,5283 | 0,4379 | 0,4788 |
| **gradient boosting** | **0,5213** | **0,7492** | **0,1312** | **0,2934** | **9.050** | **0,5386** | **0,4464** | **0,4882** |

## Como ler a coluna do limiar

As três primeiras métricas não dependem de ponto de corte. As cinco últimas dependem, e por isso
os três modelos foram medidos sob a **mesma capacidade de operação**, `k = 50 x 181 = 9.050`
contatos, e não sob o mesmo valor numérico de limiar. Cada modelo emite score na sua própria
escala, e igualar o número produziria uma comparação inválida: 0,29 na escala do candidato não
significa o mesmo que 0,29 na escala da logística.

A coluna `Fila` existe por causa do piso trivial. Ele emite a mesma probabilidade para toda linha,
então o limiar cai sobre essa constante e a seleção alcança a partição inteira, 53.486 e não 9.050.
A precisão dele no topo é a própria prevalência e a cobertura é 1,0 porque ele aciona todo mundo.
Sem essa coluna, os dois números apareceriam ao lado dos demais como se viessem de uma fila
comparável.

## Ganho do candidato sobre cada piso

| Métrica | Piso | Valor do piso | Candidato | Ganho absoluto | Razão |
|---|---|---:|---:|---:|---:|
| Precisão média | classe majoritária | 0,2041 | 0,5213 | +0,3171 | 2,55x |
| Precisão média | regressão logística | 0,5019 | 0,5213 | +0,0193 | 1,04x |
| ROC-AUC | classe majoritária | 0,5000 | 0,7492 | +0,2492 | 1,50x |
| ROC-AUC | regressão logística | 0,7442 | 0,7492 | +0,0050 | 1,01x |
| Precisão no topo | classe majoritária | 0,2041 | 0,5386 | +0,3344 | 2,64x |
| Precisão no topo | regressão logística | 0,5283 | 0,5386 | +0,0103 | 1,02x |

O absoluto e a razão entram juntos porque nenhum dos dois sustenta sozinho um juízo de relevância:
0,0193 não diz por si se é muito, e uma razão infla qualquer diferença quando o piso é próximo de
zero.

## O que a tabela sustenta, e o que não sustenta

**O ganho sobre o piso trivial é grande e não é a notícia.** Superar um modelo que não olha
nenhuma feature é o mínimo exigido, e é para isso que o piso linear existe ao lado.

**O ganho sobre a regressão logística é pequeno e consistente.** Na mesma fila de 9.050 contatos,
o candidato encontra 4.874 Detratores contra 4.781 da logística: 93 Detratores a mais no semestre,
cerca de meio por dia de operação. É ganho real nas três métricas, mas apresentá-lo como salto
seria distorcer.

**A diferença relevante está na calibração.** O Brier cai de 0,1877 para 0,1312, uma redução de
30%. As duas ordenam de forma parecida, mas só o candidato emite probabilidade que pode ser lida
como risco, o que importa para um score que vira faixa de risco na mão da operação.

**Uma meta da Seção 4.1.3 não foi atingida.** O ROC-AUC ficou em 0,7492 contra a meta de 0,75,
uma diferença de 0,0008. Não muda conclusão prática nenhuma, mas arredondar para 0,75 na redação
afirmaria que a meta foi cumprida quando não foi. A precisão média, meta de 0,40, ficou em 0,5213.

## Como os números foram gerados

`notebooks/modelagem.ipynb`, seção 9, por `modelo.tabela_comparativa` e `modelo.ganhos_do_candidato`
(`src/modelo.py`), sobre os mesmos objetos `trivial`, `logistica` e `candidato` das seções 2 e 4.1.
Os valores sem arredondamento ficam em `assets/comparativo_modelos.json`, gravado pela própria
célula. Para reproduzir, rodar o notebook de ponta a ponta contra
`data/processed/base_analitica.parquet`.
