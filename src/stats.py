"""
SAFIRA | Secao 4.2.1 - Classificacao das colunas, estatistica descritiva e
medidas de associacao.

Produz as tres tabelas da secao 4.2.1: numericas, categoricas e V de Cramer
contra o alvo binarizado. Inclui tambem o comparativo entre a taxa de detracao
bruta e a pos-estratificada.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import chi2_contingency

# Ordem das tabelas da secao 4.2.1, itens (c) e (d).
NUMERICAS = [
    "TEMPO_VOO", "ESTATISTICA_ATRASOSAIDA", "ATRASO_CHEGADA",
    "ANTECEDENCIA_CANCELAMENTO", "QTDE_VIAGENS_12M", "QTDE_VIAGENS_24M",
    "QTDE_VIAGENS_36M", "N_TRECHOS",
]

CATEGORICAS = [
    "CLASSE_NPS", "VOO_TIPO", "TIPO_ENTRETENIMENTO", "CANAL_COMPRA", "SEGMENTO",
    "TIER_VIAGEM", "SUB_FIL_MOTIVOVIAGEM", "SUB_FIL_FREQUENCIAAZUL",
    "CANCELAMENTO_VOO", "SUB_ENTRETENIMENTO1", "SUB_ENTRETENIMENTO2",
    "FAIXA_ATRASO", "AEROPORTO_ORIGEM", "EQUIPAMENTO_TIPO", "BASE_AIRPORTLEG",
    "ASSENTOS", "VOO_NUMERO",
]

# Preditoras candidatas para a medida de associacao com o alvo. Ficam de fora
# CLASSE_NPS (e o proprio alvo) e os campos de altissima cardinalidade.
CAT_ASSOCIACAO = [
    "FAIXA_ATRASO", "CANCELAMENTO_VOO", "SUB_FIL_FREQUENCIAAZUL",
    "TIPO_ENTRETENIMENTO", "VOO_TIPO", "TIER_VIAGEM", "SUB_FIL_MOTIVOVIAGEM",
    "AEROPORTO_ORIGEM", "SEGMENTO", "CANAL_COMPRA",
]


def classificar_colunas(df, limite_cardinalidade: int = 25):
    """Separa as colunas em numericas e categoricas de forma programatica.

    O criterio nao e apenas o dtype: campos inteiros de baixa cardinalidade,
    como flags, sao tratados como categoricos.
    """
    num, cat = [], []
    for c in df.columns:
        s = df[c]
        if pd.api.types.is_numeric_dtype(s) and not pd.api.types.is_bool_dtype(s):
            (cat if s.nunique(dropna=True) <= 2 else num).append(c)
        elif pd.api.types.is_datetime64_any_dtype(s):
            continue
        else:
            cat.append(c)
    return num, cat


def tabela_numericas(df, cols=None) -> pd.DataFrame:
    """describe com percentis, nulidade e assimetria."""
    cols = cols or NUMERICAS
    t = df[cols].describe(percentiles=[0.25, 0.5, 0.75, 0.95]).T
    t["nulos"] = df[cols].isna().mean() * 100
    t["assimetria"] = df[cols].skew()
    t = t[["count", "mean", "50%", "std", "min", "max", "95%", "nulos", "assimetria"]]
    t.columns = ["n", "Média", "Mediana", "Desvio", "Mín", "Máx", "P95",
                 "% Nulo", "Assimetria"]
    return t.round(2)


def tabela_categoricas(df, cols=None) -> pd.DataFrame:
    """Contagem de categorias, moda, frequencia da moda e nulidade."""
    cols = cols or CATEGORICAS
    linhas = []
    for c in cols:
        vc = df[c].value_counts(dropna=True)
        linhas.append({
            "Variável": c,
            "Categorias": int(df[c].nunique()),
            "Moda": str(vc.index[0]),
            "Freq. moda": int(vc.iloc[0]),
            "% moda": round(vc.iloc[0] / len(df) * 100, 2),
            "% Nulo": round(df[c].isna().mean() * 100, 2),
        })
    return pd.DataFrame(linhas)


def cramers_v(x: pd.Series, y: pd.Series) -> float:
    """V de Cramer (CRAMER, 1946) entre duas variaveis nominais.

    Mede associacao onde o coeficiente de correlacao nao se aplica. Varia de
    0 (independencia) a 1 (associacao perfeita).
    """
    tab = pd.crosstab(x, y)
    if tab.shape[0] < 2 or tab.shape[1] < 2:
        return np.nan
    chi2 = chi2_contingency(tab)[0]
    n = tab.to_numpy().sum()
    return float(np.sqrt(chi2 / (n * (min(tab.shape) - 1))))


def tabela_cramer(df, cols=None, alvo: str = "DETRATOR") -> pd.DataFrame:
    """Forca de associacao de cada categorica com o alvo, em ordem decrescente."""
    cols = cols or CAT_ASSOCIACAO
    linhas = [{"Variável": c, "V de Cramér": round(cramers_v(df[c], df[alvo]), 3)}
              for c in cols]
    return (pd.DataFrame(linhas)
              .sort_values("V de Cramér", ascending=False)
              .reset_index(drop=True))


def bruto_vs_ponderado(df, cortes=("FAIXA_ATRASO", "CANAL_COMPRA", "TIER_VIAGEM", "VOO_TIPO")):
    """Taxa de detracao bruta e pos-estratificada, por corte."""
    saida = {}
    for c in cortes:
        linhas = []
        for chave, g in df.groupby(c, observed=True):
            pond = (np.average(g["DETRATOR"], weights=g["PESO_POP"]) * 100
                    if g["PESO_POP"].sum() > 0 else np.nan)
            linhas.append({c: chave, "n": len(g),
                           "bruto": g["DETRATOR"].mean() * 100, "pond": pond})
        saida[c] = pd.DataFrame(linhas).set_index(c).round(2)
    return saida


def resumo_geral(df) -> dict:
    """Numeros de referencia citados no texto da secao 4.2.1."""
    return {
        "registros": len(df),
        "clientes_distintos": int(df["ID_GOLDENRECORD"].nunique()),
        "detracao_bruta": df["DETRATOR"].mean() * 100,
        "detracao_ponderada": np.average(df["DETRATOR"], weights=df["PESO_POP"]) * 100,
        "nps_bruto": df["NPS_PRINCIPAL"].mean(),
        "nps_ponderado": np.average(df["NPS_PRINCIPAL"], weights=df["PESO_POP"]),
    }


if __name__ == "__main__":
    import pickle

    pd.set_option("display.width", 300)
    pd.set_option("display.max_columns", 80)
    pd.set_option("display.max_rows", 200)

    with open("out/clean.pkl", "rb") as fh:
        base = pickle.load(fh)

    print("=== TABELA NUMERICAS ===")
    print(tabela_numericas(base).to_string())
    print("\n=== TABELA CATEGORICAS ===")
    print(tabela_categoricas(base).to_string(index=False))
    print("\n=== V DE CRAMER CONTRA O ALVO ===")
    print(tabela_cramer(base).to_string(index=False))
    print("\n=== BRUTO vs PONDERADO ===")
    for corte, tabela in bruto_vs_ponderado(base).items():
        print(f"\n{corte}")
        print(tabela.to_string())
    r = resumo_geral(base)
    print(f"\nGERAL bruto={r['detracao_bruta']:.2f}% pond={r['detracao_ponderada']:.2f}%")
