"""SAFIRA | Baseline dummy da base analítica.

Produz `data/dummy/base_analitica.parquet`, com as mesmas 52 colunas, na mesma
ordem e com os mesmos tipos de `data/processed/base_analitica.parquet`, em 10%
do volume e com valores inteiramente sintéticos. Serve para exercitar o
pipeline (particionamento, matriz, modelo) sem tocar no dado do parceiro, que
não é versionável.

O dummy não é escrito coluna a coluna a partir de um esquema copiado à mão. O
gerador sorteia apenas as oito fontes que `integrar_bases` lê de `data/raw/` e
deixa o próprio pipeline produzir a base analítica a partir delas, como faz com
o dado real. Um segundo esquema escrito aqui envelheceria em silêncio: as
derivadas de `preparar_base_analitica` mudariam no pipeline e continuariam as
antigas no dummy. Assim, as derivadas não podem divergir — são as mesmas.

Os CSV sintéticos ficam ao lado do parquet, e valem por si: quem quiser testar a
integração, e não só o que vem depois dela, aponta `carregar_bases` para a pasta.

Nenhum valor real é copiado. Os identificadores são uma sequência própria
começando em 10.000.000, fora da faixa dos dados reais, e as demais colunas são
sorteadas a partir de vocabulários públicos (siglas IATA, tipos de aeronave,
canais de compra) ou de distribuições paramétricas.

O que o gerador preserva de propósito nas fontes, porque o pipeline depende
disso para chegar até a base analítica:

- Cobertura integral e cardinalidade 1:1 de `RESPONDENT_ID` entre NPS, PERFIL e
  VIAGEM, exigidas por `clean.conferir_cobertura` e pelos merges validados.
- `ID_GOLDENRECORD` idêntico nas duas tabelas em que aparece, ausências
  incluídas, exigido por `clean._conferir_coluna_redundante`.
- `RESPONDENT_ID` crescente com `DATA_STD`, de que dependem a anterioridade em
  `features.adicionar_historico` e o corte temporal de `split`.
- Reincidência de clientes em `ID_GOLDENRECORD`, sem a qual as features de
  histórico ficariam todas vazias.
- Coerência entre `BASE_AIRPORTLEG`, `EQUIPAMENTO_TIPO`, `VOO_NUMERO`,
  `VOO_TIPO` e `ASSENTOS`: um aeroporto a mais que trechos, e uma aeronave, um
  número de voo e um assento por trecho.
- O par duplicado de `RESPONDENT_ID` em NPS_04 divergindo em `TEMPO_VOO`, único
  caso que `clean.DIVERGENCIA_APROVADA_NPS` autoriza.
- As ausências que definem o tipo lido: `ID_GOLDENRECORD` sai int64 em NPS_01 e
  NPS_04 e float64 em NPS_02 e NPS_03, como no real.

Uma exceção deliberada aos 10%: DISTRIBUICAO_PAX_NORMALIZADO é tabela de apoio,
não amostra, e não entra na base analítica. `clean.pesos_pos_estratificacao`
interrompe se algum estrato mês x faixa de atraso x canal da amostra ficar sem
contrapartida, então a grade 36 x 4 x 6 é gerada inteira.

Executar com:  python scripts/gerar_dummy.py
Conferir com:  python scripts/gerar_dummy.py --conferir
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from preprocessamento_nps import integrar_bases, preparar_base_analitica

SAIDA_PADRAO = Path("data/dummy")
BASE_ANALITICA = "base_analitica.parquet"
BASE_ANALITICA_REAL = Path("data/processed") / BASE_ANALITICA
FRACAO = 0.10
SEMENTE = 42

# (bloco, linhas únicas no real, primeira data, última data, ausência em ID_GOLDENRECORD)
BLOCOS = (
    ("NPS_01", 120000, "2023-07-01", "2024-01-06", 0.0000),
    ("NPS_02", 120000, "2024-01-06", "2024-07-28", 0.0005),
    ("NPS_03", 120000, "2024-07-28", "2025-05-13", 0.0003),
    ("NPS_04", 124915, "2025-05-13", "2026-06-30", 0.0000),
)
# Cada arquivo de perfil cobre dois blocos de NPS, como no dado real.
PERFIL_DO_BLOCO = ("PERFIL_CLIENTE_01", "PERFIL_CLIENTE_01",
                   "PERFIL_CLIENTE_02", "PERFIL_CLIENTE_02")

PRIMEIRO_ID = 10_000_000
FRACAO_CLIENTES = 0.85          # clientes distintos por resposta; no real, ~0,85

AEROPORTOS = ("VCP", "CGH", "GRU", "CNF", "SDU", "REC", "POA", "CWB", "BSB",
              "FOR", "SSA", "MAO", "BEL", "VIX", "NAT", "GYN", "FLN", "CGB",
              "MCZ", "UDI", "JPA", "THE", "SLZ", "AJU", "PMW", "IGU", "LDB",
              "JOI", "NVT", "IOS")
EQUIPAMENTOS = ("32N", "32Q", "295", "E95", "AT9", "32I", "339")
CANAIS = ("Web", "Mobile", "Agency", "Callcenter", "Aeroporto", "Other")
PESO_CANAL = (0.2921, 0.2512, 0.4278, 0.0190, 0.0030, 0.0069)
SEGMENTOS = ("Demais Clientes", "Azul Viagens", "Corporativo")
PESO_SEGMENTO = (0.8941, 0.0207, 0.0852)
# Azul One e Diamante Unique só aparecem na segunda metade da série.
TIERS_ANTIGOS = ("Sem cadastro", "Azul Fidelidade", "Topazio", "Safira", "Diamante")
TIERS_NOVOS = TIERS_ANTIGOS + ("Azul One", "Diamante Unique")
PESO_TIER = (0.1201, 0.5034, 0.1159, 0.1032, 0.1545, 0.0004, 0.0024)
FAIXAS_ATRASO = ("a. Sem Atraso", "b. 15m - 60m", "c. 61m - 120m", "d. >120m")

# Itens de NPS: nota em {-100, 0, 100} e a ausência medida no dado real, que é o
# que separa um item respondido de um item não apresentado ao respondente.
ITENS_NPS = {
    "NPS_ATRASO": 0.855, "NPS_BAGAGEM": 0.655, "NPS_BAGMAO": 0.195,
    "NPS_CANCELAMENTO24H": 0.985, "NPS_CKBALCAO": 0.897, "NPS_CKMOBILE": 0.457,
    "NPS_CKTOTEM": 0.997, "NPS_CKWEB": 0.859, "NPS_COMISSARIOS": 0.208,
    "NPS_CONFORTO": 0.256, "NPS_EMBARQUE": 0.155, "NPS_ENTRETENIMENTO": 0.662,
    "NPS_LIMPEZA": 0.234, "NPS_PILOTOS": 0.224, "NPS_RESAGENCIA": 0.645,
    "NPS_RESWEB": 0.513, "NPS_SNACKS": 0.315, "NPS_AZULFID": 0.718,
    "NPS_WIFI": 0.902,
}

COLUNAS_NPS = (
    "RESPONDENT_ID", "ID_GOLDENRECORD", "DATA_STD", "EQUIPAMENTO_TIPO",
    "BASE_AIRPORTLEG", "VOO_TIPO", "VOO_NUMERO", "TIPO_ENTRETENIMENTO",
    "NPS_PRINCIPAL", *ITENS_NPS, "SUB_ENTRETENIMENTO1", "SUB_ENTRETENIMENTO2",
    "SUB_FIL_MOTIVOVIAGEM", "SUB_FIL_FREQUENCIAAZUL", "VOO_INTERNACIONAL",
    "TEMPO_VOO", "CANAL_COMPRA",
)
COLUNAS_PERFIL = ("RESPONDENT_ID", "ID_GOLDENRECORD", "SEGMENTO", "TIER_VIAGEM",
                  "QTDE_VIAGENS_12M", "QTDE_VIAGENS_24M", "QTDE_VIAGENS_36M")
COLUNAS_VIAGEM = ("RESPONDENT_ID", "CANCELAMENTO_VOO", "ANTECEDENCIA_CANCELAMENTO",
                  "ATRASO_CHEGADA", "ESTATISTICA_ATRASOSAIDA", "ASSENTOS")
COLUNAS_DIST = ("MES", "DELAY_DEPARTURE_RANGE", "CANAL_COMPRA", "PERC_PAX")


def _ausentar(rng, valores, taxa):
    """Devolve a série com `taxa` das posições sorteadas trocadas por ausência."""
    s = pd.Series(list(valores))
    return s.mask(rng.random(len(s)) < taxa) if taxa else s


def _categorica(rng, n, valores, pesos=None, ausencia=0.0):
    return _ausentar(rng, rng.choice(valores, n, p=pesos), ausencia)


def _pesos(valores):
    """Renormaliza para somar 1, para poder recortar um prefixo da tupla."""
    p = np.asarray(valores, dtype=float)
    return p / p.sum()


def _juntar(partes):
    """Concatena por linha as listas de trechos, no formato 'A/B/C'."""
    return ["/".join(p) for p in partes]


def _esqueleto(rng, fracao):
    """Monta a espinha dorsal compartilhada: chave, cliente, data e nº de trechos.

    Tudo que precisa bater entre os três arquivos nasce aqui, uma vez só. É o que
    garante a cobertura integral e o 1:1 sem depender de o gerador de cada tabela
    lembrar de sortear a mesma coisa.
    """
    tamanhos = [max(1, round(n * fracao)) for _, n, *_ in BLOCOS]
    inicios = np.cumsum([0] + tamanhos[:-1])
    total = sum(tamanhos)

    # Chave crescente: a ordem por RESPONDENT_ID tem que reproduzir a cronologia,
    # de que dependem a anterioridade do histórico e o corte temporal.
    resp = PRIMEIRO_ID + np.cumsum(rng.integers(1, 40, total))

    # Clientes sorteados de um conjunto menor que o de respostas, para que haja
    # reincidência e as features de histórico tenham o que enxergar.
    clientes = rng.choice(np.arange(500_000, 299_000_000),
                          max(1, round(total * FRACAO_CLIENTES)), replace=False)
    golden = pd.Series(rng.choice(clientes, total), dtype="Int64")

    datas = []
    sem_cliente = np.zeros(total, dtype=bool)
    bloco = np.repeat(np.arange(len(BLOCOS)), tamanhos)
    for (_, _, ini, fim, taxa_nula), n, pos in zip(BLOCOS, tamanhos, inicios):
        ini, fim = pd.Timestamp(ini), pd.Timestamp(fim)
        datas.append(ini + pd.to_timedelta(
            np.sort(rng.integers(0, (fim - ini).days + 1, n)), unit="D"))
        if taxa_nula:
            sem_cliente[pos:pos + n] = rng.random(n) < taxa_nula
    golden = golden.mask(sem_cliente)

    # Voo direto tem um trecho; conexão e escala têm de dois a seis, na proporção
    # condicional que N_TRECHOS tem na base analítica real.
    tipo = rng.choice(("Direto", "Conexão", "Escala"), total, p=_pesos((0.7024, 0.2949, 0.0027)))
    trechos = np.where(tipo == "Direto", 1,
                       rng.choice((2, 3, 4, 5, 6), total,
                                  p=_pesos((0.8270, 0.1660, 0.0050, 0.0015, 0.0005))))

    return pd.DataFrame({
        "RESPONDENT_ID": resp,
        "ID_GOLDENRECORD": golden,
        "DATA_STD": pd.DatetimeIndex(np.concatenate(datas)),
        "VOO_TIPO": tipo,
        "N_TRECHOS": trechos,
        "BLOCO": bloco,
    })


def _nps(rng, base):
    """Colunas da pesquisa, coerentes com o itinerário sorteado no esqueleto."""
    n = len(base)
    trechos = base["N_TRECHOS"].to_numpy()
    percursos = [rng.choice(AEROPORTOS, t + 1, replace=False) for t in trechos]

    # Tempo de voo cresce com o número de trechos e inclui a espera em conexão.
    por_trecho = np.clip(rng.lognormal(4.45, 0.45, n), 35, 700)
    tempo = np.clip(por_trecho * trechos + 60 * (trechos - 1), 35, 4320).round()

    df = pd.DataFrame({
        "RESPONDENT_ID": base["RESPONDENT_ID"].to_numpy(),
        "ID_GOLDENRECORD": base["ID_GOLDENRECORD"].array,
        "DATA_STD": base["DATA_STD"].dt.strftime("%Y-%m-%d").to_numpy(),
        "EQUIPAMENTO_TIPO": _juntar(rng.choice(EQUIPAMENTOS, t) for t in trechos),
        "BASE_AIRPORTLEG": _juntar(percursos),
        "VOO_TIPO": base["VOO_TIPO"].to_numpy(),
        "VOO_NUMERO": _juntar(rng.integers(2100, 9900, t).astype(str) for t in trechos),
        "TIPO_ENTRETENIMENTO": _categorica(
            rng, n, ("AO VIVO", "GRAVADO", "NÃO TEM ENTRETENIMENTO"),
            (0.55, 0.20, 0.25), 0.30),
        "NPS_PRINCIPAL": rng.choice((100, 0, -100), n, p=_pesos((0.6498, 0.1457, 0.2044))),
    })
    for item, ausencia in ITENS_NPS.items():
        df[item] = _ausentar(
            rng, rng.choice((100, 0, -100), n, p=(0.72, 0.12, 0.16)), ausencia
        ).astype("Int64")
    df["SUB_ENTRETENIMENTO1"] = _categorica(
        rng, n, ("Sim", "Não", "Não assisti"), (0.45, 0.40, 0.15), 0.67)
    df["SUB_ENTRETENIMENTO2"] = _categorica(
        rng, n, ("Monitor", "Áudio", "Controle", "Sinal Ruim",
                 "Não tinha canal ao vivo"), None, 0.93)
    df["SUB_FIL_MOTIVOVIAGEM"] = _categorica(
        rng, n, ("Lazer", "Trabalho", "Pessoal", "Trabalho combinado com lazer"),
        (0.55, 0.25, 0.14, 0.06), 0.006)
    df["SUB_FIL_FREQUENCIAAZUL"] = _categorica(
        rng, n, ("De 2 a 5 vezes por ano", "De 6 a 10 vezes por ano",
                 "Esta foi a primeira vez",
                 "Realizo pelo menos 1 viagem por mês pela Azul"),
        (0.48, 0.20, 0.22, 0.10), 0.008)
    df["VOO_INTERNACIONAL"] = "Domestic"
    df["TEMPO_VOO"] = _ausentar(rng, tempo, 0.0005).astype("Int64")
    df["CANAL_COMPRA"] = rng.choice(CANAIS, n, p=_pesos(PESO_CANAL))
    return df[list(COLUNAS_NPS)]


def _perfil(rng, base):
    n = len(base)
    # Os tiers novos só existem nos blocos mais recentes, como na série real; nos
    # blocos antigos os pesos dos cinco originais são renormalizados entre si.
    tier = np.where(base["BLOCO"].to_numpy() >= 2,
                    rng.choice(TIERS_NOVOS, n, p=_pesos(PESO_TIER)),
                    rng.choice(TIERS_ANTIGOS, n, p=_pesos(PESO_TIER[:len(TIERS_ANTIGOS)])))
    # Ausência no perfil acompanha a do cliente: sem cadastro, sem histórico.
    sem_cadastro = base["ID_GOLDENRECORD"].isna().to_numpy()
    v12 = rng.poisson(3, n) + rng.binomial(1, 0.1, n) * rng.poisson(12, n)
    v24 = v12 + rng.poisson(4, n)
    v36 = v24 + rng.poisson(5, n)

    def contagem(v):
        return pd.Series(v, dtype="Int64").mask(sem_cadastro)

    df = pd.DataFrame({
        "RESPONDENT_ID": base["RESPONDENT_ID"].to_numpy(),
        "ID_GOLDENRECORD": base["ID_GOLDENRECORD"].array,
        "SEGMENTO": rng.choice(SEGMENTOS, n, p=_pesos(PESO_SEGMENTO)),
        "TIER_VIAGEM": tier,
        "QTDE_VIAGENS_12M": contagem(v12),
        "QTDE_VIAGENS_24M": contagem(v24),
        "QTDE_VIAGENS_36M": contagem(v36),
    })
    return df[list(COLUNAS_PERFIL)]


def _viagem(rng, base):
    n = len(base)
    trechos = base["N_TRECHOS"].to_numpy()
    # 80% dos voos chegam sem atraso; quando atrasam, o atraso na saída explica a
    # maior parte do atraso na chegada.
    chegada = np.where(rng.random(n) < 0.796, 0,
                       np.clip(rng.lognormal(3.5, 1.3, n), 1, 4319)).round()
    saida = np.where(
        chegada == 0,
        np.where(rng.random(n) < 0.60, 0, np.clip(rng.lognormal(2.0, 0.8, n), 1, 60)),
        chegada * rng.uniform(0.6, 1.1, n),
    ).round()

    cancelado = rng.random(n) < 0.089
    antecedencia = pd.array(rng.exponential(12, n).round().clip(0, 400),
                            dtype="Int64")
    assentos = _ausentar(rng, _juntar(
        [f"{f}{c}" for f, c in zip(rng.integers(1, 31, t),
                                   rng.choice(tuple("ABCDEF"), t))]
        for t in trechos), 0.0012)

    df = pd.DataFrame({
        "RESPONDENT_ID": base["RESPONDENT_ID"].to_numpy(),
        # O real grava TRUE/FALSE em caixa alta; o pandas lê os dois como bool.
        "CANCELAMENTO_VOO": np.where(cancelado, "TRUE", "FALSE"),
        # Só voo cancelado tem antecedência de aviso.
        "ANTECEDENCIA_CANCELAMENTO": pd.Series(antecedencia).where(cancelado),
        "ATRASO_CHEGADA": chegada.astype(int),
        "ESTATISTICA_ATRASOSAIDA": saida.astype(int),
        "ASSENTOS": assentos,
    })
    return df[list(COLUNAS_VIAGEM)]


def _distribuicao(rng):
    """Grade completa mês x faixa x canal, com PERC_PAX somando 1 por mês."""
    meses = pd.date_range(BLOCOS[0][2], BLOCOS[-1][3], freq="MS")
    grade = pd.MultiIndex.from_product(
        [meses, FAIXAS_ATRASO, CANAIS], names=COLUNAS_DIST[:3]).to_frame(index=False)
    # Estritamente positivo: estrato com peso zero é condição de parada em clean.
    peso = pd.Series(rng.gamma(2.0, 1.0, len(grade)) + 0.01)
    grade["PERC_PAX"] = (peso / peso.groupby(grade["MES"]).transform("sum")).round(6)
    grade["MES"] = grade["MES"].dt.strftime("%Y-%m-%d 00:00:00.000")
    return grade[list(COLUNAS_DIST)]


def gerar(saida: Path | str = SAIDA_PADRAO, fracao: float = FRACAO,
          semente: int = SEMENTE) -> dict[str, int]:
    """Escreve a base analítica e suas fontes, e devolve {arquivo: nº de linhas}.

    A base analítica dummy não é escrita a partir de um segundo esquema copiado
    à mão: sai de `integrar_bases` e `preparar_base_analitica` lendo os CSV
    recém-gerados, exatamente como a real sai de `data/raw/`. É o que faz as 52
    colunas, a ordem e os tipos baterem sem que nada aqui precise saber quais
    são — e o que faz o dummy continuar correto quando o pipeline mudar.
    """
    rng = np.random.default_rng(semente)
    saida = Path(saida)
    saida.mkdir(parents=True, exist_ok=True)

    base = _esqueleto(rng, fracao)
    nps = _nps(rng, base)
    perfil = _perfil(rng, base)
    viagem = _viagem(rng, base)
    escritos = {}

    def escrever(nome, df):
        df.to_csv(saida / f"PROJETO_INTELI.{nome}.csv", index=False,
                  encoding="utf-8", lineterminator="\n")
        escritos[nome] = len(df)

    for i, (nome, *_) in enumerate(BLOCOS):
        fatia = nps[(base["BLOCO"] == i).to_numpy()]
        if nome == "NPS_04":
            # Reproduz a única duplicata aprovada: mesma chave, TEMPO_VOO
            # divergente. É o caso que clean.deduplicar existe para tratar.
            copia = fatia.iloc[[0]].copy()
            copia["TEMPO_VOO"] = copia["TEMPO_VOO"] + 444
            fatia = pd.concat([fatia, copia], ignore_index=True)
        escrever(nome, fatia)

    for nome in dict.fromkeys(PERFIL_DO_BLOCO):
        blocos = [i for i, p in enumerate(PERFIL_DO_BLOCO) if p == nome]
        escrever(nome, perfil[base["BLOCO"].isin(blocos).to_numpy()])

    escrever("INFORMACAO_VIAGEM", viagem)
    escrever("DISTRIBUICAO_PAX_NORMALIZADO", _distribuicao(rng))

    analitica = preparar_base_analitica(integrar_bases(saida)[0])
    analitica.to_parquet(saida / BASE_ANALITICA, index=False)
    escritos[BASE_ANALITICA] = len(analitica)
    return escritos


def conferir(real: Path | str = "data/raw", dummy: Path | str = SAIDA_PADRAO) -> bool:
    """Compara colunas, tipos e volume contra a base analítica real e suas fontes.

    É a evidência dos critérios de aceite, e não um teste da suíte: exige o dado
    do parceiro em disco e lê os arquivos inteiros, porque o tipo de
    `ID_GOLDENRECORD` e `TEMPO_VOO` depende de ausências raras demais para
    aparecerem em uma amostra das primeiras linhas.
    """
    real, dummy = Path(real), Path(dummy)
    ok = True

    def comparar(nome, r, d):
        nonlocal ok
        colunas = list(r.columns) == list(d.columns)
        tipos = {c: (str(r[c].dtype), str(d[c].dtype))
                 for c in r.columns if colunas and r[c].dtype != d[c].dtype}
        ok = ok and colunas and not tipos
        print(f"{nome:48s} {len(d):6d}/{len(r):7d} = {len(d) / len(r):6.2%}"
              f"  colunas={'ok' if colunas else 'DIVERGEM'}"
              f"  tipos={'ok' if not tipos else tipos}")

    if BASE_ANALITICA_REAL.exists():
        comparar(BASE_ANALITICA, pd.read_parquet(BASE_ANALITICA_REAL),
                 pd.read_parquet(dummy / BASE_ANALITICA))
    else:
        print(f"{BASE_ANALITICA}: sem contraparte em {BASE_ANALITICA_REAL}, não conferida")

    for arquivo in sorted(real.glob("PROJETO_INTELI.*.csv")):
        comparar(arquivo.name, pd.read_csv(arquivo, low_memory=False),
                 pd.read_csv(dummy / arquivo.name, low_memory=False))

    print("CONFERE" if ok else "NÃO CONFERE")
    return ok


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--saida", default=SAIDA_PADRAO, type=Path)
    p.add_argument("--conferir", metavar="DIR_REAL", nargs="?", const="data/raw",
                   help="compara o dummy já gerado com a base real e sai")
    args = p.parse_args()

    if args.conferir:
        raise SystemExit(0 if conferir(args.conferir, args.saida) else 1)

    for nome, linhas in gerar(args.saida).items():
        print(f"{nome:34s} {linhas:7d} linha(s)")
    print(f"\nEscrito em {args.saida.resolve()}")
    print(f"Use com:  pd.read_parquet('{args.saida / BASE_ANALITICA}')")
    print(f"   ou:    carregar_bases('{args.saida}'), para testar a integração")
