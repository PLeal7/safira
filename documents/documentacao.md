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


## <a name="c1"></a>1. Introdução
```
Apresente de forma sucinta o parceiro de negócio, seu porte, local, área de atuação e posicionamento no mercado. Maiores detalhes deverão ser descritos na seção 4. Descreva resumidamente o problema a ser resolvido (sem ainda mencionar a solução). 

Remova este bloco ao final
```

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
- A matriz SWOT é uma ferramenta de diagnóstico estratégico dividida em quatro quadrantes: Forças e Fraquezas, que são fatores internos da organização e estão sob seu controle, e Oportunidades e Ameaças, que são fatores externos do mercado e não dependem diretamente da organização.

- As Forças são os pontos em que a organização já se destaca, como recursos, competências ou processos bem estabelecidos. As Fraquezas são as limitações internas que ainda pesam contra ela, como falhas de processo, dados incompletos ou dependências não resolvidas. Já as Oportunidades são condições externas favoráveis que a organização pode aproveitar, como tendências de mercado ou brechas deixadas pela concorrência, enquanto as Ameaças são riscos externos que fogem do seu controle, como mudanças regulatórias, movimentos da concorrência ou instabilidade econômica.

- A ideia é cruzar esses dois eixos, interno e externo, favorável e desfavorável, para dar uma visão organizada da situação de um projeto, produto ou empresa em determinado momento. Esse diagnóstico serve de base para decisões estratégicas antes de partir para a definição de soluções, ajudando a identificar onde investir, o que corrigir e quais riscos monitorar de perto.

<div align="center">
  <sub>Análise SWOT</sub><br>
  <img src="../assets/analise_swot.png" width="100%" alt="Análise SWOT"><br>
  <sup>Fonte: Autoria própria.</sup>
</div>

**Texto Analítico**

**Critério de classificação escolhido pelo grupo**

A matriz se organiza em dois eixos: interno ou externo, e favorável ou desfavorável. O teste aplicado para o primeiro eixo foi a capacidade de decisão da companhia. Se a Azul pode alterar o fator por decisão própria, ele é interno; se apenas reage a ele, é externo.

Esse critério explica duas escolhas que poderiam gerar dúvida. A saída do Chapter 11 foi classificada como força, e não oportunidade, porque decorre de reestruturação conduzida pela própria empresa e se materializa no balanço (Azul S.A., 2026b). Já a entrada de United e American no capital é oportunidade, pois depende de decisão de terceiros e de aprovação regulatória (Conselho Administrativo de Defesa Econômica [CADE], 2026).

**Forças**

Descrevem capacidades próprias da companhia. A malha capilar, com 132 destinos domésticos e cerca de 800 voos diários, é o ativo central, já que a exclusividade em parte das rotas regionais reduz a pressão sobre tarifas (Azul S.A., 2026a). A frota compatível com esse modelo é a condição técnica que a viabiliza, existindo relação de causa entre os dois pontos (Azul S.A., 2026a). A reestruturação concluída entra como força por se traduzir em indicadores internos de balanço: dívida bruta de R$ 34,6 bi para R$ 20,6 bi, alavancagem de 2,4x e liquidez de R$ 4,7 bi (Azul S.A., 2026b, 2026c). A pontualidade, com a quarta colocação mundial em 2025, resulta de gestão operacional (Cirium, 2026). A diversificação de receita, via fidelidade com 20 milhões de clientes (Azul Fidelidade, 2026) e logística em 96% dos municípios (Azul Logística, 2026), reduz a dependência da venda de passagens.

**Fraquezas**

Foram escolhidas de modo a não apenas espelhar o inverso das forças. A terceira posição no mercado doméstico, com 28,6% no primeiro semestre de 2026, limita a diluição de custos fixos (Agência Nacional de Aviação Civil [ANAC], 2026b). A complexidade de sete tipos de aeronave é o contraponto direto da segunda força: a diversidade que viabiliza a malha encarece manutenção, peças e treinamento (Azul S.A., 2026a). As 52 aeronaves fora de operação imobilizam capital sem receita (Azul S.A., 2026b). A estrutura de custos dolarizada foi mantida como interna porque resulta do modelo de financiamento adotado, ainda que a cotação da moeda seja externa (Azul S.A., 2026c). A diluição acionária é a contrapartida negativa da recuperação do balanço (InfoMoney, 2026).

**Oportunidades**

Reúnem movimentos externos que a companhia pode capturar. A entrada de United e American, com cerca de 8% cada e assento no conselho, fornece o canal internacional (CADE, 2026; Azul S.A., 2026b), enquanto a expansão do mercado internacional brasileiro, com 15 milhões de passageiros no primeiro semestre de 2026, fornece a demanda (ANAC, 2026a). As duas se reforçam. O crescimento do e-commerce sustenta o plano de triplicar a capacidade de cargas até 2027, dialogando com a força da diversificação (Azul Logística, 2026). A postergação das tarifas de navegação aérea é decisão de política pública que melhora o fluxo de caixa. A baixa concorrência nas rotas regionais é condição de mercado, não atributo da empresa, o que justifica sua posição neste quadrante (ANAC, 2026b).

**Ameaças**

