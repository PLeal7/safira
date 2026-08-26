# Documentos complementares

Esta pasta guarda o material de apoio do projeto Safira, ou seja, o que não faz parte de
`documents/documentacao.md` mas precisa ficar versionado e localizável.

## Apresentações

Ficam em [`apresentacoes/`](apresentacoes), uma por sprint.

| Sprint | Arquivo | Conteúdo |
|---|---|---|
| Sprint 01 | [apresentacoes/sprint-01.pdf](apresentacoes/sprint-01.pdf) | Sprint Review 1: entendimento do negócio, contexto de mercado, SWOT, 5 Forças de Porter, proposta de solução, personas e timeline das sprints |

## Outros documentos

| Arquivo | Conteúdo |
|---|---|
| [Hipoteses.md](Hipoteses.md) | Hipóteses levantadas e ainda não confirmadas, com tipo e status de validação |

## Convenções desta pasta

- Nome de pasta e de arquivo em minúsculas, sem acento e com hífen separando as palavras. O Git
  escapa caminho com acento na saída padrão, e `assets/instrução.txt` já aparece no repositório como
  `"assets/instru\303\247\303\243o.txt"`, o que atrapalha script, link e `git add` pelo nome.
- Apresentação de sprint entra como `apresentacoes/sprint-NN.pdf`, em PDF e não em `.pptx`, porque o
  PDF abre no próprio GitLab e não depende da versão do editor de origem.
- Um arquivo novo aqui entra também na tabela correspondente acima, senão ele fica invisível para
  quem não abriu a pasta.
