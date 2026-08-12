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

**Contexto Setorial**

O mercado doméstico brasileiro é altamente concentrado em três principais companhias — LATAM, GOL e Azul. Em 2025, essas três companhias responderam, juntas, por praticamente todo o mercado doméstico de passageiros em RPK: 39,9% LATAM, 30,9% GOL e 29,1% Azul (ANAC, 2026, p. 62). A LATAM apresenta forte participação no mercado doméstico e ampla atuação nacional e internacional. A GOL possui forte participação no mercado doméstico e historicamente adotou uma estratégia orientada à eficiência operacional e à competitividade de custos, tendo iniciado processo de reestruturação financeira nos Estados Unidos (Chapter 11) em janeiro de 2024 e concluído o processo em junho de 2025 (G1, 2025). A Azul, a mais recente das três, se diferencia por capilaridade e experiência do cliente, sendo a companhia aérea brasileira com o maior número de cidades atendidas — aproximadamente 800 voos diários, mais de 130 destinos e a única companhia em cerca de 80% de suas rotas (AZUL S.A., 2026) —, competindo menos por preço e mais por alcance geográfico e diferenciação de produto. Ambas as concorrentes também passaram por processos de reestruturação financeira nos Estados Unidos, com a Azul concluindo o seu em fevereiro de 2026, após pouco mais de nove meses (FORBES, 2026).

A Azul se posiciona como a companhia de maior capilaridade do Brasil. Sua frota diversificada, composta por aeronaves ATR, Embraer E-Jets e Airbus, permite atuar em mercados de menor densidade que os concorrentes, que operam principalmente com aeronaves de maior porte, não conseguiriam explorar de forma rentável (AZUL S.A., 2026). Além da malha ampliada, a empresa aposta na diferenciação da experiência de bordo — entretenimento com TV ao vivo e opções de refeição pouco comuns no setor — como forma de fortalecer a diferenciação e a fidelização dos clientes, competindo menos por preço e mais por alcance geográfico e diferenciação de produto. A companhia também mantém unidades estratégicas de negócio complementares à operação aérea, como o programa de fidelidade Azul Fidelidade, a Azul Cargo e a Azul Viagens, e utiliza o NPS como indicador de satisfação do cliente, tendo registrado média de 38,5 em 2025 (AZUL S.A., 2026).

O setor aéreo brasileiro apresenta elevada complexidade operacional e exposição a ciclos de pressão financeira, associados, entre outros fatores, a custos elevados, volatilidade cambial, combustível, financiamento e restrições na cadeia de suprimentos. Ao mesmo tempo, o mercado doméstico segue em expansão estrutural: o tráfego doméstico brasileiro registrou o maior crescimento em RPK entre os mercados domésticos analisados pela IATA em 2025, com alta de 11,1% sobre 2024 (IATA, 2026). Além dos requisitos de capital e infraestrutura, a atividade é submetida a requisitos regulatórios e operacionais rigorosos, aumentando as barreiras à entrada de novos concorrentes. Some-se a isso a escassez global de aeronaves — a carteira de pedidos ultrapassou 17 mil unidades, equivalente a quase 60% da frota ativa mundial, com déficit acumulado de pelo menos 5.300 entregas nos últimos cinco anos (ENCHIOGLO, 2025) —, que eleva o poder de barganha dos fabricantes (Boeing, Airbus, Embraer), limita a capacidade das companhias de expandir oferta rapidamente e, aliada à necessidade de capital intensivo e escala para negociar com os fabricantes, justifica a barreira de entrada alta do setor — o que favorece a Azul e suas competidoras, já que não precisarão se preocupar com a ameaça de novos entrantes. Soma-se ainda o crescimento do mercado internacional, com disputa acirrada por rotas estratégicas (como Brasil-EUA) via expansão de rede e parcerias como a joint venture Latam-Delta.

**5 Forças de Porter**

![5 Forças de Porter](assets/5-forcas.png)<br>
Imagem 1: 5 Forças de Porter - Produção autoral

**Poder de barganha dos fornecedores: Alto**<br>
As companhias aéreas dependem de uma cadeia de fornecedores altamente especializada e concentrada, incluindo fabricantes de aeronaves (Boeing, Airbus e a nacional Embraer), motores, componentes, serviços de manutenção e empresas de leasing. As restrições atuais da cadeia de suprimentos, somadas ao elevado tempo necessário para substituição ou expansão de frota, aumentam o poder de barganha desses fornecedores. O backlog global de aeronaves ultrapassou 17 mil unidades, e os atrasos de entregas e componentes têm elevado custos de leasing, manutenção e operação das companhias aéreas (IATA apud ENCHIOGLO, 2025). A escassez de insumos para fabricação, intensificada após a pandemia, também eleva os custos de produção repassados às companhias aéreas (TAMIOZZO, 2026), reforçando a dependência tecnológica e o alto custo de troca desse elo da cadeia.

**Poder de barganha dos clientes: Moderado**<br>
Em rotas com múltiplas companhias, o passageiro possui maior poder de barganha, pois pode comparar preços, horários e condições e trocar de fornecedor com relativa facilidade. Entretanto, esse poder é reduzido nas rotas de menor densidade atendidas exclusiva ou predominantemente pela Azul, bem como pelos mecanismos de fidelização e diferenciação da companhia — a Azul afirma ser a única companhia em aproximadamente 80% de suas rotas (AZUL S.A., 2026). Dessa forma, o poder de barganha dos clientes é classificado como moderado.