O quadrante foi consolidado para evitar redundância. Combustível e câmbio, antes separados, foram unificados, pois o querosene responde por cerca de 45% dos custos do setor e é reajustado com base no dólar (Associação Brasileira das Empresas Aéreas [ABEAR], 2026; Petrobras, 2026). A desaceleração da demanda, que recuou de dois dígitos no início de 2026 para praticamente estabilidade em junho, limita o repasse de custos via tarifa (ANAC, 2026a). A concorrência de Latam e Gol, somando mais de 70% do mercado, articula-se com a fraqueza de escala (ANAC, 2026b). O custo estruturalmente mais alto do combustível no Brasil é risco distinto da volatilidade, por tratar de nível de preço e não de oscilação (ABEAR, 2026). A dependência de infraestrutura e tarifas reguladas completa o quadrante como risco institucional (ANAC, 2026b).

**Conexões SWOT**

Três tensões organizam a leitura. A primeira é que malha capilar e complexidade de frota têm a mesma origem, de modo que a vantagem competitiva carrega seu próprio custo. A segunda é que a recomposição do balanço é justamente o que torna acessíveis a expansão internacional, a retomada regional e o crescimento de cargas, tendo como contrapartida a diluição acionária. A terceira é que a menor escala se torna mais crítica em um mercado que deixou de crescer aceleradamente, pois a disputa passa a ocorrer por participação.

**Síntese**

A Azul apresenta vantagem competitiva defensável, sustentada pela capilaridade da malha e pela reputação operacional, mas opera com margem financeira estreita e alta exposição a custos externos. A prioridade estratégica é usar o fôlego da reestruturação e a conectividade dos parceiros internacionais para proteger o ativo regional, avançando na logística para reduzir a sensibilidade a combustível, câmbio e ciclo da demanda doméstica.

#### 4.1.3. Planejamento Geral da Solução
```
a) quais os dados disponíveis (fonte e conteúdo - exemplo: dados da área de Compras da empresa descrevendo seus fornecedores).
b) qual a solução proposta (pode ser um resumo do texto da Seção 2.2).
c) como a solução proposta deverá ser utilizada.
d) quais os benefícios trazidos pela solução proposta.
e) qual será o critério de sucesso.

Remova este bloco ao final
```

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
**Análise SWOT (Seção 4.1.2)**

Agência Nacional de Aviação Civil. (2026a, 30 de julho). *Transporte aéreo movimenta 65,2 milhões de passageiros no 1º semestre*. Pontos pra Voar. https://pontospravoar.com/transporte-aereo-movimenta-652-milhoes-de-passageiros-no-1o-semestre/

Agência Nacional de Aviação Civil. (2026b). *Painel de indicadores do transporte aéreo*. https://www.gov.br/anac/pt-br/assuntos/dados-e-estatisticas/mercado-do-transporte-aereo/painel-de-indicadores-do-transporte-aereo

Associação Brasileira das Empresas Aéreas. (2026, 1 de julho). *Querosene de aviação tem corte de 14,5% no preço praticado pela Petrobras a partir de julho*. Mixvale. https://www.mixvale.com.br/2026/07/01/querosene-de-aviacao-tem-corte-de-145-no-preco-praticado-pela-petrobras-a-partir-de-julho/

Azul Fidelidade. (2026, 25 de maio). *Azul Fidelidade supera 20 milhões de clientes e dobrou de tamanho em cinco anos*. Brasilturis. https://brasilturis.com.br/2026/05/25/azul-fidelidade-supera-20-milhoes-de-clientes-e-dobrou-de-tamanho-em-cinco-anos/

Azul Logística. (2026). *Azul Logística amplia operação multimodal e triplica frota cargueira até 2027*. Logweb. https://logweb.com.br/azul-logistica-amplia-operacao-multimodal-e-triplica-frota-cargueira-ate-2027/

Azul S.A. (2026a, 17 de junho). *Com 30 mil voos por mês, Azul aposta em expansão operacional*. Brasilturis. https://brasilturis.com.br/2026/06/17/com-30-mil-voos-por-mes-azul-aposta-em-expansao-operacional/

Azul S.A. (2026b, 18 de fevereiro). *Form 6-K*. Securities and Exchange Commission. https://www.sec.gov/Archives/edgar/data/1432364/000129281426000396/azul20260218_6k.htm

Azul S.A. (2026c, maio). *Resultados do 1º trimestre de 2026*. VoeNews. https://voenews.com.br/azul-registra-resultados-expressivos-no-1o-trimestre-de-2026-com-receita-de-r-55-bilhoes-ebitda-de-r-17-bilhao-e-avanco-no-plano-de-rentabilidade/

Cirium. (2026, janeiro). *On-Time Performance Review 2025*. Panrotas. https://www.panrotas.com.br/aviacao/empresas/2026/01/azul-e-latam-estao-entre-as-companhias-aereas-mais-pontuais-do-mundo-em-2025-veja-ranking_224723.html

Conselho Administrativo de Defesa Econômica. (2026, 3 de agosto). *Cade aprova sem restrições operação entre Azul e American Airlines*. Brasilturis. https://brasilturis.com.br/2026/08/03/cade-aprova-sem-restricoes-operacao-entre-azul-e-american-airlines/

InfoMoney. (2026). *Azul atualiza plano, mostra melhora, mas previsão de forte diluição impede otimismo*. https://www.infomoney.com.br/mercados/azul-atualiza-plano-mostra-melhora-mas-previsao-de-forte-diluicao-impede-otimismo/

Petrobras. (2026, junho). *Petrobras reduz preço do querosene de aviação em 14,2%*. Agência Brasil. https://agenciabrasil.ebc.com.br/economia/noticia/2026-06/petrobras-reduz-preco-do-querosene-de-aviacao-em-142

## <a name="attachments"></a>Anexos
```
Utilize esta seção para anexar materiais como manuais de usuário, documentos complementares que ficaram grandes e não couberam no corpo do texto etc.

Remova este bloco ao final
```
