"""Testes da figura de dependencia parcial (#192).

Como nos testes das curvas (#107), o que se protege aqui nao e a aparencia da
figura: e o que faria ela afirmar algo falso sem quebrar nada.

1. Categorica desenhada como eixo continuo. Uma linha ligando tiers sugere
   ordem e valores intermediarios que nao existem (CR02).
2. Paineis diferentes do ranking. A figura tem de mostrar exatamente as
   features pedidas, na ordem pedida (CR01).
3. Grade que ignora a feature. Uma coluna com ausentes, como
   `ANTECEDENCIA_CANCELAMENTO`, saia com a grade inteira em NaN e um painel
   vazio; uma grade passada pelo nome da feature era ignorada sem aviso.
4. Faixa de mudanca fora do lugar. O dado sintetico tem um degrau conhecido,
   e a faixa que o texto do notebook cita tem de conte-lo (CR05).
5. Entrada que produziria uma figura valida e errada: pipeline sem ajuste,
   matriz ja transformada, alvo que nao e Detrator = 1.

Todos usam dados sinteticos, sem tocar nas bases da Azul (CR04).

Executar com:  pytest tests/test_graficos_dependencia_parcial.py -v
"""
import matplotlib
import numpy as np
import pandas as pd
import pytest
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.exceptions import NotFittedError
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

matplotlib.use("Agg")

import graficos as gr  # noqa: E402

LIMIAR_ATRASO = 30
TIER_ARRISCADO = "Sem cadastro"
NUMERICAS = ["ATRASO_CHEGADA", "ANTECEDENCIA_CANCELAMENTO", "N_TRECHOS"]
CATEGORICAS = ["TIER_VIAGEM", "CANCELAMENTO_VOO"]


def _pipeline(random_state=42):
    preparo = ColumnTransformer([
        ("numericas", SimpleImputer(strategy="median", add_indicator=True), NUMERICAS),
        ("categoricas", Pipeline([
            ("imputacao", SimpleImputer(strategy="most_frequent")),
            ("one_hot", OneHotEncoder(handle_unknown="ignore")),
        ]), CATEGORICAS),
    ])
    modelo = RandomForestClassifier(n_estimators=40, max_depth=5, random_state=random_state, n_jobs=1)
    return Pipeline([("preparo", preparo), ("modelo", modelo)])


@pytest.fixture(scope="module")
def dados():
    """Matriz crua com os dtypes do contrato e um efeito conhecido no alvo.

    O risco salta quando o atraso passa de 30 minutos e sobe para quem nao tem
    cadastro; antecedencia de cancelamento e ruido, e ausente em 80% das linhas,
    como na base real.
    """
    rng = np.random.default_rng(42)
    n = 3000
    x = pd.DataFrame({
        "ATRASO_CHEGADA": rng.uniform(0, 120, n),
        "TIER_VIAGEM": pd.Series(rng.choice(["Diamante", "Safira", TIER_ARRISCADO], n), dtype="string"),
        "CANCELAMENTO_VOO": rng.random(n) < 0.2,
        "ANTECEDENCIA_CANCELAMENTO": np.where(rng.random(n) < 0.2, rng.uniform(0, 10, n), np.nan),
        "N_TRECHOS": rng.integers(1, 4, n),
    })
    atrasado = x["ATRASO_CHEGADA"].to_numpy() > LIMIAR_ATRASO
    sem_cadastro = x["TIER_VIAGEM"].to_numpy(dtype=object) == TIER_ARRISCADO
    risco = 0.1 + 0.5 * atrasado + 0.2 * sem_cadastro
    y = (rng.random(n) < risco).astype(int)
    return x, y


@pytest.fixture(scope="module")
def ajustado(dados):
    x, y = dados
    return _pipeline().fit(x, y)


@pytest.fixture(scope="module")
def resultado(ajustado, dados):
    x, _ = dados
    return gr.dependencia_parcial(ajustado, x, ["ATRASO_CHEGADA", "TIER_VIAGEM", "ANTECEDENCIA_CANCELAMENTO"])


