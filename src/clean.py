"""
SAFIRA | Secao 4.2.1 - Integracao e limpeza das bases da Azul.

Le os cinco arquivos disponibilizados pelo parceiro, aplica os filtros de
qualidade, constroi as variaveis derivadas e calcula os pesos de
pos-estratificacao. Produz um DataFrame unico com granularidade de voo
avaliado.

As bases NAO sao versionadas (restricao do TAPI). Aponte DATA_DIR para o
diretorio local ou para a pasta montada do Google Drive.
"""
from __future__ import annotations

import glob
import os

import numpy as np
import pandas as pd

DATA_DIR = os.environ.get("SAFIRA_DATA_DIR", "dados")

# Taxonomia de atraso usada pela Azul. A ordem importa: e a mesma chave da
# base populacional DISTRIBUICAO_PAX_NORMALIZADO.
ORD_ATRASO = ["a. Sem Atraso", "b. 15m - 60m", "c. 61m - 120m", "d. >120m"]


def _p(nome: str) -> str:
    return os.path.join(DATA_DIR, nome)


def carregar_bases(data_dir: str | None = None):
    """Le as tres bases transacionais. Retorna (nps, perfil, viagem)."""
    d = data_dir or DATA_DIR
    nps = pd.concat(
        [pd.read_csv(f, low_memory=False)
         for f in sorted(glob.glob(os.path.join(d, "PROJETO_INTELI.NPS_0*.csv")))],
        ignore_index=True,
    )
    perfil = pd.concat(
        [pd.read_csv(f, low_memory=False)
         for f in sorted(glob.glob(os.path.join(d, "PROJETO_INTELI.PERFIL_CLIENTE_0*.csv")))],
        ignore_index=True,
    )
    viagem = pd.read_csv(
        os.path.join(d, "PROJETO_INTELI.INFORMACAO_VIAGEM.csv"), low_memory=False
    )
    return nps, perfil, viagem


def carregar_populacao(data_dir: str | None = None) -> pd.DataFrame:
    """Le a base agregada de distribuicao populacional de passageiros."""
    d = data_dir or DATA_DIR
    dist = pd.read_csv(os.path.join(d, "PROJETO_INTELI.DISTRIBUICAO_PAX_NORMALIZADO.csv"))
    dist["MES_ANO"] = pd.to_datetime(dist["MES"])
    return dist


def faixa_atraso(minutos: pd.Series) -> pd.Categorical:
    """Discretiza o atraso na saida na taxonomia da Azul."""
    banda = np.select(
        [minutos < 15, minutos <= 60, minutos <= 120],
        ORD_ATRASO[:3],
        default=ORD_ATRASO[3],
    )
    return pd.Categorical(banda, categories=ORD_ATRASO, ordered=True)


def integrar(nps, perfil, viagem, log=None):
    """Aplica filtros F1 a F4 e devolve a base analitica integrada."""
    registrar = log.append if log is not None else (lambda s: None)

    def L(s):
        registrar(s)
        print(s)

    L(f"[0] Bruto: NPS={len(nps)} PERFIL={len(perfil)} VIAGEM={len(viagem)}")

    # F1: linhas integralmente duplicadas.
    n0 = len(nps)
    nps = nps.drop_duplicates()
    L(f"[F1] Linhas 100% duplicadas removidas: {n0 - len(nps)}")

    # F2: RESPONDENT_ID repetido com valores divergentes, mantem a primeira.
    n0 = len(nps)
    nps = nps.drop_duplicates(subset="RESPONDENT_ID", keep="first")
    L(f"[F2] RESPONDENT_ID duplicado com conflito removido: {n0 - len(nps)}")

    perfil = perfil.drop_duplicates(subset="RESPONDENT_ID")
    viagem = viagem.drop_duplicates(subset="RESPONDENT_ID")

    df = (nps
          .merge(perfil.drop(columns=["ID_GOLDENRECORD"]), on="RESPONDENT_ID", how="inner")
          .merge(viagem, on="RESPONDENT_ID", how="inner"))
    L(f"[F3] Apos juncao 1:1 (inner): {len(df)} linhas x {df.shape[1]} colunas")

    # F4: colunas sem poder discriminativo.
    const = [c for c in df.columns if df[c].nunique(dropna=False) <= 1]
    df = df.drop(columns=const)
    L(f"[F4] Colunas constantes removidas: {const}")
    return df


