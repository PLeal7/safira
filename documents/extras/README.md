# Documentos complementares

Esta pasta guarda o material de apoio do projeto Safira, ou seja, o que não faz parte de
`documents/documentacao.md` mas precisa ficar versionado e localizável.

## Apresentações

Ficam em [`apresentacoes/`](apresentacoes), uma por sprint.

| Sprint | Arquivo | Conteúdo |
|---|---|---|
| Sprint 01 | [sprint-01.pdf](apresentacoes/sprint-01.pdf) | Sprint Review 1: entendimento do negócio, contexto de mercado, SWOT, 5 Forças de Porter, proposta de solução, personas e timeline das sprints |
| Sprint 02 | [sprint-02.pdf](apresentacoes/sprint-02.pdf) | Sprint Review 2: perfil da base de 484.915 respostas, viés de resposta e ponderação, tratamento de nulos e outliers, resultado das hipóteses H1 a H4, testes de normalidade, escolha das escalas de normalização e próximos passos |

## Outros documentos

| Documento | Conteúdo |
|---|---|
| [Hipóteses](Hipoteses.md) | Hipóteses levantadas e ainda não confirmadas, com tipo e status de validação |
| [Composição dos conjuntos](composicao-dos-conjuntos.md) | Tabela e figura da composição de treino/validação/teste, material de apoio do #132 para a redação do #116 |
| [Relatório de validação do corte de leakage](relatorio-validacao-leakage.md) | Resultado do #198 sobre a base dummy: datas de treino < validação < teste e nenhum `RESPONDENT_ID`/`ID_GOLDENRECORD` em dois conjuntos. Regerar com `python scripts/validar_leakage.py` |
| [Decisão sobre explicabilidade: por que não adotamos SHAP](decisao-explicabilidade-shap.md) | Registro da decisão do grupo de não usar SHAP na Seção 4.4, com a justificativa, o que se perde e as duas vias de explicabilidade entregues (#215) |
| [Parecer de reprodutibilidade dos interpretáveis](parecer-reprodutibilidade-interpretaveis.md) | Revisão cruzada da Seção 4.4.2 e dos notebooks da Regressão Logística e da Árvore de Decisão pelo #195: veredito de execução do zero, checklist técnico e conferência número a número |
| [Parecer de reprodutibilidade dos ensembles](parecer-reprodutibilidade-ensembles.md) | Revisão cruzada da Seção 4.4.4 e do `ensembles.ipynb` pelo #216: veredito de execução de ponta a ponta, conferência número a número e verificação do isolamento do teste e dos folds por Cliente |
| [Reprodutibilidade do notebook integrado](reprodutibilidade-notebook-integrado/relatorio-reprodutibilidade-base-real.md) | Duas execuções consecutivas de `notebooks/comparacao_modelos.ipynb` na base real, com a mesma semente: métricas idênticas, logs iguais linha a linha ([execução 1](reprodutibilidade-notebook-integrado/execucao-1.log), [execução 2](reprodutibilidade-notebook-integrado/execucao-2.log)) e variação máxima de 0%. Regerar com `NOTEBOOK_BASE_REAL=1 pytest tests/test_reprodutibilidade_notebook.py` |

## Convenções desta pasta

- Nome de pasta e de arquivo em minúsculas, sem acento e com hífen separando as palavras. O Git
  escapa caminho com acento na saída padrão, e o único arquivo acentuado do repositório já aparece
  como `"assets/instru\303\247\303\243o.txt"`, o que atrapalha script, link e `git add` pelo nome.
- Apresentação de sprint entra como `apresentacoes/sprint-NN.pdf`, em PDF e não em `.pptx`, porque o
  PDF abre no próprio GitLab e não depende da versão do editor de origem.
- Um arquivo novo aqui entra também na tabela correspondente acima, senão ele fica invisível para
  quem não abriu a pasta.
