# Decisão sobre explicabilidade: por que o grupo não adota SHAP

Registro de decisão sobre a técnica de explicabilidade usada na comparação de modelos da Seção 4.4.

| | |
|---|---|
| Card | #215 |
| Situação | Decidido |
| Data | 24/09/2026 |
| Decidido por | Grupo G01, em conversa registrada no canal da equipe |
| Consumido por | #214 (subseção da Regressão Logística), #193 e #194 (subseção dos ensembles), #251 (leitura da tabela comparativa) |

Este documento **decide e justifica**. Ele não redige a Seção 4.4 nem implementa explicabilidade
nenhuma: as implementações são as dos cards listados na seção 2.

## 1. A decisão

O grupo não adota SHAP na entrega do ART.7. A explicabilidade exigida pelo barema é atendida por
duas vias já implementadas, descritas na seção 2, e a ausência de SHAP é escolha de método
registrada aqui, não lacuna de execução.

A decisão foi tomada em 24/09/2026, depois de os odds ratio do card #212 estarem prontos. A ordem
importa: só com a explicabilidade intrínseca medida foi possível avaliar o que SHAP acrescentaria
sobre ela.

## 2. As duas vias de explicabilidade que o grupo entrega

| Via | O que produz | Onde está |
|---|---|---|
| **Intrínseca** | Odds ratio por feature original da Regressão Logística, com nível de referência declarado e suporte por coluna | Seções 6 e 7 de `notebooks/regressao_logistica.ipynb`, cards #212 e #213 |
| **Intrínseca** | Árvore de decisão visual | Cards #228 e #229, em execução |
| **Post-hoc** | Permutation importance do melhor ensemble | Card #191, em `develop` |
| **Post-hoc** | Gráficos de dependência parcial | Card #192, em execução |

Na data desta decisão, só a explicabilidade intrínseca da Regressão Logística e a permutation
importance do #191 estão em `develop`. A árvore visual e a dependência parcial estão sendo
entregues, e este documento não as dá como concluídas.

O barema do ART.7 exige que **ao menos um** dos modelos supervisionados apresente explicabilidade.
A via intrínseca da Regressão Logística já cumpre esse requisito sozinha.

## 3. O motivo principal: a matriz tem blocos de colunas colineares

A base analítica, depois do contrato de dados, produz uma matriz em que **a mesma informação
aparece repetida em várias colunas**. Dois casos foram medidos no card #212, sobre a partição de
treino:

- **Cancelamento ocupa sete colunas.** `preprocessamento_nps.aplicar_contrato_temporal_score_pos_viagem`
  apaga `TEMPO_VOO`, `ESTATISTICA_ATRASOSAIDA`, `ATRASO_CHEGADA` e `N_TRECHOS` em toda linha de voo
  cancelado, porque no instante do score essa informação não existe. Os quatro indicadores de
  ausência resultantes, mais a ausência de `ANTECEDENCIA_CANCELAMENTO` e os dois níveis de
  `CANCELAMENTO_VOO`, carregam o mesmo fato. A correspondência medida é de 100% de nulos nos
  cancelados contra 0,02% nos demais.
- **`TIPO_ENTRETENIMENTO` = `NAO_INFORMADO` é `VOO_TIPO` = `CONEXÃO`.** A coluna é nula em 109.698
  linhas do treino, e a correspondência com voo de conexão é de 100% nos dois sentidos.

SHAP reparte o crédito de uma previsão entre as features segundo o valor de Shapley
(SHAPLEY, 1953; LUNDBERG; LEE, 2017). Quando duas features carregam a mesma informação, essa
repartição **depende do esquema de amostragem usado para simular a ausência de cada uma**, e não do
fenômeno. Com colinearidade perfeita, a divisão entre elas é arbitrária, pelo mesmo motivo que a
penalidade L1 reparte arbitrariamente o peso entre as sete colunas de cancelamento.

O efeito prático é o que torna a decisão necessária. Uma atribuição por observação diria, para um
Cliente específico, que ele entrou na lista de contato **porque faltou o tempo de voo**, quando a
leitura correta é **porque o voo foi cancelado**. Explicação individual que parece precisa e não é
sai pior do que ausência de explicação individual, porque quem opera a lista não tem como duvidar
dela.

Resolver isso exigiria reagrupar as colunas colineares antes de aplicar SHAP, o que é trabalho de
engenharia de features e não estava no escopo desta sprint.

## 4. O custo computacional, dito com precisão

A base tem **484.915 registros**, e é sobre esse número que o argumento de custo costuma ser
construído. Ele não sustenta a decisão, e vale registrar por quê, para que ninguém o reapresente:

- **O KernelSHAP explica uma amostra, não a base inteira.** O uso descrito na seção 5, dar a quem
  faz o contato o motivo daquele caso, precisaria apenas das respostas efetivamente contatadas.
  Pela premissa de capacidade do documento, são 50 contatos por dia, ou cerca de 9.050 no semestre.
  Nessa escala o KernelSHAP cabe.
- **Para os três ensembles existe o TreeSHAP**, exato e de custo polinomial baixo
  (LUNDBERG et al., 2020), e todos os candidatos da outra dupla são baseados em árvore.
- **Para a Regressão Logística existe o `LinearExplainer`**, que é exato e praticamente gratuito.

O custo só impediria o KernelSHAP aplicado às 484.915 linhas, que é um uso que ninguém propôs.
**Ele não é motivo da decisão.**

## 5. O que se perde com a decisão

A entrega fica **sem atribuição por observação individual**. As duas vias adotadas explicam o
comportamento do modelo sobre o conjunto: quais variáveis ele usa para ordenar e quanto. Nenhuma
delas responde por que um Cliente específico ocupa a posição que ocupa na lista priorizada.

Para a operação de Experiência do Cliente isso tem custo concreto: quem faz o contato recebe a
posição na fila, mas não o motivo daquele caso.

Vale ser preciso sobre o tamanho da perda. A Regressão Logística **permite** decompor cada
observação pela própria forma linear, somando a contribuição de cada coluna por bloco, e isso não
depende de SHAP nenhum. Essa decomposição não foi entregue nesta sprint. O que a decisão custa,
portanto, é a atribuição por observação **nos modelos de árvore**, onde ela exigiria SHAP, e a
padronização de uma mesma leitura individual entre os quatro candidatos.

## 6. Divergência a resolver no documento

A matriz de riscos da Seção 4.1.5 registra, no risco R04, a mitigação *"apresentar os resultados do
SHAP como associação, não causalidade"*. Esse texto foi escrito quando o uso de SHAP era previsto e
**ficou inconsistente com esta decisão**.

O ajuste não é feito aqui, porque a Seção 4.1.5 é de outra autoria e este card não reescreve seção
de colega. Fica registrado para o card de revisão editorial da entrega.

## 7. Referências

LUNDBERG, S. M.; LEE, S.-I. A unified approach to interpreting model predictions. In: CONFERENCE
ON NEURAL INFORMATION PROCESSING SYSTEMS, 31., 2017, Long Beach. **Advances in Neural Information
Processing Systems 30**. Red Hook: Curran Associates, 2017. p. 4765-4774.

LUNDBERG, S. M. et al. From local explanations to global understanding with explainable AI for
trees. **Nature Machine Intelligence**, v. 2, n. 1, p. 56-67, 2020.

SHAPLEY, L. S. A value for n-person games. In: KUHN, H. W.; TUCKER, A. W. (org.). **Contributions
to the theory of games**, v. 2. Princeton: Princeton University Press, 1953. p. 307-317.
