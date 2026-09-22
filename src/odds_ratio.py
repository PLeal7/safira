"""Odds ratio da Regressao Logistica por feature original (card #212).

O coeficiente de uma Regressao Logistica e legivel, mas nao no espaco em que o
modelo o produz. Entre a feature do contrato e o coeficiente existem tres
transformacoes que mudam o que o numero significa, e ignorar qualquer uma delas
devolve um odds ratio valido e errado:

- **o `OneHotEncoder` quebra uma categorica em uma coluna por nivel.** Reportar
  `categoricas__CANAL_COMPRA_OTHER` sem dizer que a feature e `CANAL_COMPRA` e o
  nivel e `OTHER` entrega ao leitor o nome que a biblioteca inventou, nao a
  variavel que a operacao conhece;
- **o `SimpleImputer` acrescenta um indicador por coluna com ausencia.** Esse
  indicador nao mede a variavel: mede o fato de ela nao ter sido medida. Em
  `ANTECEDENCIA_CANCELAMENTO`, que so existe em voo cancelado, o indicador de
  ausencia e na pratica "o voo nao foi cancelado", e le-lo como se fosse a
  antecedencia inverteria o sentido;
- **o `RobustScaler` divide pelo IQR do treino.** `exp(coef)` passa a ser o odds
  ratio por IQR, e nao por unidade natural. Nesta base o IQR e 9 minutos em
  `ESTATISTICA_ATRASOSAIDA` e 140 em `TEMPO_VOO`; nas outras seis numericas ele
  e zero e o `scikit-learn` cai no fallback de 1,0, entao ali `exp(coef)` ja e
  por unidade. Usar a mesma leitura para as oito e o erro que passa despercebido.

Nao ha categoria de referencia: o `OneHotEncoder` do contrato e `drop=None`,
entao todos os niveis entram. O coeficiente de um nivel nao compara contra um
nivel-base ausente, e a comparacao que significa algo e entre niveis da mesma
variavel.

O mapeamento nao e feito por parsing do nome de saida. Ele e reconstruido da
estrutura ajustada do `ColumnTransformer` e depois **conferido** contra
`get_feature_names_out()`: se o `scikit-learn` mudar a convencao de nome, a
funcao levanta em vez de rotular a coluna errada em silencio.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

PASSO_PREPARO = "preparo"
PASSO_MODELO = "modelo"
PREFIXO_INDICADOR = "missingindicator_"


def _nome_esperado(bloco: str, feature: str, tipo: str, nivel: str | None) -> str:
    if tipo == "ausencia":
        return f"{bloco}__{PREFIXO_INDICADOR}{feature}"
    if tipo == "categorica":
        return f"{bloco}__{feature}_{nivel}"
    return f"{bloco}__{feature}"


def mapear_colunas(preprocessador) -> pd.DataFrame:
    """Cada coluna da matriz de volta para (feature original, tipo, nivel).

    Devolve uma linha por coluna de saida, na mesma ordem de
    `get_feature_names_out()`, com `feature_original`, `tipo` em
    {numerica, ausencia, categorica} e `nivel` preenchido so nas categoricas.
    """
    linhas = []
    for bloco, transformador, colunas in preprocessador.transformers_:
        if transformador == "drop" or not len(colunas):
            continue
        passos = getattr(transformador, "named_steps", {})
        codificador = passos.get("codificar")
        imputador = passos.get("imputar")

        if codificador is not None:
            for coluna, niveis in zip(colunas, codificador.categories_):
                for nivel in niveis:
                    linhas.append((bloco, coluna, "categorica", str(nivel)))
            continue

        linhas.extend((bloco, coluna, "numerica", None) for coluna in colunas)
        # O indicador vem depois das colunas imputadas, e so para as que tinham
        # ausencia no treino: `indicator_.features_` traz os indices dessas.
        if imputador is not None and getattr(imputador, "indicator_", None) is not None:
            linhas.extend((bloco, colunas[i], "ausencia", "valor ausente")
                          for i in imputador.indicator_.features_)

    tabela = pd.DataFrame(linhas, columns=["bloco", "feature_original", "tipo", "nivel"])
    esperado = [_nome_esperado(*linha) for linha in linhas]
    saida = list(preprocessador.get_feature_names_out())
    if esperado != saida:
        divergentes = [(e, s) for e, s in zip(esperado, saida) if e != s]
        raise ValueError(
            "o mapeamento nao reproduz get_feature_names_out(): "
            f"{len(saida)} colunas na saida, {len(esperado)} reconstruidas, "
            f"primeiras divergencias {divergentes[:3]}"
        )
    tabela.insert(0, "coluna_matriz", saida)
    return tabela.drop(columns="bloco")


def _escalas(preprocessador) -> dict[str, float]:
    """IQR do treino por coluna numerica, ou vazio se nao houver escalonamento."""
    for bloco, transformador, colunas in preprocessador.transformers_:
        passos = getattr(transformador, "named_steps", {})
        escalador = passos.get("escalar")
        if escalador is not None:
            # `scale_` cobre a saida do imputador, que traz as colunas e depois
            # os indicadores; so as primeiras correspondem as numericas.
            return dict(zip(colunas, escalador.scale_[:len(colunas)]))
    return {}


def odds_ratio(pipeline, passo_preparo: str = PASSO_PREPARO,
               passo_modelo: str = PASSO_MODELO) -> pd.DataFrame:
    """Tabela de odds ratio do pipeline ajustado, por feature original.

    `odds_ratio` e `exp(coef)`, o efeito de uma unidade **da matriz**.
    `odds_ratio_por_unidade` desfaz o escalonamento e devolve o efeito de uma
    unidade **da variavel original**; fica vazio nas categoricas e nos
    indicadores, onde a coluna ja e 0/1 e as duas leituras coincidem.

    A tabela sai ordenada por `odds_ratio` decrescente: no topo o que mais
    aumenta a chance de detracao, na base o que mais reduz.
    """
    preprocessador = pipeline.named_steps[passo_preparo]
    estimador = pipeline.named_steps[passo_modelo]
    coeficientes = np.asarray(estimador.coef_).ravel()

    tabela = mapear_colunas(preprocessador)
    if len(coeficientes) != len(tabela):
        raise ValueError(
            f"{len(coeficientes)} coeficientes para {len(tabela)} colunas mapeadas"
        )

    escalas = _escalas(preprocessador)
    tabela["coeficiente"] = coeficientes
    tabela["iqr_do_treino"] = [escalas.get(f) if t == "numerica" else np.nan
                               for f, t in zip(tabela["feature_original"], tabela["tipo"])]
    tabela["odds_ratio"] = np.exp(coeficientes)
    tabela["odds_ratio_por_unidade"] = np.where(
        tabela["tipo"] == "numerica",
        np.exp(coeficientes / tabela["iqr_do_treino"].fillna(1.0)),
        np.nan,
    )
    return tabela.sort_values("odds_ratio", ascending=False).reset_index(drop=True)


def efeito_acumulado(odds_ratio_por_unidade: float, unidades: float) -> float:
    """Efeito de `unidades` da variavel original, composto multiplicativamente.

    Uma variavel cujo odds ratio por minuto e 1,0028 nao tem "efeito nenhum":
    tem 1,18 por hora de atraso. Reportar so o valor unitario de uma variavel
    medida em minutos esconde o efeito na escala em que a operacao decide.
    """
    return float(odds_ratio_por_unidade ** unidades)