def test_categoricas_saem_do_dtype_como_no_contrato(dados):
    x, _ = dados
    assert gr.colunas_categoricas(x, x.columns) == CATEGORICAS


def test_paineis_sao_as_features_pedidas_na_ordem(resultado):
    """CR01: o painel i e a i-esima feature do ranking, nem mais nem menos."""
    fig, tabela = resultado
    assert len(fig.axes) == 3
    assert list(tabela["feature"].unique()) == ["ATRASO_CHEGADA", "TIER_VIAGEM", "ANTECEDENCIA_CANCELAMENTO"]
    for i, (ax, feature) in enumerate(zip(fig.axes, tabela["feature"].unique()), 1):
        assert ax.get_title(loc="left") == f"{i}º do ranking: {feature}"


def test_categorica_vira_barras_e_continua_vira_linha(resultado):
    """CR02: uma barra por categoria, rotulada pela categoria, e nenhuma linha."""
    fig, _ = resultado
    ax_atraso, ax_tier, _ = fig.axes

    assert len(ax_tier.patches) == 3
    assert len(ax_tier.get_lines()) == 0
    assert [t.get_text() for t in ax_tier.get_xticklabels()] == ["Diamante", "Safira", TIER_ARRISCADO]

    assert len(ax_atraso.patches) == 0
    assert len(ax_atraso.get_lines()) == 1


def test_booleana_tambem_vira_barras_rotuladas(ajustado, dados):
    """CANCELAMENTO_VOO e bool: o eixo nao pode mostrar 0,0 / 0,5 / 1,0."""
    x, _ = dados
    fig, _ = gr.dependencia_parcial(ajustado, x, ["CANCELAMENTO_VOO"])
    ax = fig.axes[0]
    assert len(ax.patches) == 2
    assert [t.get_text() for t in ax.get_xticklabels()] == ["False", "True"]


def test_categorica_explicita_sobrepoe_o_dtype(ajustado, dados):
    """N_TRECHOS e inteiro; quem quiser barras por trecho pode pedir."""
    x, _ = dados
    fig, tabela = gr.dependencia_parcial(ajustado, x, ["N_TRECHOS"], categoricas=["N_TRECHOS"])
    assert len(fig.axes[0].patches) == 3
    assert tabela["categorica"].all()


def test_grade_da_continua_fica_entre_os_percentis(resultado, dados):
    x, _ = dados
    _, tabela = resultado
    grade = tabela.loc[tabela["feature"] == "ATRASO_CHEGADA", "valor"].to_numpy(dtype=float)
    inicio, fim = np.quantile(x["ATRASO_CHEGADA"], gr.PERCENTIS_DEPENDENCIA)
    assert len(grade) == gr.GRADE_DEPENDENCIA
    assert grade[0] == pytest.approx(inicio)
    assert grade[-1] == pytest.approx(fim)


def test_feature_com_ausentes_tem_grade_preenchida(resultado):
    """Antes da correcao, os percentis com NaN davam uma grade toda em NaN."""
    _, tabela = resultado
    linhas = tabela[tabela["feature"] == "ANTECEDENCIA_CANCELAMENTO"]
    assert len(linhas) == gr.GRADE_DEPENDENCIA
    assert linhas["valor"].notna().all()
    assert linhas["valor"].nunique() == gr.GRADE_DEPENDENCIA


def test_feature_discreta_usa_os_proprios_valores(ajustado, dados):
    x, _ = dados
    _, tabela = gr.dependencia_parcial(ajustado, x, ["N_TRECHOS"])
    assert list(tabela["valor"]) == [1, 2, 3]


def test_eixo_vertical_e_probabilidade_de_detrator(resultado):
    """O efeito sintetico sobe o risco: a curva e a da classe 1, nao a da 0."""
    _, tabela = resultado
    assert tabela["probabilidade"].between(0, 1).all()
    atraso = tabela[tabela["feature"] == "ATRASO_CHEGADA"]
    assert atraso["probabilidade"].iloc[-1] > atraso["probabilidade"].iloc[0] + 0.2
    tier = tabela[tabela["feature"] == "TIER_VIAGEM"].set_index("valor")["probabilidade"]
    assert tier.idxmax() == TIER_ARRISCADO


