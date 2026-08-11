# Documentação Modelo Preditivo - Inteli

```
INSTRUÇÕES GERAIS (remova este trecho ao final)

Você deve editar este documento utilizando notação markdown - siga as convenções neste link 
https://docs.github.com/en/get-started/writing-on-github/getting-started-with-writing-and-formatting-on-github/basic-writing-and-formatting-syntax
```

## Nome da Solução
### Nome do grupo
#### (preencha aqui os nomes dos integrantes, em ordem alfabética, separados por vírgula)

## Sumário
[1. Introdução](#c1)

[2. Objetivos e Justificativa](#c2)

[3. Metodologia](#c3)

[4. Desenvolvimento e Resultados](#c4)

[5. Conclusões e Recomendações](#c5)

[6. Referências](#c6)

[Anexos](#attachments)

### 1. Introdução

A Azul Linhas Aéreas Brasileiras atua na aviação comercial desde 2008. Sua sede administrativa fica em Alphaville, Barueri, na região metropolitana de São Paulo, e seus principais centros de operação são os aeroportos de Viracopos, em Campinas, e Confins, em Belo Horizonte. Com aproximadamente 15 mil Tripulantes e uma malha que alcança mais de uma centena de aeroportos brasileiros, é a companhia de maior capilaridade do país. Em boa parte dessas cidades ela opera sozinha, e essa condição define seu posicionamento de mercado. Enquanto as concorrentes disputam as rotas de maior densidade entre capitais, a Azul construiu vantagem competitiva justamente onde a alternativa de transporte é lenta ou simplesmente não existe.

O alcance da companhia se estende para além do transporte de passageiros. Ela opera também na logística de cargas, no varejo de turismo, na manutenção aeronáutica e em um programa de fidelidade próprio, de modo que a relação com o Cliente não começa nem termina no voo. Esse ponto ganhou peso depois da reestruturação financeira concluída em 2026, da qual a empresa saiu com endividamento reduzido e um plano de crescimento deliberadamente mais moderado, concentrado no mercado doméstico e em rotas de maior rentabilidade. Quando a estratégia deixa de se apoiar na expansão da malha, a base de Clientes existente passa a responder por uma fatia maior do resultado. A experiência entregue em cada viagem deixa de ser apenas atributo de marca e se torna variável econômica.

A leitura dessa experiência cabe à área de Experiência do Cliente e se apoia principalmente no Net Promoter Score. Um dia após o voo, parte dos passageiros recebe uma pesquisa em que indica, numa escala de 0 a 10, o quanto recomendaria a Azul a um amigo ou familiar. As notas 9 e 10 identificam Promotores, 7 e 8 identificam Neutros, e as notas de 0 a 6 identificam Detratores. O questionário vai além da avaliação geral e cobre etapas específicas da jornada, como reserva, check-in, embarque, atendimento a bordo e bagagem. O indicador da companhia se mantém consistentemente acima da média do setor, o que dá à Azul uma posição confortável na comparação com as concorrentes, mas não resolve o problema de como agir sobre os casos individuais de insatisfação.

O desenho da medição impõe dois limites à atuação. O primeiro é de tempo. A informação sobre um Cliente insatisfeito só chega depois que a viagem terminou e depois que ele decidiu responder, o que restringe qualquer intervenção ao campo da recuperação, quando a experiência ruim já foi vivida. O segundo é de cobertura. A taxa de resposta é baixa e alguns perfis participam sistematicamente menos que outros, entre eles quem compra por agência de viagens e quem voa com pouca frequência. Uma parcela relevante da insatisfação real, portanto, nunca chega a ser registrada.

O efeito combinado dos dois limites é que a companhia enxerga com clareza o que já aconteceu, mas não consegue antecipar com quem vai acontecer. Uma mesma falha operacional atinge centenas de passageiros ao mesmo tempo e produz reações bastante distintas, porque o peso de um atraso ou de uma bagagem extraviada varia conforme o perfil do Cliente, o motivo da viagem, a categoria de fidelidade e o histórico de relacionamento com a companhia. Sem uma forma de distinguir esses casos antes que a avaliação ocorra, a priorização dos esforços de atendimento depende de critérios heurísticos e de análise manual, e as decisões de melhoria da jornada acabam apoiadas em um retrato parcial e defasado da experiência do Cliente.

## <a name="c2"></a>2. Objetivos e Justificativa
### 2.1 Objetivos
```
Descreva resumidamente os objetivos gerais e específicos do seu parceiro de negócios.

Remova este bloco ao final
```

### 2.2 Proposta de solução
```
Descreva resumidamente sua proposta de modelo preditivo e como esse modelo pretende resolver o problema, atendendo os objetivos.

Remova este bloco ao final
```

### 2.3 Justificativa
```
Faça uma breve defesa de sua proposta de solução, escreva sobre seus potenciais, seus benefícios e como ela se diferencia.

Remova este bloco ao final
```

## <a name="c3"></a>3. Metodologia
```
Descreva a metodologia CRISP-DM e suas etapas de desenvolvimento, citando o referencial teórico. Você deve apenas enunciar os métodos, sem dizer ainda como eles foram aplicados, nem quais resultados foram obtidos.

Remova este bloco ao final
```

## <a name="c4"></a>4. Desenvolvimento e Resultados
### 4.1. Compreensão do Problema
#### 4.1.1. Contexto da indústria 
```
Descreva aqui o Contexto Setorial e posicione a análise das 5 Forças de Porter

Remova este bloco ao final
```
#### 4.1.2. Análise SWOT 
```
Posicione aqui sua análise SWOT.

Remova este bloco ao final
```

#### 4.1.3. Planejamento Geral da Solução

**a) Dados disponíveis**
 
A base utilizada no projeto é a `AMOSTRA_NPS_INTELI_FINAL`, fornecida pela Azul Linhas Aéreas Brasileiras a partir de sua plataforma de dados e disponibilizada à equipe em formato de planilha. O conjunto reúne 98.414 respostas à pesquisa de NPS coletadas entre 1º de junho de 2023 e 26 de julho de 2026, todas referentes a voos domésticos. Cada registro corresponde a uma resposta individual, associada a um localizador de reserva e enriquecida com atributos operacionais do voo realizado. Todos os campos foram anonimizados pela companhia em conformidade com a LGPD, sem qualquer informação que permita identificar o passageiro.
 
A pesquisa é enviada um dia após o voo a 50% dos Clientes domésticos, que dispõem de sete dias para responder, com quarentena de noventa dias entre envios ao mesmo Cliente. Isso significa que a amostra representa quem respondeu, e não a totalidade dos passageiros transportados no período.
 
| Nome da Coluna | Tipo de Dado | Preenchimento | Descrição |
|---|---|---|---|
| RESPONDENT_ID | Numérico | 100% | Identificador único da resposta à pesquisa de NPS |
| CLIENTE_RECORDLOCATOR | Texto | 100% | Localizador da reserva à qual a resposta se refere |
| DATA_STD | Data | 100% | Data prevista de partida do voo (Scheduled Time of Departure) |
| EQUIPAMENTO_PREFIXO | Texto | 100% | Prefixo de matrícula da aeronave utilizada. Em jornadas com mais de um trecho, traz os prefixos concatenados |
| BASE_AIRPORTLEG | Texto | 100% | Sequência de aeroportos da jornada, no formato origem/destino ou origem/conexão/destino |
| PERFIL_TUDOAZUL | Texto | 100% | Categoria do Cliente no programa de fidelidade (Cliente Azul, Tudo Azul, Topázio, Safira, Diamante, Azul Diamante Unique, Azul One) |
| VOO_TIPO | Texto | 100% | Natureza da operação: Direto, Conexão ou Escala |
| TIPO_ENTRETENIMENTO | Texto | 100% | Sistema de entretenimento de bordo disponível na aeronave |
| NPS_PRINCIPAL | Numérico | 100% | Classificação do Cliente na pergunta principal de recomendação: -100 (Detrator), 0 (Neutro) ou 100 (Promotor) |
| NPS_ATRASO | Numérico | 14,7% | Avaliação da experiência com atraso no voo |
| NPS_BAGAGEM | Numérico | 34,5% | Avaliação do serviço de bagagem despachada |
| NPS_BAGMAO | Numérico | 79,8% | Avaliação do espaço e serviço de bagagem de mão |
| NPS_CANCELAMENTO24H | Numérico | 1,4% | Avaliação da experiência com cancelamento em até 24 horas |
| NPS_CKBALCAO | Numérico | 11,1% | Avaliação do check-in realizado no balcão |
| NPS_CKMOBILE | Numérico | 54,1% | Avaliação do check-in realizado pelo aplicativo |
| NPS_CKTOTEM | Numérico | 0,3% | Avaliação do check-in realizado no totem de autoatendimento |
| NPS_CKWEB | Numérico | 14,4% | Avaliação do check-in realizado pelo site |
| NPS_COMISSARIOS | Numérico | 78,2% | Avaliação do atendimento dos Tripulantes a bordo |
| NPS_CONFORTO | Numérico | 73,1% | Avaliação do conforto da aeronave, incluindo assento e espaço |
| NPS_EMBARQUE | Numérico | 84,0% | Avaliação do processo de embarque |
| NPS_ENTRETENIMENTO | Numérico | 35,8% | Avaliação do sistema de entretenimento de bordo |
| NPS_LIMPEZA | Numérico | 75,3% | Avaliação da limpeza da aeronave |
| NPS_PILOTOS | Numérico | 76,4% | Avaliação dos pilotos, considerando comunicação e condução do voo |
| NPS_RESAGENCIA | Numérico | 37,5% | Avaliação da reserva realizada por agência de viagem |
| NPS_RESWEB | Numérico | 46,9% | Avaliação da reserva realizada pelos canais digitais próprios |
| NPS_SNACKS | Numérico | 65,1% | Avaliação do serviço de alimentação a bordo |
| NPS_TUDOAZUL | Numérico | 29,4% | Avaliação do programa de fidelidade |
| NPS_WIFI | Numérico | 16,2% | Avaliação do serviço de conexão Wi-Fi a bordo |
| SUB_ENTRETENIMENTO1 | Texto | 31,1% | Indicação de falha no sistema de entretenimento durante o voo (Sim, Não, Não assisti) |
| SUB_ENTRETENIMENTO2 | Texto | 6,7% | Natureza da falha relatada no entretenimento, quando houve |
| SUB_FIL_MOTIVOVIAGEM | Texto | 99,4% | Motivo declarado da viagem: Lazer, Trabalho, Pessoal ou Trabalho combinado com lazer |
| SUB_FIL_FREQUENCIAAZUL | Texto | 99,2% | Frequência de viagens pela companhia, declarada pelo próprio Cliente |
| ESTATISTICA_ATRASOSAIDA | Numérico | 100% | Atraso registrado na partida, em minutos |
| VOO_INTERNACIONAL | Texto | 100% | Classificação do voo como Domestic ou International |
| SEGMENTO | Texto | 100% | Segmento comercial ao qual o Cliente pertence (Corporativo, Azul Viagens, Demais Clientes) |
| TEMPO_VOO | Numérico | 100% | Duração da viagem, em minutos |
| CANCELAMENTO_VOO | Booleano | 100% | Indicação de que houve cancelamento associado à reserva |
| ANTECEDENCIA_CANCELAMENTO | Numérico | 16,3% | Intervalo entre o cancelamento e a partida originalmente prevista, em dias |
 
**Nota sobre a qualidade e a estrutura dos dados**
 
A exploração inicial da base revelou características que condicionam diretamente as etapas de preparação de dados previstas na metodologia adotada.
 
A variável-alvo apresenta desbalanceamento moderado: 65,2% dos registros correspondem a Promotores, 14,5% a Neutros e 20,3% a Detratores. A classe de interesse é minoritária, o que exige atenção à escolha das métricas de avaliação, mas sua proporção permite trabalhar sem recorrer a estratégias agressivas de reamostragem.
 
As avaliações por etapa da jornada apresentam ausência estrutural, e não aleatória. Cada Cliente avalia apenas o que efetivamente vivenciou, de modo que o preenchimento varia de 84,0% no embarque a 0,3% no check-in por totem. Os quatro campos de check-in são mutuamente exclusivos, com apenas um deles preenchido por registro. Da mesma forma, as avaliações de atraso e de cancelamento só existem quando o evento ocorreu. A ausência, nesses casos, carrega informação sobre a jornada e será tratada como sinal, não como ruído a ser imputado.
 
Os campos `BASE_AIRPORTLEG` e `EQUIPAMENTO_PREFIXO` não descrevem um único voo. Aproximadamente 30% dos registros trazem valores concatenados que representam jornadas de múltiplos trechos, o que produz 8.746 combinações distintas de rota e 19.456 de aeronave, número muito superior ao tamanho real da frota. A decomposição desses campos em atributos derivados, como aeroporto de origem, aeroporto de destino final, quantidade de trechos e presença de conexão em hub, é condição para que o modelo capte padrões de rota e de equipamento.
 
Três inconsistências foram identificadas e serão tratadas na preparação dos dados. O campo `TEMPO_VOO` apresenta 1.241 registros com valores nulos ou negativos, incompatíveis com a duração de uma viagem. O campo `TIPO_ENTRETENIMENTO` contém treze categorias que se reduzem a sete após a padronização de grafias divergentes, como `eX1` e `EX1` ou `não possui entretenimento` e `Nao tem entretenimento`. Por fim, ainda que o campo `VOO_INTERNACIONAL` exista na estrutura, a amostra recebida contém exclusivamente voos domésticos, o que delimita o escopo de aplicação do modelo.

**b) Solução proposta**

A solução proposta é um modelo de classificação supervisionada capaz de estimar, para cada Cliente, a probabilidade de que sua experiência resulte em uma avaliação de detração. O modelo é treinado sobre o histórico de respostas de NPS combinado aos registros operacionais do voo, aprendendo a associar configurações de jornada a desfechos de insatisfação.

A Azul já opera um modelo preditivo de NPS em nível agregado, que projeta o comportamento semanal do indicador. O que a companhia não possui é a capacidade de descer ao nível do passageiro individual e responder quem, dentro de um conjunto de voos, tende a se tornar Detrator. É essa lacuna que a solução endereça.

Ao componente preditivo soma-se uma camada de interpretabilidade construída a partir da análise de importância de atributos do modelo treinado. Ela permite hierarquizar quais variáveis da jornada e da operação mais influenciam a probabilidade de detração, revelando quais etapas concentram o peso na formação da nota. O modelo, assim, não apenas ordena Clientes por risco, mas devolve à companhia um mapa dos pontos em que a experiência se deteriora.

O desenvolvimento será conduzido em Python, com a biblioteca pandas para manipulação e preparação dos dados, numpy para as operações numéricas e matplotlib para a construção dos gráficos de avaliação e de diagnóstico previstos nas entregas.

**c) Como a solução proposta deverá ser utilizada**
 
A aplicação prevista tem dois modos de operação complementares.
 
O primeiro é a pontuação individual de risco, executada no intervalo entre a realização do voo e a resposta à pesquisa. A companhia processa os voos de um período por meio da ingestão de um arquivo em formato CSV e recebe, como saída, a probabilidade de detração calculada para cada Cliente, com a respectiva faixa de risco. Como a pesquisa é enviada um dia após o voo e permanece aberta por sete dias, existe uma janela concreta em que a área de Customer Insights pode agir antes que a avaliação seja registrada. A priorização se apoia nessa lista para direcionar as ações de recuperação que a companhia já pratica, do contato personalizado dos Tripulantes ao tratamento diferenciado em solo. Essas ações se apoiam no princípio OPA, sigla para Observar, Perceber e Atender, método interno pelo qual os Tripulantes recebem autonomia para adaptar o atendimento ao contexto de cada passageiro em vez de seguir um roteiro padronizado. O modelo se acopla a esse processo ao indicar antecipadamente quais Clientes concentram maior risco, tornando a personalização mais dirigida.
 
O segundo modo é o diagnóstico agregado dos fatores de insatisfação. A hierarquia de importância dos atributos, combinada à análise da distribuição do risco por rota, tipo de operação, segmento e perfil de fidelidade, permite identificar onde a detração se concentra e quais condições a antecedem. Esse resultado alimenta a priorização de investimentos e iniciativas de melhoria, sustentando decisões que hoje dependem da análise manual de comentários e de indicadores agregados.
 
Os dois modos derivam do mesmo artefato. A entrega prevê código executável internamente pela Azul, com documentação que permita a continuidade do trabalho por profissionais que não participaram do desenvolvimento, e saída exportável para os fluxos já utilizados pela área.

**d) Benefícios trazidos pela solução proposta**
 
- Antecipação da identificação de Clientes insatisfeitos, substituindo um processo hoje reativo, que depende da resposta à pesquisa, por uma atuação preventiva dentro da janela em que ainda é possível intervir.
- Ampliação da cobertura da análise. O processo atual concentra o esforço manual dos analistas em Clientes de alto valor, enquanto o modelo pontua a totalidade dos registros processados.
- Priorização de melhorias operacionais com base em evidência quantitativa sobre o peso de cada etapa da jornada na formação da nota, incluindo limiares de atraso a partir dos quais o risco se eleva de forma relevante.
- Compreensão dos drivers específicos de cada segmento e perfil de fidelidade, permitindo que ações de recuperação sejam calibradas ao Cliente em vez de aplicadas de forma uniforme.
- Identificação de rotas e padrões operacionais sistematicamente associados à detração, subsidiando decisões de malha, alocação de equipamento e serviço de bordo.
- Melhor alocação do investimento em ações de recuperação, ao reduzir tanto o esforço direcionado a Clientes que já seriam Promotores quanto a ausência de ação junto a quem efetivamente detrataria.
- Redução do risco de acomodação de expectativa, uma vez que benefícios passam a ser concedidos com base em risco estimado e não de forma recorrente ao mesmo grupo de Clientes.

**e) Critérios de sucesso**
 
*Desempenho do modelo*
 
O erro de não identificar um Cliente que efetivamente detratará é mais custoso para a companhia do que o de acionar um Cliente que já seria Promotor, pois o primeiro implica perda de relacionamento e o segundo apenas gasto sem retorno. Por essa razão, a revocação na classe Detrator é adotada como métrica primária de avaliação.
 
- Revocação de no mínimo 0,70 na classe Detrator no conjunto de teste.
- ROC-AUC de no mínimo 0,75, demonstrando capacidade de ordenação de risco superior à referência aleatória.
- Precisão de no mínimo 0,40 na classe Detrator, o que representa aproximadamente o dobro da taxa de prevalência observada na base (20,3%) e assegura que a lista priorizada tenha densidade de risco suficiente para justificar a ação.
- F1-score reportado como métrica de equilíbrio, acompanhado da matriz de confusão e da curva Precision-Recall.
- Probabilidades calibradas, verificadas por curva de calibração, condição para que o corte de priorização seja definido em termos de negócio e não de forma arbitrária.
- Estabilidade do desempenho em validação temporal, com o modelo avaliado em período posterior ao de treino, dada a extensão de três anos da base e a presença de fatores sazonais e conjunturais no comportamento do indicador.

*Resultado de negócio*
 
Os patamares a seguir dependem de parâmetros que serão validados junto ao parceiro, entre eles o custo médio das ações de recuperação e o valor associado à retenção do Cliente.
 
- Redução de ao menos 10% na proporção de Detratores entre os Clientes submetidos a ação preventiva orientada pelo modelo, comparada ao grupo não priorizado.
- Elevação da taxa de conversão das ações de recuperação em relação à média histórica atualmente observada pela companhia.
- Redução do tempo entre a ocorrência do voo e a identificação do Cliente em risco, hoje condicionada à resposta à pesquisa.
- Adoção efetiva pela área de Customer Insights, evidenciada pela execução autônoma do modelo pela equipe da Azul ao término do projeto.
- Aderência integral aos requisitos de privacidade e proteção de dados estabelecidos pela LGPD e às restrições de compartilhamento definidas pela companhia.

*Retorno sobre o investimento*
 
Demonstração de retorno positivo em até doze meses após a entrada em operação, calculado pela comparação entre o custo das ações preventivas direcionadas pelo modelo e o valor preservado pela retenção dos Clientes recuperados. A quantificação depende dos parâmetros de custo e de valor de Cliente a serem fornecidos pela Azul.



#### 4.1.4. Value Proposition Canvas
```
Posicione aqui seu canvas.

Remova este bloco ao final
```

#### 4.1.5. Matriz de Riscos
```
Posicione aqui sua matriz.

Remova este bloco ao final
```

#### 4.1.6. Personas
```
Posicione aqui suas Personas (indique se são personas que utilizam o modelo e/ou se são afetadas pelo modelo).

Remova este bloco ao final
```

#### 4.1.7. Jornadas do Usuário
```
Posicione aqui seus mapas de jornadas do usuário que utiliza o modelo.

Remova este bloco ao final
```

#### 4.1.8 Política de Privacidade
```
Posicione aqui sua política de privacidade em acordo com a LGPD

Remova este bloco ao final
```

### 4.2. Compreensão dos Dados

#### 4.2.1. Exploração de dados
```
Apresentar a estatística descritiva básica de cada coluna, identificar se a coluna é numérica ou categórica e pelo menos 3 gráficos para visualizar a relação entre colunas escolhidas pelo grupo.

Remova este bloco ao final
```

#### 4.2.2. Pré-processamento dos dados
```
Apresentar quais foram as ações realizadas de limpeza (tratamento de missing values e remoção de outliers) e transformação (normalização e codificação) das colunas. Se houverem outliers, cite quais são e qual(is) correção(ões) será(ão) aplicada(s).

Remova este bloco ao final
```

#### 4.2.3. Hipóteses
```
Descreva três hipóteses sobre a relação dos dados e o problema. Justifique cada uma delas. 

Remova este bloco ao final
```

### 4.3. Preparação dos Dados e Modelagem
```
Caso seu projeto seja Modelo Supervisionado, apresentar: 
a) Organização dos dados (conjunto de treinamento, validação e testes)
b) Modelagem para o problema (proposta de features com a explicação completa da linha de raciocínio).
c) Métricas relacionadas ao modelo (pelo menos 3).
d) Apresentar o primeiro modelo candidato, e uma discussão sobre os resultados deste modelo (discussão sobre as métricas para esse modelo candidato).

Caso seu projeto seja Modelo Não-Supervisionado, apresentar:
a) Modelagem para o problema (proposta de features com a explicação completa da linha de raciocínio).
b) Primeiro modelo candidato para o problema.
c) Justificativa para a definição do K do modelo.
d) Escolha de um tipo de sistema de recomendação e a justificativa para essa escolha.

Remova este bloco ao final
```

### 4.4. Comparação de Modelos
```
- Descrever e justificar a escolha da métrica de avaliação dos modelos com base no que é mais importante para o problema ao 
  se medir a qualidade desses modelos;
- Descrever ao menos três modelos candidatos, seus respectivos algoritmos, seus tunings de hiperparâmetros e suas métricas 
  alcançadas;

Remova este bloco ao final
```

### 4.5. Avaliação
```
- Descreva a solução final de modelo preditivo e justifique a escolha. Alinhe sua justificativa com a Seção 4.1, resgatando o entendimento 
  do negócio e das personas, explicando de que formas seu modelo atende os requisitos e definições. 
- Descreva também um plano de contingência para os casos em que o modelo falhar em suas predições.
- Além disso, discuta sobre a explicabilidade do modelo (se aplicável) e realize a verificação de aceitação ou refutação das hipóteses.
- Se aplicável, utilize equações, tabelas e gráficos de visualização de dados para melhor ilustrar seus argumentos. 

Remova este bloco ao final
```

## <a name="c5"></a>5. Conclusões e Recomendações
```
Escreva, de forma resumida, sobre os principais resultados do seu projeto e faça recomendações formais ao seu parceiro de negócios em relação ao uso desse modelo. Você pode aproveitar este espaço para comentar sobre possíveis materiais extras, como um manual de usuário mais detalhado na seção “Anexos”. Não se esqueça também das pessoas que serão potencialmente afetadas pelas decisões do modelo preditivo e elabore recomendações que ajudem seu parceiro a tratá-las de maneira estratégica e ética. 

Remova este bloco ao final
```

## <a name="c6"></a>6. Referências
```
Incluir as principais referências de seu projeto, para que seu parceiro possa consultar caso ele se interessar em aprofundar. Não se esqueça de formatar as referências conforme a ABNT.

Remova este bloco ao final
```

## <a name="attachments"></a>Anexos
```
Utilize esta seção para anexar materiais como manuais de usuário, documentos complementares que ficaram grandes e não couberam no corpo do texto etc.

Remova este bloco ao final
```
