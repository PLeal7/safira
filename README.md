# Inteli - Instituto de Tecnologia e Liderança 

<p align="center">
<a href= "https://www.inteli.edu.br/"><img src="assets/inteli.png" alt="Inteli - Instituto de Tecnologia e Liderança" border="0"></a>
</p>

# Safira

## Avatares

## :student: Integrantes: 
- <a href="https://www.linkedin.com/in/arthur-proen%C3%A7a-87522b355">Arthur Augusto Proença Gonçalves</a>
- <a href="https://www.linkedin.com/in/cassio-reis-costa-0989803b9/">Cassio Reis Costa</a>
- <a href="https://www.linkedin.com/in/felipe-menossi-estrada/">Felipe Menossi Estrada</a>
- <a href="https://www.linkedin.com/in/fernanda-steiner-938806313/">Fernanda Jawetz Steiner</a>
- <a href="https://www.linkedin.com/in/gabriel-gomes-pimentel/">Gabriel Gomes Pimentel</a>
- <a href="https://www.linkedin.com/in/kaylan-alexandre/">Kaylan Alexandre de Paula Sathler</a>
- <a href="https://www.linkedin.com/in/luiza-chaccur-de-cresci-450015397/">Luiza Chaccur de Cresci</a>
- <a href="https://www.linkedin.com/in/pedro-leal-5b8788341/">Pedro Estellita Leal</a>

## :teacher: Professores:
### Orientador(a) 
- <a href="https://www.linkedin.com/in/marcelo-gon%C3%A7alves-phd/">Marcelo Gonçalves</a>
### Instrutores
- <a href="https://www.linkedin.com/in/zotovici/">Andréa Zotovici</a>
- <a href="https://www.linkedin.com/in/bruna-mayer/">Bruna Mayer Costa</a>
- <a href="https://www.linkedin.com/in/camilanarantes/">Camila Naves Arantes</a>
- <a href="https://www.linkedin.com/in/leandromundim/">Leandro Resende Mundim</a>
- <a href="https://www.linkedin.com/in/natalia-k-37a62052/">Natalia Kloeckner</a>


## 📝 Descrição

O **Safira** é o modelo preditivo que o G01 desenvolve com a Azul Linhas Aéreas para antecipar a detração de Clientes antes da resposta à pesquisa de NPS.

Hoje a companhia só sabe quem detratou depois que a nota foi dada. A pesquisa chega um dia após o voo, para metade dos Clientes domésticos, e fica aberta por sete dias. É nesse intervalo que ainda seria possível reverter uma experiência ruim, mas a área de Experiência do Cliente atua sem critério objetivo de priorização: trata algumas centenas de casos por dia, enquanto um único fim de semana de mau tempo afeta milhares de passageiros. Quando o Detrator aparece no indicador, a informação já deixou de ser acionável.

A solução proposta é um modelo de classificação que estima, para cada jornada encerrada, a probabilidade de o Cliente se tornar Detrator, usando apenas dados operacionais e de perfil disponíveis antes da resposta à pesquisa. A saída tem dois usos complementares: a **pontuação individual de risco**, que ordena a lista de contato da equipe de Experiência do Cliente dentro da janela em que a recuperação ainda é possível, e o **diagnóstico agregado**, que hierarquiza os fatores de insatisfação e orienta onde investir em melhoria operacional.

A base analisada reúne 484.915 respostas de 36 meses de operação doméstica, de julho de 2023 a junho de 2026, integradas pela chave `RESPONDENT_ID` às informações de voo e ao perfil do Cliente. A exploração dos dados, o pré-processamento e as hipóteses testadas estão na seção 4.2 da documentação e nos notebooks deste repositório. O modelo preditivo em si é construído a partir da Sprint 3.

<b>Link para vídeo demonstrativo:</b> será adicionado na entrega final do projeto.

## 📁 Estrutura de pastas

Dentre os arquivos presentes na raiz do projeto, definem-se:

- <b>readme.md</b>: arquivo que serve como guia e explicação geral sobre o projeto (o mesmo que você está lendo agora).

- <b>assets</b>: todas as imagens e mídias utilizadas nos notebooks e documentação são posicionadas aqui.

- <b>documents</b>: aqui estarão todos os documentos do projeto. Há também uma pasta denominada <b>extras</b> onde estão presentes documentos complementares, entre eles as apresentações de sprint. O índice dessa pasta está em <a href="documents/extras/README.md">documents/extras</a>.

- <b>notebooks</b>: todos os Jupyter Notebooks criados para desenvolvimento do projeto.

