"""Pré-processamento reprodutível da base NPS.

O módulo separa o diagnóstico (feito sobre a base integrada) das transformações
para modelagem. Imputação, codificação e escala são ajustadas somente no treino.
"""

from __future__ import annotations

from pathlib import Path
import re

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, RobustScaler


PADROES = {
    "nps": re.compile(r"NPS[_ .-]", re.IGNORECASE),
    "perfil": re.compile(r"PERFIL_CLIENTE", re.IGNORECASE),
    "viagem": re.compile(r"INFORMACAO_VIAGEM", re.IGNORECASE),
}
EXTENSOES = {".csv", ".xlsx", ".parquet"}
PRIORIDADE_FORMATO = {".parquet": 0, ".csv": 1, ".xlsx": 2}


def ler_arquivo(caminho: Path) -> pd.DataFrame:
    """Lê CSV, Excel ou Parquet sem supor um nome completo de arquivo."""
    if caminho.suffix.lower() == ".csv":
        return pd.read_csv(caminho)
    if caminho.suffix.lower() == ".xlsx":
        # Calamine é substancialmente mais rápido em planilhas grandes. O
        # fallback mantém compatibilidade com ambientes que só têm openpyxl.
        try:
            return pd.read_excel(caminho, engine="calamine")
        except ImportError:
            return pd.read_excel(caminho, engine="openpyxl")
    if caminho.suffix.lower() == ".parquet":
        return pd.read_parquet(caminho)
    raise ValueError(f"Formato não suportado: {caminho}")


def descobrir_fontes(diretorio: str | Path = "data/raw") -> dict[str, list[Path]]:
    """Descobre as fontes e prefere um formato por parte lógica.

    Quando existem CSV e XLSX da mesma parte, ambos são comparados antes de o
    formato prioritário ser usado. Assim, não há concatenação duplicada.
    """
    diretorio = Path(diretorio)
    # Path.iterdir() não garante ordem alguma, e a ordem obtida aqui define a ordem em que as
    # partições são concatenadas e, por consequência, a ordem das linhas da base analítica. Sem
    # ordenar, a mesma base sai com linhas em posições diferentes em cada máquina, e qualquer
    # artefato que dependa de posição muda em silêncio. Ordenar pelo nome torna a base idêntica
    # em qualquer ambiente.
    arquivos = sorted(
        (p for p in diretorio.iterdir() if p.suffix.lower() in EXTENSOES),
        key=lambda caminho: caminho.name.upper(),
    )
    grupos = {nome: [] for nome in PADROES}
    for arquivo in arquivos:
        nome = arquivo.name.upper()
        if "DISTRIBUICAO_PAX_NORMALIZADO" in nome:
            continue
        for grupo, padrao in PADROES.items():
            if padrao.search(nome):
                grupos[grupo].append(arquivo)
                break

    for grupo, encontrados in grupos.items():
        if not encontrados:
            raise FileNotFoundError(f"Nenhum arquivo encontrado para o grupo {grupo}.")
    return grupos


def _chave_parte(caminho: Path) -> str:
    return caminho.stem.replace(" ", "_").replace(".", "_").upper()


def selecionar_partes(arquivos: list[Path]) -> tuple[list[Path], list[Path]]:
    """Compara cópias da mesma parte e retorna arquivos usados e ignorados."""
    por_parte: dict[str, list[Path]] = {}
    for arquivo in arquivos:
        por_parte.setdefault(_chave_parte(arquivo), []).append(arquivo)

    usados, ignorados = [], []
    for parte, alternativas in por_parte.items():
        alternativas.sort(key=lambda p: PRIORIDADE_FORMATO[p.suffix.lower()])
        escolhido = alternativas[0]
        if len(alternativas) == 1:
            usados.append(escolhido)
            continue
        referencia = ler_arquivo(escolhido)
        for alternativa in alternativas[1:]:
            comparacao = ler_arquivo(alternativa)
            if not referencia.equals(comparacao):
                raise ValueError(
                    f"Cópias divergentes para {parte}: {escolhido.name} e "
                    f"{alternativa.name}. Decida qual deve ser usada."
                )
            ignorados.append(alternativa)
        usados.append(escolhido)
    return usados, ignorados


def relatorio_chave(df: pd.DataFrame, nome: str) -> dict[str, object]:
    if "RESPONDENT_ID" not in df:
        raise KeyError(f"{nome} não possui RESPONDENT_ID.")
    return {
        "tabela": nome,
        "linhas": len(df),
        "colunas": len(df.columns),
        "ids_unicos": df["RESPONDENT_ID"].nunique(),
        "ids_nulos": int(df["RESPONDENT_ID"].isna().sum()),
        "ids_duplicados": int(df["RESPONDENT_ID"].duplicated().sum()),
    }


