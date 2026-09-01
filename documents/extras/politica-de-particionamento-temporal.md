# Política de particionamento temporal dos conjuntos

Registro de decisão da divisão da base analítica em treino, validação e teste.

| | |
|---|---|
| Card | #127 |
| Situação | Decidido |
| Data | 01/09/2026 |
| Consumido por | #113 (implementação do split), #116 (item (a) da Seção 4.3), #131 (congelamento dos splits) |
| Implementação que recebe estes parâmetros | `src/split.py`, entregue em #128 |

Este documento **decide e justifica**. Ele não implementa o corte nem redige a
Seção 4.3. Ele é a fonte única das datas de corte: `src/split.py` recebe essas
datas como parâmetro e deliberadamente não as fixa em constante, para que não
exista uma segunda fonte de verdade capaz de divergir desta.

---

## 1. A decisão

A base analítica é dividida por **data prevista de partida do voo** (`DATA_STD`),
em três conjuntos contíguos e sem sobreposição:

| Conjunto | Início | Fim | Meses | Ciclo anual coberto |
|---|---|---|---:|---|
| Treino | 01/07/2023 | 30/06/2025 | 24 | dois ciclos completos |
| Validação | 01/07/2025 | 31/12/2025 | 6 | pico de julho e pico de dezembro |
| Teste | 01/01/2026 | 30/06/2026 | 6 | pico de janeiro e baixa de fevereiro a maio |

**Convenção de intervalo:** fechado à esquerda e aberto à direita. Um voo datado
exatamente em 01/07/2025 pertence à validação, não ao treino. Sem essa convenção
declarada, o dia do corte cairia em dois conjuntos ou em nenhum, conforme o
operador de comparação que o implementador escolhesse.

**Chamada correspondente em `src/split.py`:**

```python
particoes, metadados = dividir(
    df,
    corte_validacao="2025-07-01",
    corte_teste="2026-01-01",
    sem_data="treino",   # condicionado à verificação da Seção 5
)
```

## 2. Proporções-alvo

| Conjunto | Proporção-alvo (meses) | Tolerância aceita (linhas) |
|---|---:|---|
| Treino | 66,7% | 60% a 72% |
| Validação | 16,7% | 12% a 21% |
| Teste | 16,7% | 12% a 21% |

**O que é vinculante são as datas, não as proporções.** As proporções são
consequência das datas e não podem ser ajustadas para caber na faixa: o volume
mensal de respostas varia, e a regra de desempate por Cliente da Seção 6 remove
linhas do treino em quantidade que só se conhece em execução. A faixa serve como
alarme, não como meta. Se a composição observada cair fora dela, a resposta é
reabrir este registro e mover uma data de corte com justificativa escrita, nunca
reamostrar até a proporção fechar.

A composição efetiva de cada execução fica registrada nos metadados devolvidos
por `dividir` e na tabela de `resumo`, que reporta n, intervalo de datas,
Clientes distintos e taxa do alvo por partição.

## 3. Por que o corte é temporal, e não aleatório

**Porque a divisão aleatória mede uma tarefa que a operação nunca enfrenta.** O
Safira pontua o risco de detração no intervalo entre a realização do voo e a
resposta à pesquisa, que é enviada um dia após o voo e permanece aberta por sete
dias (Seção 4.1.3). O modelo sempre prevê para frente, a partir do que se sabe
até hoje. Embaralhar as linhas colocaria voos de 2026 no treino e voos de 2024 no
teste, e a métrica resultante descreveria a habilidade de prever o passado
conhecendo o futuro. Essa métrica seria melhor que a real e não teria contraparte
em produção.

**Porque o efeito de período vazaria para os três conjuntos.** A Seção 4.2.1
documenta um choque em 2024Q4, quando a taxa de detratores chegou a 32,58% contra
20,44% no período completo, e mostra que ele não é explicado pela composição
operacional: a detração subiu inclusive entre voos pontuais, de 16,6% em 2024Q3
para 25,4% em 2024Q4. É conjuntura reputacional, não sinal do voo. Sob divisão
aleatória, o mesmo trimestre atípico apareceria nos três conjuntos e o modelo
seria avaliado sobre um período que já viu.

