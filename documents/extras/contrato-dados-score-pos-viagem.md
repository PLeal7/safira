# Contrato de Dados do Score Pos-Viagem

## Finalidade

Este documento fixa o contrato da base analitica usada pelo score pos-viagem do SAFIRA. O contrato e executavel em `scripts/preprocessamento_nps.py` e e validado antes da particicao e da montagem da matriz em `src/matriz.py`.

## Unidade e Chaves

- Cada linha representa uma resposta ou jornada identificada por `RESPONDENT_ID`.
- `RESPONDENT_ID` e obrigatorio, nao pode ser nulo e deve ser unico na base analitica.
- `ID_GOLDENRECORD` identifica o Cliente e e usado exclusivamente para agrupamento na validacao.
- Registros sem `ID_GOLDENRECORD` nao sao corrigidos nem transformados em grupos unitarios. Eles ficam fora das particoes agrupadas, com a quantidade registrada em metadados.
- Fontes transacionais unidas por `RESPONDENT_ID` devem obedecer cardinalidade 1:1; qualquer multiplicacao de linhas interrompe a integracao.

## Target

- Target de modelagem: `DETRATOR`.
- Classe positiva: `NPS_PRINCIPAL == -100`.
- Classe negativa: `NPS_PRINCIPAL` igual a `0` ou `100`.
- Na base de treino e avaliacao, `DETRATOR` deve pertencer ao dominio binario `{0, 1}` e nunca compoe `X`.
- Na entrada de uma jornada a pontuar, `DETRATOR` nao existe e nao e exigido pelo contrato.

## Feature Set V1

A allowlist implementada contem exatamente 11 features:

`TIER_VIAGEM`, `VOO_TIPO`, `TIPO_ENTRETENIMENTO`, `CANAL_COMPRA`, `SEGMENTO`, `ESTATISTICA_ATRASOSAIDA`, `ATRASO_CHEGADA`, `CANCELAMENTO_VOO`, `ANTECEDENCIA_CANCELAMENTO`, `TEMPO_VOO` e `N_TRECHOS`.

- `TIER_VIAGEM` substitui `PERFIL_TUDOAZUL` para evitar redundancia semantica.
- `N_TRECHOS` e a unica derivacao de rota aprovada e deriva de `BASE_AIRPORTLEG`.
- `QTDE_VIAGENS_12M` fica fora ate que exista uma contagem reconstruida com corte estrito em `t_score`.

## Leakage e Disponibilidade Temporal

- Nenhuma feature pode estar disponivel depois de `t_score`.
- `NPS_PRINCIPAL`, `DETRATOR`, `CATEGORIA_NPS`, qualquer `NPS_*`, qualquer `SUB_*` e identificadores nao entram como preditores.
- Para voos cancelados, `ESTATISTICA_ATRASOSAIDA`, `ATRASO_CHEGADA`, `TEMPO_VOO` e `N_TRECHOS` sao mascaradas como ausentes, pois dependem do encerramento da jornada.
- Missing estrutural e preservado. O pipeline nao aplica `fillna(0)` global.

## Validacao

- O split e temporal e agrupado por `ID_GOLDENRECORD`.
- Nenhum Cliente pode existir em mais de uma particao ou fold.
- Imputacao, encoding e escalonamento sao ajustados somente no treino.
- Schema invalido, duplicidade de `RESPONDENT_ID`, target fora do dominio e dtypes incompativeis falham explicitamente.

## Seguranca

Testes utilizam fixtures sinteticas. Dados reais, credenciais e outputs de notebooks nao podem ser versionados.