def consolidar_duplicidades_tempo_voo(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Consolida somente cópias iguais exceto por ``TEMPO_VOO``.

    A regra é específica ao caso aprovado: uma única resposta por
    ``RESPONDENT_ID`` e duas medições divergentes de duração. O valor final é a
    média aritmética; qualquer outra divergência permanece um erro bloqueante.
    """
    if "TEMPO_VOO" not in df.columns:
        raise KeyError("A regra de consolidação exige a coluna TEMPO_VOO.")

    resultado = df.copy()
    resultado["TEMPO_VOO_CONSOLIDADO"] = 0
    ids_duplicados = resultado.loc[
        resultado["RESPONDENT_ID"].duplicated(keep=False), "RESPONDENT_ID"
    ].dropna().unique()
    colunas_comparacao = [
        coluna for coluna in resultado.columns
        if coluna not in {"RESPONDENT_ID", "TEMPO_VOO", "TEMPO_VOO_CONSOLIDADO"}
    ]
    remover = []

    for respondent_id in ids_duplicados:
        indices = resultado.index[resultado["RESPONDENT_ID"] == respondent_id]
        grupo = resultado.loc[indices]
        divergentes = [
            coluna for coluna in colunas_comparacao
            if grupo[coluna].nunique(dropna=False) > 1
        ]
        if divergentes:
            raise ValueError(
                f"RESPONDENT_ID {respondent_id} possui divergências além de TEMPO_VOO: "
                f"{divergentes}. A integração foi bloqueada."
            )
        valores_tempo = pd.to_numeric(grupo["TEMPO_VOO"], errors="coerce")
        if valores_tempo.notna().sum() != len(grupo):
            raise ValueError(
                f"RESPONDENT_ID {respondent_id} tem TEMPO_VOO nulo ou inválido; "
                "não é possível aplicar a média com segurança."
            )
        indice_manter = indices[0]
        resultado.loc[indice_manter, "TEMPO_VOO"] = valores_tempo.mean()
        resultado.loc[indice_manter, "TEMPO_VOO_CONSOLIDADO"] = 1
        remover.extend(indices[1:])

    resultado = resultado.drop(index=remover).reset_index(drop=True)
    return resultado, len(ids_duplicados)


def remover_colunas_redundantes(
    esquerda: pd.DataFrame, direita: pd.DataFrame, nome_direita: str
) -> tuple[pd.DataFrame, list[str]]:
    """Remove colunas repetidas somente quando forem iguais por respondente."""
    repetidas = (set(esquerda.columns) & set(direita.columns)) - {"RESPONDENT_ID"}
    remover = []
    for coluna in sorted(repetidas):
        comparacao = esquerda[["RESPONDENT_ID", coluna]].merge(
            direita[["RESPONDENT_ID", coluna]],
            on="RESPONDENT_ID",
            how="inner",
            validate="one_to_one",
            suffixes=("_esquerda", "_direita"),
        )
        esquerda_valor = comparacao[f"{coluna}_esquerda"]
        direita_valor = comparacao[f"{coluna}_direita"]
        equivalentes = (esquerda_valor.eq(direita_valor) |
                         (esquerda_valor.isna() & direita_valor.isna()))
        if not equivalentes.all():
            raise ValueError(
                f"A coluna repetida {coluna} diverge entre NPS e {nome_direita}; "
                "a integração foi bloqueada para investigação."
            )
        remover.append(coluna)
    if remover:
        print(f"{nome_direita}: colunas redundantes comprovadamente equivalentes e removidas: {remover}")
    return direita.drop(columns=remover), remover


def integrar_bases(diretorio: str | Path = "data/raw") -> tuple[pd.DataFrame, pd.DataFrame]:
    """Integra as bases com consolidação auditável do caso aprovado de duplicidade."""
    grupos = descobrir_fontes(diretorio)
    tabelas: dict[str, pd.DataFrame] = {}
    relatorios = []
    for grupo, arquivos in grupos.items():
        usados, ignorados = selecionar_partes(arquivos)
        print(f"{grupo}: usados={[p.name for p in usados]}; ignorados={[p.name for p in ignorados]}")
        tabela = pd.concat([ler_arquivo(p) for p in usados], ignore_index=True)
        duplicados_antes = int(tabela["RESPONDENT_ID"].duplicated().sum())
        consolidados = 0
        if grupo == "nps" and duplicados_antes:
            tabela, consolidados = consolidar_duplicidades_tempo_voo(tabela)
            print(f"nps: {consolidados} RESPONDENT_ID duplicado(s) consolidado(s) pela média de TEMPO_VOO.")
        relatorio = relatorio_chave(tabela, grupo)
        relatorio["ids_duplicados_antes"] = duplicados_antes
        relatorio["ids_consolidados_tempo_voo"] = consolidados
        relatorios.append(relatorio)
        if tabela["RESPONDENT_ID"].duplicated().any():
            raise ValueError(
                f"{grupo} possui RESPONDENT_ID duplicado. O merge one_to_one foi bloqueado; "
                "aprove uma regra de deduplicação antes de persistir a base final."
            )
        tabelas[grupo] = tabela

    perfil_sem_redundancias, removidas_perfil = remover_colunas_redundantes(
        tabelas["nps"], tabelas["perfil"], "perfil"
    )
    integrado = tabelas["nps"].merge(perfil_sem_redundancias, on="RESPONDENT_ID", validate="one_to_one")
    viagem_sem_redundancias, removidas_viagem = remover_colunas_redundantes(
        integrado, tabelas["viagem"], "viagem"
    )
    integrado = integrado.merge(viagem_sem_redundancias, on="RESPONDENT_ID", validate="one_to_one")
    print(f"Colunas redundantes removidas após comparação: {removidas_perfil + removidas_viagem}")
    return integrado, pd.DataFrame(relatorios)


def perfil_qualidade(df: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame({
        "coluna": df.columns,
        "tipo": df.dtypes.astype(str).to_numpy(),
        "nulos": df.isna().sum().to_numpy(),
        "percentual_nulos": (df.isna().mean() * 100).round(2).to_numpy(),
        "valores_unicos": df.nunique(dropna=True).to_numpy(),
    }).sort_values(["percentual_nulos", "valores_unicos"], ascending=False)


def identificar_outliers_iqr(df: pd.DataFrame, colunas: list[str]) -> pd.DataFrame:
    registros = []
    for coluna in colunas:
        serie = pd.to_numeric(df[coluna], errors="coerce").dropna()
        q1, q3 = serie.quantile([0.25, 0.75])
        iqr = q3 - q1
        limite_superior = q3 + 1.5 * iqr
        limite_inferior = q1 - 1.5 * iqr
        registros.append({
            "variavel": coluna, "q1": q1, "q3": q3, "p95": serie.quantile(.95),
            "p99": serie.quantile(.99), "min": serie.min(), "max": serie.max(),
            "outliers_iqr": int(((serie < limite_inferior) | (serie > limite_superior)).sum()),
        })
    return pd.DataFrame(registros).round(2)


def padronizar_categoricas(df: pd.DataFrame) -> pd.DataFrame:
    """Padroniza espaços e caixa sem preencher nulos ou inventar categorias."""
    resultado = df.copy()
    for coluna in resultado.select_dtypes(include=["object", "string"]):
        resultado[coluna] = resultado[coluna].str.strip().str.upper().str.replace(r"\s+", " ", regex=True)
    return resultado


def preparar_base_analitica(df_raw: pd.DataFrame) -> pd.DataFrame:
    """Aplica somente correções semanticamente justificadas e preserva nulos."""
    df = padronizar_categoricas(df_raw)
    df["DATA_STD_CONVERTIDA"] = pd.to_datetime(df["DATA_STD"], format="mixed", errors="coerce")
    df["MES_ANO"] = df["DATA_STD_CONVERTIDA"].dt.to_period("M").astype("string")
    df["DETRATOR"] = (df["NPS_PRINCIPAL"] == -100).astype("int8")
    df["CATEGORIA_NPS"] = df["NPS_PRINCIPAL"].map({
        -100: "DETRATOR", 0: "NEUTRO", 100: "PROMOTOR"
    }).astype("string")
    df["TEMPO_VOO_INVALIDO"] = (df["TEMPO_VOO"] <= 0).astype("int8")
    df.loc[df["TEMPO_VOO"] <= 0, "TEMPO_VOO"] = np.nan
    return df


def dividir_treino_teste_temporal_por_cliente(
    df: pd.DataFrame,
    proporcao_teste: float = .2,
) -> tuple[pd.Index, pd.Index, dict[str, object]]:
    """Reserva os meses mais recentes para teste sem repetir Clientes.

    O corte é temporal, em vez de aleatório: o teste contém os últimos meses
    disponíveis. Para impedir vazamento entre respostas recorrentes, todo
    ``ID_GOLDENRECORD`` que ocorre no teste é retirado também do treino.
    """
    colunas_obrigatorias = {"DATA_STD_CONVERTIDA", "ID_GOLDENRECORD"}
    ausentes = colunas_obrigatorias - set(df.columns)
    if ausentes:
        raise KeyError(f"A divisão exige as colunas: {sorted(ausentes)}.")
    if not 0 < proporcao_teste < 1:
        raise ValueError("proporcao_teste deve estar entre 0 e 1.")

    datas = pd.to_datetime(df["DATA_STD_CONVERTIDA"], errors="coerce")
    if datas.isna().any():
        raise ValueError("DATA_STD_CONVERTIDA possui valores inválidos; corrija-os antes do split.")
    grupos = df["ID_GOLDENRECORD"]
    if grupos.isna().any():
        raise ValueError("ID_GOLDENRECORD possui nulos; não é seguro dividir por Cliente.")

    meses = datas.dt.to_period("M")
    meses_ordenados = meses.sort_values().unique()
    meses_teste = max(1, int(np.ceil(len(meses_ordenados) * proporcao_teste)))
    primeiro_mes_teste = meses_ordenados[-meses_teste]
    mascara_teste = meses >= primeiro_mes_teste
    clientes_teste = set(grupos.loc[mascara_teste])
    mascara_treino = (meses < primeiro_mes_teste) & ~grupos.isin(clientes_teste)

    if not mascara_treino.any() or not mascara_teste.any():
        raise ValueError("A divisão temporal não produziu treino e teste não vazios.")
    if set(grupos.loc[mascara_treino]) & clientes_teste:
        raise AssertionError("Há Cliente presente simultaneamente no treino e no teste.")

    metadados = {
        "primeiro_mes_teste": str(primeiro_mes_teste),
        "ultimo_mes_teste": str(meses.max()),
        "linhas_removidas_por_recorrencia": int(((meses < primeiro_mes_teste) & grupos.isin(clientes_teste)).sum()),
        "clientes_treino": int(grupos.loc[mascara_treino].nunique()),
        "clientes_teste": int(grupos.loc[mascara_teste].nunique()),
    }
    return df.index[mascara_treino], df.index[mascara_teste], metadados


def criar_folds_validacao_por_cliente(
    x_treino: pd.DataFrame, grupos_treino: pd.Series, n_splits: int = 5,
):
    """Gera folds de validação sem que um Cliente apareça em dois folds."""
    if grupos_treino.isna().any():
        raise ValueError("A validação por grupo exige ID_GOLDENRECORD sem nulos.")
    if grupos_treino.nunique() < n_splits:
        raise ValueError("Há Clientes insuficientes para a quantidade de folds solicitada.")
    return GroupKFold(n_splits=n_splits).split(x_treino, groups=grupos_treino)


def criar_preprocessador_modelagem(df: pd.DataFrame):
    """Cria e ajusta o pré-processador somente nos dados de treino.

    Nulos estruturais recebem categoria explícita apenas na matriz do modelo;
    a base analítica permanece com os nulos originais.
    """
    alvo = "DETRATOR"
    excluir = [
        alvo, "NPS_PRINCIPAL", "CATEGORIA_NPS", "RESPONDENT_ID", "CLIENTE_RECORDLOCATOR", "DATA_STD",
        "DATA_STD_CONVERTIDA", "MES_ANO",
    ]
    excluir.extend(c for c in df.columns if c.startswith("NPS_") or c.startswith("SUB_"))
    candidatos = df.drop(columns=excluir, errors="ignore")
    categoricas = [c for c in candidatos.select_dtypes(include=["object", "string", "category", "bool"])
                    if candidatos[c].nunique(dropna=True) <= 100]
    numericas = [c for c in candidatos.select_dtypes(include=[np.number]).columns
                 if candidatos[c].nunique(dropna=True) <= 1000]
    x = candidatos[categoricas + numericas]
    y = df[alvo]
    indices_treino, indices_teste, metadados_divisao = dividir_treino_teste_temporal_por_cliente(df)
    x_treino, x_teste = x.loc[indices_treino], x.loc[indices_teste]
    y_treino, y_teste = y.loc[indices_treino], y.loc[indices_teste]
    pipeline_numerico = Pipeline([
        ("imputar", SimpleImputer(strategy="median", add_indicator=True)),
        ("escalar", RobustScaler()),
    ])
    pipeline_categorico = Pipeline([
        ("imputar", SimpleImputer(strategy="constant", fill_value="NAO_INFORMADO")),
        ("codificar", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
    ])
    preprocessador = ColumnTransformer([
        ("numericas", pipeline_numerico, numericas),
        ("categoricas", pipeline_categorico, categoricas),
    ], remainder="drop")
    x_treino_transformado = preprocessador.fit_transform(x_treino)
    x_teste_transformado = preprocessador.transform(x_teste)
    return preprocessador, (x_treino, x_teste, y_treino, y_teste), (x_treino_transformado, x_teste_transformado), (numericas, categoricas), metadados_divisao
