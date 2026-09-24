# Interpretação das regras da Árvore de Decisão para a operação (card #234)

Leitura das 16 folhas da árvore final (`max_depth=4`, ver #232/#233), traduzida para
decisões que a área de Experiência do Cliente da Azul reconhece. Todos os números vêm de
`documents/extras/folhas_arvore_decisao.md` (taxa observada) e da estrutura real da árvore —
nenhum threshold foi arredondado a mão; os valores numéricos foram desfeitos do
`RobustScaler` de volta para a unidade original (minutos ou dias, conforme o dicionário de
dados da Seção 4.2).

**Associação, não causa.** As regras abaixo descrevem o que o modelo encontrou associado à
detração na base histórica, não o que causa a detração. Nenhuma afirmação aqui deve ser lida
como "fazer X evita a detração".

## O que domina a árvore

**1. Atraso de chegada (`ATRASO_CHEGADA`) é o primeiro corte, e o efeito é gradual.**
A árvore separa primeiro em ≤34,5min / >34,5min, e dentro do ramo >34,5min continua
cortando em 78,5min, 117,5min e 152,5min — quatro faixas de atraso, com risco crescente em
cada uma:

| Faixa de atraso na chegada | Taxa de Detrator observada | Vezes a prevalência geral (20,43%) |
|---|---|---|
| ≤ 34,5 min (maioria dos casos) | 13,1% a 66,1%* | 0,6x a 3,2x |
| 34,5–78,5 min | 31,4% a 47,4% | 1,5x a 2,3x |
| 78,5–117,5 min | 42,6% a 56,4% | 2,1x a 2,8x |
| 117,5–152,5 min | 68,1% | 3,3x |
| > 152,5 min (~2h30) | **76,5%** | **3,7x** |

\* dentro de ≤34,5min o risco varia muito porque esse ramo também é onde o cancelamento
com pouca antecedência aparece — ver item 2.

**Leitura para a operação:** atraso de chegada acima de ~2h30 é o sinal isolado mais forte de
risco de detração que a árvore encontrou. Vale como critério de priorização de contato
pós-viagem.

**2. Cancelamento com pouca antecedência é o segundo sinal forte — mas só se aplica a quem
teve cancelamento.**

Atenção: `ANTECEDENCIA_CANCELAMENTO` só existe preenchida para voos com cancelamento
associado (16,3% da base, conforme a Seção 4.2 do documento); para os demais 83,7% dos
registros ela é nula e o pré-processador imputa a mediana (10 dias) com um indicador de
ausência. Isso significa que o corte da árvore em `ANTECEDENCIA_CANCELAMENTO ≤ 9,5 dias`
não separa "clientes que cancelam com pouca antecedência" de "clientes que cancelam com
folga" — ele separa, na prática, **cancelamento recente (≤9,5 dias) do restante da base**
(que inclui tanto quem não cancelou quanto quem cancelou com mais folga).

| Situação | Taxa de Detrator observada |
|---|---|
| Sem cancelamento, ou cancelamento com >9,5 dias de antecedência, atraso ≤34,5min | 13,1% a 25,9% |
| **Cancelamento com ≤9,5 dias de antecedência**, atraso ≤34,5min | **58,6% a 76,0%** |

**Leitura para a operação:** cancelamento avisado em cima da hora pesa tanto quanto um atraso
de 2h30 no risco de detração. Essa é uma alavanca operacional real — antecedência de aviso é
algo que a Azul controla, ao contrário do atraso em si.

**3. Fidelidade (`TIER_VIAGEM_DIAMANTE`) tem efeito secundário, mas consistente: Cliente
Diamante detrata mais dentro de cada faixa de atraso/cancelamento, não menos.**

O tier entra como o último corte em quatro ramos diferentes da árvore, e nos quatro o
Cliente Diamante tem taxa maior que o não-Diamante no mesmo contexto de atraso/cancelamento —
a diferença fica entre 10 e 16 pontos percentuais em todos eles:

| Contexto (mesmo ramo de atraso/cancelamento) | não-Diamante | Diamante | Diferença |
|---|---|---|---|
| Cancelamento ≤2,5 dias de antecedência | 66,1% | 76,0% | +9,9 pp |
| Cancelamento 2,5–9,5 dias de antecedência | 45,9% | 58,6% | +12,7 pp |
| Atraso 34,5–44,5 min | 31,4% | 47,4% | +16,0 pp |
| Atraso 44,5–78,5 min | 42,6% | 56,6% | +14,0 pp |
| Atraso 78,5–117,5 min | 56,4% | 69,4% | +13,0 pp |

**Leitura para a operação:** quando a viagem tem problema (atraso ou cancelamento), o Cliente
Diamante reclama proporcionalmente mais do que o Cliente sem esse status — o contrário do que
a intuição de "cliente fiel é mais tolerante" sugeriria. Isso é coerente com a expectativa de
serviço mais alta que um Cliente de tier superior costuma ter. Acima de ~117,5min de atraso a
árvore para de usar o tier como corte (profundidade máxima atingida), então esse padrão não
está confirmado nos atrasos mais extremos.

## Limitações da leitura

- A árvore captura interação entre variáveis por construção (é a vantagem dela sobre a
  Regressão Logística), mas com apenas 16 folhas ela só descreve as interações mais fortes;
  efeitos mais sutis ficam de fora — é a troca aceita ao limitar a profundidade a 4 por
  legibilidade (ver #232).
- O rótulo `class: 0/1` do `export_text` (arquivo `regras_arvore_decisao.txt`) reflete o voto
  ponderado por `class_weight="balanced"`, não a maioria observada — todas as taxas citadas
  aqui vêm da contagem real por folha, não desse rótulo.
- `ANTECEDENCIA_CANCELAMENTO` é condicional a `CANCELAMENTO_VOO`, como registrado na Seção
  4.2 do documento; a leitura acima já considera essa condicionalidade, mas qualquer reuso
  futuro dessa variável precisa repetir o cuidado.