**Porque a dependência intracliente sobreviveria ao corte por data.** A Seção
4.2.1 registra que 26,8% das respostas vêm de Clientes que responderam mais de
uma vez, e a Hipótese 4 da Seção 4.2.3 estima, sobre 77.673 respostas de Clientes
com histórico, que a chance de detratar entre quem já detratou é 4,75 vezes a
chance entre quem não detratou (IC 95% de 4,56 a 4,94), já descontados atraso na
chegada e cancelamento. Um mesmo Cliente presente no treino e no teste faria o
modelo reconhecer a pessoa em vez de aprender o fenômeno. Por isso o corte é
temporal **e** por Cliente, conforme a Seção 6.

Esta política atende ao plano de resposta do risco **R01** da matriz da Seção
4.1.5, que trata o desempenho artificialmente alto como sinal de alerta e não
como resultado.

## 4. Por que estas datas

**Horizonte.** A base analítica cobre 01/07/2023 a 30/06/2026, 36 meses completos
de operação doméstica, com 484.915 registros e 407.139 Clientes distintos (Seção
4.2.1). Trinta e seis meses dividem-se exatamente em 24 + 6 + 6, sem mês
fracionado em nenhum conjunto.

**Sazonalidade da demanda.** O mercado doméstico brasileiro tem alta em janeiro,
julho e dezembro, e baixa entre fevereiro e maio. Isso restringe as datas de duas
maneiras que uma escolha por proporção pura ignoraria:

1. **O treino precisa de ciclos anuais inteiros.** Vinte e quatro meses garantem
   que todo mês do calendário apareça duas vezes no treino. Um treino de 25 ou 27
   meses veria janeiro três vezes e junho duas, e o modelo herdaria um
   desbalanceamento sazonal que nada na operação justifica.
2. **Validação e teste não podem cair dentro de uma única estação.** Este é o
   erro que a janela mais curta convida. Um teste de três meses no fim da base
   cobriria abril, maio e junho de 2026, ou seja, baixa temporada inteira, e
   mediria o modelo num regime de demanda que não representa o ano. Com seis
   meses, o teste contém janeiro, mês de pico, e o bloco de baixa de fevereiro a
   maio; a validação contém julho e dezembro, os outros dois picos, e a baixa de
   agosto a novembro. Cada conjunto de avaliação vê pico e vale.

**Posição do choque de 2024Q4.** O trimestre atípico cai inteiramente dentro do
treino. É o lugar correto: o modelo aprende que períodos de choque reputacional
existem, sem que a métrica de teste seja inflada ou deprimida por um evento único
e irrepetível.

**Recência do teste.** O teste ocupa os seis meses mais recentes da base. É a
melhor aproximação disponível do regime em que o modelo vai operar, e é a única
posição que permite ler a métrica de teste como estimativa de desempenho futuro
em vez de retrospectiva.

## 5. Registros sem data válida

**Regra:** vão para o **treino**, condicionada à verificação de anterioridade
descrita abaixo. Se a verificação falhar, são **excluídos** dos três conjuntos.

Nunca vão para validação ou teste. Nesses dois conjuntos a data é necessária para
situar cada linha dentro do período avaliado, e não apenas antes dele.

O card #128 relata cerca de 120.000 linhas sem `DATA_STD` na base analítica,
aproximadamente um quarto do total, originadas de fontes que não trazem a coluna,
e não de datas corrompidas. Descartar um quarto da base sem ganho de rigor é caro
o bastante para exigir prova, e a prova está implementada em
`verificar_anterioridade_sem_data`, que exige duas condições simultâneas:

1. `RESPONDENT_ID` acompanha a ordem cronológica nas linhas datadas, com
   correlação de Spearman de no mínimo 0,99;
2. o maior `RESPONDENT_ID` sem data é menor que o menor `RESPONDENT_ID` datado.

Valendo as duas, os blocos não se sobrepõem e as linhas sem data precedem todo o
período datado. Nesse caso elas são as observações mais antigas disponíveis, que
é exatamente o lugar de dados de treino. A função levanta `AssertionError` quando
qualquer condição falha, de modo que uma base futura com outro padrão de ausência
não herda em silêncio uma conclusão que valia para esta.