- <b>src</b>: módulos Python importados pelos notebooks, do dado à métrica: integração e limpeza das bases, estatística descritiva, figuras, particionamento e congelamento dos conjuntos, matriz do modelo, pipelines e espaços de busca dos modelos, avaliação, calibração e explicabilidade. É a implementação canônica: os notebooks importam essas funções em vez de reimplementá-las.

- <b>scripts</b>: o módulo `preprocessamento_nps.py`, que define o contrato do score pós-viagem (allowlist do Feature Set V1, derivação de `N_TRECHOS`, validação de schema e preparação da base analítica), documentado nas Seções 4.2.2 a 4.3.2.5 de [documents/documentacao.md](documents/documentacao.md), e utilitários executados pela linha de comando, como `gerar_dummy.py`, que gera a base sintética usada nos testes.

- <b>tests</b>: testes automatizados executáveis com `pytest`, sem dependência das bases do parceiro: cobrem as travas de integridade, o contrato de dados, o particionamento e os módulos de modelagem, e executam o notebook integrado sobre a base sintética.

A divisão entre `src/` e `scripts/` é histórica, e não por tipo de código: os dois guardam módulos importáveis, e os testes de `tests/` colocam ambos no caminho de importação. O grupo optou por não mover arquivos entre as pastas nesta etapa, porque notebooks, testes e documentação referenciam os caminhos atuais.

## 💻 Execução dos projetos

### Bases de dados

As bases fornecidas pela Azul **não são versionadas neste repositório**, conforme o Termo de Abertura de Projeto de Inovação, que veda a publicação de dados do parceiro. Os diretórios `data/` e `dados/` estão no `.gitignore`, assim como qualquer arquivo `.csv`, `.pkl` ou `.parquet`.

Para executar os notebooks é preciso obter os cinco arquivos com o grupo e colocá-los em uma pasta local:

```
PROJETO_INTELI.NPS_01.csv ... NPS_04.csv
PROJETO_INTELI.PERFIL_CLIENTE_01.csv e _02.csv
PROJETO_INTELI.INFORMACAO_VIAGEM.csv
PROJETO_INTELI.DISTRIBUICAO_PAX_NORMALIZADO.csv
```

### Localmente (VS Code com Python)

Requer Python 3.10 ou superior.

```bash
python -m venv .venv
.venv/Scripts/activate      # no Linux ou macOS: source .venv/bin/activate
pip install -r requirements.txt
jupyter lab notebooks/exploracao_dados.ipynb
```

O notebook localiza a raiz do projeto sozinho, subindo a árvore de diretórios até encontrar `src/`. Por padrão ele procura as bases em `dados/` na raiz; se elas estiverem em outro lugar, ajuste `CAMINHO_DADOS` na célula de configuração. Depois basta executar todas as células na ordem: as figuras são geradas como saída das próprias células e gravadas em `figuras/`.

Os módulos de `src/` também podem ser executados isoladamente, apontando o diretório das bases por variável de ambiente:

```bash
SAFIRA_DATA_DIR=/caminho/para/dados python src/clean.py
```

### Reprodução dos conjuntos de treino, validação e teste

Os cards de modelagem da Seção 4.3 comparam métricas entre si, e isso só faz sentido se todos rodarem sobre exatamente as mesmas partições. A divisão é temporal e por Cliente, portanto determinística — mas determinismo não basta: uma base analítica regerada com uma linha a mais produziria outros conjuntos sem aviso. Por isso a divisão é **congelada** num artefato de índices.

O artefato é gerado na primeira execução da seção 1.5 de `notebooks/modelagem.ipynb` e reutilizado em todas as seguintes:

```
data/processed/particoes_modelagem.json
```

Ele fica sob `data/`, coberto pelo `.gitignore`, e **não é versionado**: índices são posições de linhas de uma base do parceiro. Cada pessoa gera o seu localmente, e o hash é o que prova que todos chegaram ao mesmo lugar.

Para reproduzir os conjuntos do zero numa pasta limpa:

```bash
git clone <url-do-repositorio> && cd g01
python -m venv .venv && .venv/Scripts/activate
pip install -r requirements.txt
jupyter nbconvert --execute --to notebook --output-dir=.execucao notebooks/pre-processamento.ipynb
jupyter nbconvert --execute --to notebook --output-dir=.execucao notebooks/modelagem.ipynb
```