def test_faixa_de_mudanca_contem_o_degrau(resultado):
    """CR05: a faixa citada no texto e onde o degrau sintetico esta."""
    _, tabela = resultado
    faixa = gr.faixa_de_mudanca(tabela)

    atraso = faixa.loc["ATRASO_CHEGADA"]
    assert atraso["de"] <= LIMIAR_ATRASO <= atraso["ate"]
    assert atraso["ate"] - atraso["de"] < 20

    tier = faixa.loc["TIER_VIAGEM"]
    assert tier["ate"] == TIER_ARRISCADO
    assert tier["amplitude"] == pytest.approx(tier["maior_prob"] - tier["menor_prob"])


def test_ruido_tem_amplitude_menor_que_o_efeito(resultado):
    _, tabela = resultado
    faixa = gr.faixa_de_mudanca(tabela)
    assert faixa.loc["ANTECEDENCIA_CANCELAMENTO", "amplitude"] < faixa.loc["ATRASO_CHEGADA", "amplitude"] / 3


def test_faixa_de_curva_plana_cobre_a_grade():
    tabela = pd.DataFrame({
        "feature": "F", "valor": [0.0, 1.0, 2.0], "probabilidade": 0.3, "categorica": False,
    })
    faixa = gr.faixa_de_mudanca(tabela).loc["F"]
    assert (faixa["de"], faixa["ate"], faixa["amplitude"]) == (0.0, 2.0, 0.0)


def test_mesma_entrada_da_mesma_tabela(ajustado, dados):
    x, _ = dados
    _, primeira = gr.dependencia_parcial(ajustado, x, ["ATRASO_CHEGADA", "TIER_VIAGEM"])
    _, segunda = gr.dependencia_parcial(ajustado, x, ["ATRASO_CHEGADA", "TIER_VIAGEM"])
    pd.testing.assert_frame_equal(primeira, segunda)


def test_rodape_declara_a_grade_e_a_fonte(resultado):
    fig, _ = resultado
    rodape = " ".join(t.get_text() for t in fig.texts)
    assert f"até {gr.GRADE_DEPENDENCIA} pontos" in rodape
    assert "5% e 95%" in rodape
    assert "Fonte: Autoria própria." in rodape


def test_recusa_pipeline_sem_ajuste(dados):
    x, _ = dados
    with pytest.raises(NotFittedError):
        gr.dependencia_parcial(_pipeline(), x, ["ATRASO_CHEGADA"])


def test_recusa_matriz_transformada(ajustado, dados):
    x, _ = dados
    transformada = ajustado.named_steps["preparo"].transform(x)
    with pytest.raises(TypeError):
        gr.dependencia_parcial(ajustado, transformada, [0])


@pytest.mark.parametrize("features", [["FAIXA_ATRASO"], [], ["ATRASO_CHEGADA", "ATRASO_CHEGADA"]])
def test_recusa_feature_fora_da_matriz_vazia_ou_repetida(ajustado, dados, features):
    """FAIXA_ATRASO nao esta no contrato: o modelo recebe o atraso continuo."""
    x, _ = dados
    with pytest.raises(ValueError):
        gr.dependencia_parcial(ajustado, x, features)


def test_recusa_alvo_que_nao_e_detrator_um(dados):
    x, y = dados
    rotulado = _pipeline().fit(x, np.where(y == 1, "Detrator", "Outro"))
    with pytest.raises(ValueError, match="Detrator = 1"):
        gr.dependencia_parcial(rotulado, x, ["ATRASO_CHEGADA"])


def test_grade_recusa_coluna_toda_vazia():
    with pytest.raises(ValueError):
        gr.grade_continua(pd.Series([np.nan, np.nan], name="VAZIA"))
