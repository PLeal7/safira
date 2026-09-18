"""Testes do baseline dummy da base analítica.

O que se testa aqui não é a semelhança estatística com o dado real, e sim que o
dummy cumpre os contratos que o projeto já impõe à base analítica de verdade, e
que atravessa o pipeline até a matriz de modelagem.

As validações usadas são as do próprio projeto — `validar_schema_features_v1`,
as travas de `clean`, `preparar_matriz` — e não cópias delas escritas para o
teste. Uma cópia passaria a concordar consigo mesma no dia em que o contrato
mudasse; estas param junto com o pipeline.

A conferência de colunas e tipos contra `data/processed/base_analitica.parquet`
fica fora da suíte, em `gerar_dummy.conferir`, porque exige o dado do parceiro.

Executar com:  pytest tests/test_dummy.py -v
"""
import pandas as pd
import pytest

import clean
import features
import matriz
from gerar_dummy import (BASE_ANALITICA, COLUNAS_NPS, COLUNAS_PERFIL,
                         COLUNAS_VIAGEM, PRIMEIRO_ID, gerar)
from preprocessamento_nps import validar_parquet, validar_schema_features_v1

# Fração pequena: o que se verifica é estrutura, não volume.
FRACAO_TESTE = 0.01
# Os mesmos cortes da política de particionamento temporal do projeto.
CORTE_VALIDACAO, CORTE_TESTE = "2025-07-01", "2026-01-01"


@pytest.fixture(scope="module")
def dummy(tmp_path_factory):
    destino = tmp_path_factory.mktemp("dummy")
    gerar(destino, fracao=FRACAO_TESTE)
    return destino


@pytest.fixture(scope="module")
def base(dummy):
    return pd.read_parquet(dummy / BASE_ANALITICA)


@pytest.fixture(scope="module")
def fontes(dummy):
    return clean.carregar_bases(dummy)


def test_parquet_da_base_analitica_e_legivel(dummy):
    validar_parquet(dummy / BASE_ANALITICA)


def test_base_analitica_cumpre_o_contrato_de_features_v1(base):
    """A trava que o projeto aplica à base real aceita a dummy sem ressalva."""
    validar_schema_features_v1(base)


def test_base_analitica_traz_as_derivadas_do_preparo(base):
    """As derivadas vêm de `preparar_base_analitica`, não de um esquema copiado."""
    assert base["DETRATOR"].isin((0, 1)).all()
    assert (base["DETRATOR"] == (base["NPS_PRINCIPAL"] == -100)).all()
    assert base["CATEGORIA_NPS"].isin(("DETRATOR", "NEUTRO", "PROMOTOR")).all()
    assert (base["DATA_STD_CONVERTIDA"] == base["DATA_STD"]).all()
    assert (base["MES_ANO"] == base["DATA_STD"].dt.to_period("M").astype("string")).all()
    # Categóricas padronizadas em caixa alta, como na base real.
    assert base["VOO_TIPO"].isin(("DIRETO", "CONEXÃO", "ESCALA")).all()
    # N_TRECHOS cobre a mesma faixa do real, incluindo os itinerários longos raros.
    assert base["N_TRECHOS"].between(1, 6).all()
    assert base["N_TRECHOS"].max() > 2


def test_base_analitica_atravessa_o_particionamento_e_a_matriz(base):
    """Ponta a ponta até a matriz, com os cortes temporais do projeto."""
    preparo = matriz.preparar_matriz(base, corte_validacao=CORTE_VALIDACAO,
                                     corte_teste=CORTE_TESTE)
    for nome, particao in preparo["particoes"].items():
        assert len(particao) > 0, f"partição {nome} vazia"


def test_fontes_tem_as_colunas_e_a_ordem_do_contrato(fontes):
    nps, perfil, viagem = fontes
    assert list(nps.columns) == list(COLUNAS_NPS)
    assert list(perfil.columns) == list(COLUNAS_PERFIL)
    assert list(viagem.columns) == list(COLUNAS_VIAGEM)


def test_integracao_das_fontes_atravessa_sem_afrouxar_validacao(dummy, fontes):
    """As travas de `clean` ligadas, que é como o notebook roda."""
    df = clean.derivar(clean.integrar(*fontes))
    df = clean.pesos_pos_estratificacao(df, clean.carregar_populacao(dummy))

    assert len(df) == len(fontes[0].drop_duplicates("RESPONDENT_ID"))
    assert df["PESO_POP"].gt(0).all()
    # Um aeroporto a mais que trechos, e um assento por trecho — exceto nas
    # poucas linhas em que ASSENTOS vem ausente, como no dado real.
    assinalado = df["ASSENTOS"].notna()
    assert (df.loc[assinalado, "N_ASSENTOS_AUDIT"] == df.loc[assinalado, "N_TRECHOS"]).all()


def test_duplicata_aprovada_de_nps_04_chega_ate_a_deduplicacao(fontes):
    """O dummy carrega o caso que `clean.deduplicar` existe para tratar."""
    divergentes = clean.duplicatas_divergentes(fontes[0])
    assert divergentes != {}
    assert all(colunas == ["TEMPO_VOO"] for colunas in divergentes.values())


def test_historico_por_cliente_tem_o_que_enxergar(fontes):
    """Sem reincidência de ID_GOLDENRECORD as features de histórico nasceriam vazias."""
    df = features.adicionar_historico(clean.derivar(clean.integrar(*fontes)))
    assert df["HIST_RESPOSTAS_ANTERIORES"].gt(0).any()
    assert df["HIST_DETRATOU_ANTES"].notna().any()
    # A ordem por chave tem que reproduzir a cronologia, como no dado real.
    ordem = df["RESPONDENT_ID"].corr(df["DATA_STD"].astype("int64"), method="spearman")
    assert ordem > 0.999


def test_nenhum_identificador_real_no_dummy(base, fontes):
    """CR04: as chaves são de uma faixa própria, disjunta da do dado real."""
    for df in (base, *fontes):
        assert df["RESPONDENT_ID"].min() >= PRIMEIRO_ID
        assert df["RESPONDENT_ID"].max() < 28_211_922  # menor RESPONDENT_ID real


def test_populacao_cobre_todo_mes_da_amostra(dummy, base):
    """Estrato sem contrapartida populacional é condição de parada em `clean`."""
    dist = clean.carregar_populacao(dummy)
    assert set(base["MES_ANO"]) <= set(dist["MES_ANO"].dt.strftime("%Y-%m"))