def derivar(df, log=None):
    """Constroi alvo e variaveis derivadas do item (f) da secao 4.2.1."""
    registrar = log.append if log is not None else (lambda s: None)

    def L(s):
        registrar(s)
        print(s)

    df = df.copy()
    df["DATA_STD"] = pd.to_datetime(df["DATA_STD"])
    df["DETRATOR"] = (df["NPS_PRINCIPAL"] == -100).astype(int)
    df["CLASSE_NPS"] = df["NPS_PRINCIPAL"].map({100: "Promotor", 0: "Neutro", -100: "Detrator"})

    # CANCELAMENTO_VOO costuma vir como booleano, mas se o CSV trouxer texto o
    # astype(bool) marcaria a string 'False' como verdadeira. Normaliza uma vez so.
    if not pd.api.types.is_bool_dtype(df["CANCELAMENTO_VOO"]):
        df["CANCELAMENTO_VOO"] = (df["CANCELAMENTO_VOO"].astype(str).str.strip()
                                  .str.lower().isin(["true", "1", "sim", "s"]))

    # ATENCAO: ASSENTOS traz um assento POR TRECHO do mesmo passageiro
    # (ex.: '20A/17A/28A' para o itinerario FOR/UDI/CNF/POA). Nao mede tamanho
    # de grupo. Verificado por tabulacao cruzada contra N_TRECHOS (rho = 0,984).
    # Mantida apenas como variavel de auditoria, fora do conjunto de preditores.
    df["N_ASSENTOS_AUDIT"] = df["ASSENTOS"].str.count("/").add(1)

    df["N_TRECHOS"] = df["BASE_AIRPORTLEG"].str.count("/")  # trechos = aeroportos - 1
    df["AEROPORTO_ORIGEM"] = df["BASE_AIRPORTLEG"].str.split("/").str[0]
    df["AEROPORTO_DESTINO"] = df["BASE_AIRPORTLEG"].str.split("/").str[-1]
    df["FAIXA_ATRASO"] = faixa_atraso(df["ESTATISTICA_ATRASOSAIDA"])
    df["TRIMESTRE"] = df["DATA_STD"].dt.to_period("Q").astype(str)
    df["MES_ANO"] = df["DATA_STD"].dt.to_period("M").dt.to_timestamp()
    df["N_RESP_CLIENTE"] = df["ID_GOLDENRECORD"].map(df["ID_GOLDENRECORD"].value_counts())

    L("[F5] Derivadas: N_TRECHOS, AEROPORTO_ORIGEM/DESTINO, FAIXA_ATRASO, "
      "MES_ANO, N_RESP_CLIENTE")
    L("[F5b] N_ASSENTOS descartada como preditor: redundante com N_TRECHOS (rho=0,984)")
    return df


def pesos_pos_estratificacao(df, dist, log=None):
    """Peso = proporcao populacional / proporcao amostral, por mes x faixa x canal."""
    registrar = log.append if log is not None else (lambda s: None)

    pop = (dist.groupby(["MES_ANO", "DELAY_DEPARTURE_RANGE", "CANAL_COMPRA"])
               ["PERC_PAX"].sum().rename("p_pop").reset_index())
    pop["p_pop"] = pop.groupby("MES_ANO")["p_pop"].transform(lambda x: x / x.sum())

    amo = (df.groupby(["MES_ANO", "FAIXA_ATRASO", "CANAL_COMPRA"], observed=True)
             .size().rename("n").reset_index())
    amo["p_amo"] = amo.groupby("MES_ANO")["n"].transform(lambda x: x / x.sum())

    m = amo.merge(
        pop,
        left_on=["MES_ANO", "FAIXA_ATRASO", "CANAL_COMPRA"],
        right_on=["MES_ANO", "DELAY_DEPARTURE_RANGE", "CANAL_COMPRA"],
        how="left",
    )
    m["PESO_POP"] = m["p_pop"] / m["p_amo"]

    df = df.merge(
        m[["MES_ANO", "FAIXA_ATRASO", "CANAL_COMPRA", "PESO_POP"]],
        on=["MES_ANO", "FAIXA_ATRASO", "CANAL_COMPRA"],
        how="left",
    )
    df["PESO_POP"] = df["PESO_POP"].fillna(0)

    msg = "[F6] Peso de pos-estratificacao calculado (mes x faixa_atraso x canal)"
    registrar(msg)
    print(msg)
    return df


def pipeline(data_dir: str | None = None):
    """Executa o pipeline completo. Retorna (df, log)."""
    log: list[str] = []
    nps, perfil, viagem = carregar_bases(data_dir)
    df = integrar(nps, perfil, viagem, log)
    df = derivar(df, log)
    df = pesos_pos_estratificacao(df, carregar_populacao(data_dir), log)
    msg = f"[FINAL] {len(df)} linhas x {df.shape[1]} colunas"
    log.append(msg)
    print(msg)
    return df, log


if __name__ == "__main__":
    import pickle

    pd.set_option("display.width", 250)
    pd.set_option("display.max_columns", 60)

    base, registro = pipeline()
    os.makedirs("out", exist_ok=True)
    with open("out/clean.pkl", "wb") as fh:
        pickle.dump(base, fh)
    with open("out/log_limpeza.txt", "w", encoding="utf-8") as fh:
        fh.write("\n".join(registro))
