"""Testes do mapeamento de coeficiente para feature original (card #212).

O que se testa aqui e o lugar onde o calculo de odds ratio erra em silencio: a
volta da coluna da matriz para a variavel do contrato. Um mapeamento deslocado
em uma posicao nao levanta erro nenhum, produz uma tabela inteira com numeros
plausiveis, e so aparece quando alguem estranha o sinal de uma variavel.

O pre-processador vem de `matriz._montar_preprocessador`, o mesmo que o contrato
usa, e nao de uma copia montada aqui: uma copia passaria a concordar consigo
mesma no dia em que o contrato mudasse de estrutura.

Executar com:  pytest tests/test_odds_ratio.py -v
"""
import numpy as np
import pandas as pd
import pytest
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from matriz import _montar_preprocessador
from odds_ratio import efeito_acumulado, mapear_colunas, odds_ratio

NUMERICAS = ["ATRASO", "TEMPO"]
CATEGORICAS = ["CANAL", "TIER"]


@pytest.fixture
def dados():
    """Duas numericas, uma delas com ausencia, e duas categoricas."""
    rng = np.random.default_rng(42)
    n = 200
    return pd.DataFrame({
        "ATRASO": rng.integers(0, 120, n).astype("float64"),
        # so esta tem ausencia: o indicador tem que sair so para ela
        "TEMPO": pd.Series(rng.integers(40, 300, n), dtype="float64").mask(rng.random(n) < 0.2),
        "CANAL": rng.choice(["WEB", "MOBILE", "AGENCY"], n),
        "TIER": rng.choice(["SAFIRA", "DIAMANTE"], n),
    })


@pytest.fixture
def ajustado(dados):
    rng = np.random.default_rng(7)
    y = pd.Series(rng.integers(0, 2, len(dados)))
    pipeline = Pipeline([
        ("preparo", _montar_preprocessador(NUMERICAS, CATEGORICAS)),
        ("modelo", LogisticRegression(max_iter=1000, random_state=42)),
    ])
    pipeline.fit(dados, y)
    return pipeline


@pytest.fixture
def mapa(ajustado):
    return mapear_colunas(ajustado.named_steps["preparo"])


def test_mapa_cobre_todas_as_colunas_da_matriz(ajustado, mapa):
    """Uma linha por coluna de saida, na mesma ordem."""
    nomes = list(ajustado.named_steps["preparo"].get_feature_names_out())
    assert list(mapa["coluna_matriz"]) == nomes


def test_cada_nivel_categorico_vira_uma_linha(ajustado, mapa):
    """`drop=None`, entao todos os niveis entram, e cada um aponta para sua variavel."""
    codificador = (ajustado.named_steps["preparo"]
                   .named_transformers_["categoricas"].named_steps["codificar"])
    for coluna, niveis in zip(CATEGORICAS, codificador.categories_):
        linhas = mapa[(mapa["feature_original"] == coluna) & (mapa["tipo"] == "categorica")]
        assert sorted(linhas["nivel"]) == sorted(str(n) for n in niveis)


def test_indicador_de_ausencia_aponta_para_a_variavel_certa(mapa):
    """O indicador mede a ausencia de TEMPO, e nao a ausencia de ATRASO."""
    ausencias = mapa[mapa["tipo"] == "ausencia"]
    assert list(ausencias["feature_original"]) == ["TEMPO"]
    assert ausencias["coluna_matriz"].str.contains("missingindicator_TEMPO").all()


def test_nenhum_nome_gerado_pelo_columntransformer_vaza(mapa):
    """CR01: a coluna de feature traz a variavel do contrato, nunca o nome da saida."""
    assert not mapa["feature_original"].str.contains("__").any()
    assert not mapa["feature_original"].str.startswith("missingindicator_").any()
    assert set(mapa["feature_original"]) == set(NUMERICAS + CATEGORICAS)


def test_mapeamento_deslocado_levanta_em_vez_de_rotular_errado(ajustado, monkeypatch):
    """A trava existe porque o erro desta funcao e silencioso por natureza."""
    preparo = ajustado.named_steps["preparo"]
    nomes = list(preparo.get_feature_names_out())
    monkeypatch.setattr(type(preparo), "get_feature_names_out",
                        lambda self, input_features=None: np.array(nomes[1:] + ["extra"]))
    with pytest.raises(ValueError, match="get_feature_names_out"):
        mapear_colunas(preparo)


def test_odds_ratio_e_a_exponencial_do_coeficiente(ajustado):
    tabela = odds_ratio(ajustado)
    assert len(tabela) == ajustado.named_steps["modelo"].coef_.size
    assert np.allclose(tabela["odds_ratio"], np.exp(tabela["coeficiente"]))
    assert tabela["odds_ratio"].is_monotonic_decreasing


def test_odds_ratio_por_unidade_desfaz_o_escalonamento(ajustado):
    """Nas numericas, `exp(coef)` e por IQR; a coluna por unidade divide de volta."""
    tabela = odds_ratio(ajustado)
    numericas = tabela[tabela["tipo"] == "numerica"]
    assert numericas["iqr_do_treino"].notna().all()
    assert np.allclose(numericas["odds_ratio_por_unidade"],
                       np.exp(numericas["coeficiente"] / numericas["iqr_do_treino"]))
    # Categoricas e indicadores ja sao 0/1: as duas leituras coincidiriam.
    assert tabela.loc[tabela["tipo"] != "numerica", "odds_ratio_por_unidade"].isna().all()


def test_efeito_acumulado_compoe_multiplicativamente(ajustado):
    """Um odds ratio por minuto so vira leitura na escala em que a operacao decide."""
    assert efeito_acumulado(1.0028, 60) == pytest.approx(1.0028 ** 60)
    assert efeito_acumulado(1.0, 999) == pytest.approx(1.0)