O primeiro notebook grava `data/processed/base_analitica.parquet`; o segundo cria o artefato de índices e imprime, na seção 1.5, a semente fixada, a impressão digital da base de origem, as datas de corte e o hash dos índices. Compare esse hash com o de outra pessoa: iguais, as partições são as mesmas.

Para conferir que o congelamento se mantém, apague o artefato e reexecute a seção 1.4 seguida da 1.5 — o hash impresso tem de ser o mesmo:

```bash
rm data/processed/particoes_modelagem.json
```

A conferência recusa, com erro explícito, um artefato editado à mão, gerado sobre outra versão da base, com outras datas de corte, ou partições que não sejam as congeladas. Mudar a política de particionamento é decisão registrada na Seção 4.3, não efeito colateral de uma execução: exige passar `regerar=True` a `congelar_ou_conferir`.

A divisão em si não é refeita aqui. Ela acontece uma única vez, na seção 1.4, dentro de `matriz.preparar_matriz`; a seção 1.5 apenas congela o que a 1.4 produziu e, nas execuções seguintes, confere que nada mudou. `congelamento.obter_particoes` continua disponível para quem precisar das partições fora do notebook, sem montar a matriz.

### Verificação automatizada

O notebook é versionado **sem saídas de célula**, por proteção dos dados do parceiro. Isso significa que o arquivo no repositório não é evidência de que ele executa. Dois comandos suprem essa lacuna.

**Testes das travas de integridade.** Não dependem das bases da Azul: usam dados sintéticos e rodam em menos de um segundo.

```bash
pytest -v
```

Cobrem o que precisa falhar quando deve: duplicata com conteúdo divergente, cobertura incompleta da chave antes da junção, violação da cardinalidade 1:1, `ID_GOLDENRECORD` divergente entre tabelas, e estrato de pós-estratificação sem contrapartida populacional. Cobrem também a partição temporal por Cliente: nenhum Cliente nos dois conjuntos e exclusão registrada em log dos registros sem `ID_GOLDENRECORD`.

**Execução de ponta a ponta do notebook.** Requer as bases em `dados/`. Termina com código de saída zero apenas se todas as células executarem sem erro.

```bash
jupyter nbconvert --execute --to notebook --output-dir=.execucao notebooks/exploracao_dados.ipynb
```

O notebook executado, com as saídas, fica em `.execucao/`, e as sete figuras em `figuras/`. Ambos os diretórios estão no `.gitignore`: a execução serve para verificar, não para versionar saídas que contenham dados do parceiro.

Para levar as figuras à documentação, copie os PNGs de `figuras/` para `assets/`, preservando os nomes.

### No Google Colab

1. Faça upload do notebook `notebooks/exploracao_dados.ipynb` para o Colab.
2. Coloque os cinco arquivos em uma pasta do seu Google Drive.
3. Na célula de configuração, descomente as linhas de montagem do Drive e ajuste `CAMINHO_DADOS` para o caminho da pasta.
4. Execute todas as células com `Ambiente de execução > Executar tudo`.

> Se o utilizador não salvar uma cópia do notebook no seu Google Drive próprio, não será possível salvar as alterações realizadas no arquivo.

## 🗃 Histórico de lançamentos

* 1.0.0 - 11/10/2024
    * [sprint 5] Lançamento da primeira versão do modelo preditivo com documentação.
* 0.6.0 - 27/09/2024
    * [sprint 4] Comparação de modelos preditivos
* 0.3.1 - 13/09/2024
    * [sprint 3] Preparação de dados e modelo preditivo preliminar
* 0.2.7 - 30/08/2024
    * [sprint 2] Análise exploratória e levantamento de hipóteses
* 0.1.3 - 16/08/2024
    * [sprint 1] Documentação de entendimento do negócio

## 📋 Licença/License

<img style="height:22px!important;margin-left:3px;vertical-align:text-bottom;" src="https://mirrors.creativecommons.org/presskit/icons/cc.svg?ref=chooser-v1"><img style="height:22px!important;margin-left:3px;vertical-align:text-bottom;" src="https://mirrors.creativecommons.org/presskit/icons/by.svg?ref=chooser-v1"><p xmlns:cc="http://creativecommons.org/ns#" xmlns:dct="http://purl.org/dc/terms/"><a property="dct:title" rel="cc:attributionURL" href="https://github.dev/Intelihub/Template_M3">MODELO GIT INTELI</a> by Inteli is licensed under <a href="http://creativecommons.org/licenses/by/4.0/?ref=chooser-v1" target="_blank" rel="license noopener noreferrer" style="display:inline-block;">Attribution 4.0 International</a>.</p>
