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
Fernanda Ribeiro é Analista de Customer Insights e atua como utilizadora direta do modelo. Atualmente, ela é responsável por receber o volume diário de respostas da pesquisa de NPS e realizar a classificação dos passageiros em Promotores, Neutros e Detratores de forma manual, o que torna o processo reativo e trabalhoso, já que a identificação de um detrator só ocorre depois que a nota já foi dada. Com a implementação do modelo, Fernanda passará a utilizá-lo diretamente em sua rotina para antecipar a probabilidade de detração e identificar os principais fatores que influenciam uma nota baixa, tornando a análise mais rápida, organizada e menos dependente de esforço manual. Por isso, ela é considerada uma persona que utiliza o modelo.

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