**Rivalidade entre concorrentes: Alta**<br>
O mercado doméstico é altamente concentrado em três companhias — LATAM, GOL e Azul —, que disputam passageiros e slots por meio de preço, frequência de voos e rotas. O setor aéreo é caracterizado por elevados custos fixos e capacidade perecível — um assento vazio em um voo que já partiu não pode ser vendido posteriormente —, o que intensifica a pressão por ocupação e aperta as margens das companhias. Essa dinâmica ajuda a explicar por que LATAM, GOL e Azul passaram por processos de reestruturação financeira nos Estados Unidos (Chapter 11) em diferentes momentos, com a GOL concluindo o processo em 2025 (MAGALHAES, Luciana Novaes) e a Azul em fevereiro de 2026 (SABÓIA, Gabriel).

**Ameaça de produtos substitutos: Baixa/Moderada**<br>
O transporte rodoviário permanece como principal alternativa ao transporte aéreo em diversos trajetos, especialmente em viagens curtas e médias, devido ao menor custo e à ampla disponibilidade de rotas. Entretanto, o tempo significativamente maior de deslocamento reduz sua capacidade de substituir o transporte aéreo em viagens de maior distância ou para passageiros com maior sensibilidade ao tempo. Além disso, a capilaridade da Azul e sua atuação em mercados de menor densidade reduzem a disponibilidade de alternativas em determinadas rotas. Dessa forma, a ameaça de substitutos é classificada como baixa a moderada.

**Ameaça de novos entrantes: Baixa**<br>
A entrada de novos concorrentes no transporte aéreo regular brasileiro apresenta barreiras elevadas. A atividade exige elevado investimento em aeronaves, manutenção, tecnologia, pessoal e infraestrutura, além de certificação e atendimento a requisitos regulatórios estabelecidos pela ANAC [CITAÇÃO NECESSÁRIA — processo de certificação ANAC]. A entrada também é dificultada pelo acesso limitado à infraestrutura aeroportuária, especialmente em aeroportos coordenados, nos quais a disponibilidade de slots é restrita [CITAÇÃO NECESSÁRIA — alocação de slots ANAC]. Somam-se a essas barreiras as economias de escala, a necessidade de construir uma rede de rotas, marca, canais de distribuição e programas de fidelidade. Dessa forma, a ameaça de novos entrantes é classificada como baixa.

#### 4.1.2. Análise SWOT 
```
Posicione aqui sua análise SWOT.

Remova este bloco ao final
```

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

CAVALCANTI, Glauce. Avião supera ônibus em viagens no país pela 1a vez desde 2020. Disponível em: <https://oglobo.globo.com/economia/noticia/2025/10/02/aviao-supera-onibus-em-viagens-no-pais-pela-1a-vez-desde-2020.ghtml>. Acesso em: 5 ago. 2026.

INTERNATIONAL AIR TRANSPORT ASSOCIATION (IATA). Strong 2025 Passenger Demand Masks Ongoing Capacity Constraints. Geneva: IATA, 29 jan. 2026. Disponível em: https://www.iata.org/en/pressroom/2026-releases/2026-01-29-02/. Acesso em: 11 ago. 2026.

AGÊNCIA NACIONAL DE AVIAÇÃO CIVIL (ANAC). Anuário do Transporte Aéreo 2025. Brasília: ANAC, 2026. p. 62.

MARQUES, Vinícius. Brasil é o único grande mercado doméstico de aviação a crescer em junho; demanda global recua, diz IATA. Disponível em: <https://timesbrasil.com.br/empresas-e-negocios/aviacao/brasil-e-o-unico-grande-mercado-domestico-de-aviacao-a-crescer-em-junho-demanda-global-recua-diz-iata/>. Acesso em: 5 ago. 2026.

AZUL S.A. Por que investir na Azul? Relações com Investidores Azul, [2026]. Disponível em: https://ri.voeazul.com.br/a-azul/por-que-investir-na-azul/. Acesso em: 11 ago. 2026.


MAGALHAES, Luciana Novaes. Gol exits Chapter 11 with plans to add new routes and expand fleet. Disponível em: <https://www.reuters.com/world/americas/gol-exits-chapter-11-with-plans-add-new-routes-expand-fleet-2025-06-06/>. Acesso em: 11 ago. 2026.

SABÓIA, Gabriel. Azul anuncia a saída do processo de recuperação judicial nos Estados Unidos Leia mais em: https://veja.abril.com.br/economia/azul-anuncia-a-saida-do-processo-de-recuperacao-judicial-nos-estados-unidos/. Disponível em: <https://veja.abril.com.br/economia/azul-anuncia-a-saida-do-processo-de-recuperacao-judicial-nos-estados-unidos/>. Acesso em: 11 ago. 2026.


TAMIOZZO, Mateus. Por que faltam aviões para as companhias aéreas e como isso prejudica a sua viagem? Disponível em: <https://www.melhoresdestinos.com.br/falta-de-avioes.html>. Acesso em: 4 ago. 2026.


Pesquisa do IBGE revela mudança nos meios de transporte: avião supera ônibus pela primeira vez. YouTube, 2025. 1 vídeo (5:28). Disponível em: https://www.youtube.com/watch?v=jiSMLAnPCaQ. Acesso em: 05/08/2026.


Por que as Companhias Aéreas Brasileiras dão tanto PREJUÍZO? | Curioso Explica. YouTube, 2026. 1 vídeo (11:30). Disponível em: https://www.youtube.com/watch?v=hwI6NVrZGig. Acesso em: 05/08/2026.

## <a name="attachments"></a>Anexos
```
Utilize esta seção para anexar materiais como manuais de usuário, documentos complementares que ficaram grandes e não couberam no corpo do texto etc.

Remova este bloco ao final
```