**A verificação é obrigatória a cada execução, e não uma vez.** `sem_data="treino"`
só pode ser usado depois de `verificar_anterioridade_sem_data` passar na mesma
execução.

> **Pendência aberta, a resolver antes de #113.** Há divergência entre fontes
> sobre a cobertura da data, e ela precisa ser fechada, não contornada:
> o dicionário de dados da Seção 4.2.1 declara `DATA_STD` com 100% de
> preenchimento; a Seção 4.1.3 descreve a base recebida com 98.414 respostas
> entre 01/06/2023 e 26/07/2026, enquanto a Seção 4.2.1 descreve a base analítica
> com 484.915 registros entre 01/07/2023 e 30/06/2026; e #128 relata 120.000
> linhas sem data, com a menor data datada em 06/01/2024. As três leituras não
> podem estar certas ao mesmo tempo. Quem implementar #113 deve rodar
> `verificar_anterioridade_sem_data` e `resumo` na base analítica real e
> registrar aqui os números observados. **Se a menor data datada for de fato
> 06/01/2024, o corte de treino desta política começa depois do início declarado
> do horizonte, e as datas das Seções 1 e 4 devem ser reabertas antes de
> congelar os splits em #131.**

## 6. Registros sem Cliente e desempate por recorrência

**Registros sem `ID_GOLDENRECORD`:** excluídos dos três conjuntos. São 103
registros, 0,02% da base (Seção 4.2.1). O nulo ocorre simultaneamente na tabela
de pesquisa e na de perfil, então não há como afirmar que duas dessas linhas
pertencem a Clientes diferentes; tratá-las como grupos unitários reabriria
justamente o vazamento que a partição agrupada existe para impedir.

**Cliente que aparece em mais de um período:** mantido apenas no conjunto mais
recente em que ocorre, e suas linhas anteriores são descartadas. A direção
importa. Preservar o conjunto mais recente mantém teste e validação intactos, que
são os que medem desempenho, e concentra a perda no treino, que é o mais
abundante. A perda correspondente é reportada nos metadados em
`linhas_removidas_por_recorrencia` e `linhas_removidas_do_treino_por_validacao`,
para que seja auditável em vez de silenciosa.

## 7. Registros fora do horizonte

**Regra:** registros com data posterior a 30/06/2026 são excluídos dos três
conjuntos.

A Seção 4.1.3 menciona respostas até 26/07/2026, o que colocaria um julho
incompleto no fim da base. Um mês parcial no conjunto de teste distorceria tanto
a comparação sazonal quanto a taxa do alvo da partição, e julho é justamente mês
de pico: meio julho pesaria na métrica como se fosse julho inteiro. O horizonte
fecha em mês cheio.

Registros anteriores a 01/07/2023 recebem o mesmo tratamento, pela mesma razão.

## 8. Como conferir

A conferência é por asserção, não por inspeção visual. `conferir` verifica quatro
falhas que passam despercebidas na leitura de uma tabela:

- nenhuma linha em duas partições;
- nenhum `ID_GOLDENRECORD` em duas partições;
- maior data do treino anterior à menor data da validação, e maior data da
  validação anterior à menor data do teste, aferido sobre as datas reais e não
  sobre os parâmetros de corte, porque um filtro errado deixaria o parâmetro
  coerente;
- soma das três partições igual ao total esperado, quando informado.

Um terceiro reproduz esta divisão com o que está escrito aqui: as duas datas de
corte da Seção 1, a convenção de intervalo, e as regras das Seções 5, 6 e 7.

## 9. O que esta política não decide

- Não define features, nem o tratamento do desbalanceamento, nem métricas.
- Não decide o uso dos pesos de pós-estratificação da Seção 4.2.1 no treinamento,
  na avaliação ou apenas na comunicação. Essa decisão continua em aberto.
- Não substitui `criar_folds_validacao_por_cliente`: a validação cruzada por
  Cliente dentro do treino é assunto de #102 e opera sobre a partição de treino
  definida aqui.
- Não congela os splits. O congelamento com semente, hash e artefato de índices é
  #131, e consome estas datas.
