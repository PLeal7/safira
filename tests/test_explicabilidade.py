"""Travas da permutation importance do melhor ensemble (card 14A, #191).

Este arquivo nao mede qual feature importa na base real: o ranking de verdade
sai do notebook, sobre a base da Azul. O que ele protege sao os erros que fariam
a funcao devolver um ranking com cara de valido e conteudo errado, sem levantar
erro nenhum:

1. Ranking que muda entre duas execucoes, por semente solta.
2. Importancia medida sobre a matriz transformada, com cada categorica
   espalhada em colunas one-hot.
3. Importancia medida no treino, onde uma feature memorizada parece importante.
4. Scoring diferente do da busca, ou feature da propria pesquisa de NPS no
   ranking.
5. Escolha do melhor ensemble que declara vencedor quem nao disputou.

O scorer daqui e um substituto do `scorer_f2` do #242, com a mesma
configuracao, porque aquele card ainda nao esta em `develop`. Todos os dados sao
sinteticos.

Executar com:  pytest tests/test_explicabilidade.py -v
"""
import inspect
import json
import math

import numpy as np
import pandas as pd
import pytest
from sklearn.exceptions import NotFittedError
from sklearn.metrics import fbeta_score, make_scorer

import explicabilidade as expl
from ensembles import criar_pipeline_random_forest
from matriz import preparar_matriz

# Substituto do `scorer_f2` do #242, com a mesma configuracao declarada la.
SCORER_TESTE = make_scorer(fbeta_score, beta=2, pos_label=1, zero_division=0)

# Poucas arvores rasas e poucas repeticoes: a suite precisa rodar em segundos, e
# nenhuma trava aqui depende do tamanho da floresta.
HIPERPARAMETROS_TESTE = {"n_estimators": 15, "max_depth": 4}
N_REPETICOES_TESTE = 3


@pytest.fixture(scope="module")
def contrato():
    """Base sintetica com Clientes repetidos e um sinal plantado em ATRASO_CHEGADA.

    O alvo depende de `ATRASO_CHEGADA` e so dela. Isso da ao teste uma resposta
    conhecida: se a funcao mede o que diz medir, essa feature tem de ficar em
    primeiro lugar.
    """
    gerador = np.random.default_rng(11)
    n = 1500
    datas = pd.to_datetime("2024-01-01") + pd.to_timedelta(gerador.integers(0, 900, size=n), unit="D")
    atraso_chegada = gerador.integers(0, 300, n)
    probabilidade = np.where(atraso_chegada > 150, 0.7, 0.08)
    base = pd.DataFrame({
        "RESPONDENT_ID": np.arange(n),
        "ID_GOLDENRECORD": gerador.integers(1, 500, size=n),
        "DATA_STD": datas.strftime("%Y-%m-%d"),
        "DETRATOR": (gerador.random(n) < probabilidade).astype(int),
        "TIER_VIAGEM": gerador.choice(["Diamante", "Safira", "Sem cadastro"], n),
        "VOO_TIPO": gerador.choice(["Direto", "Conexao"], n),
        "TIPO_ENTRETENIMENTO": gerador.choice(["Tela", "Streaming", "Sem"], n),
        "CANAL_COMPRA": gerador.choice(["Web", "Mobile", "Agency"], n),
        "SEGMENTO": gerador.choice(["Lazer", "Corporativo"], n),
        "ESTATISTICA_ATRASOSAIDA": gerador.integers(0, 300, n),
        "ATRASO_CHEGADA": atraso_chegada,
        "CANCELAMENTO_VOO": gerador.random(n) < 0.05,
        "ANTECEDENCIA_CANCELAMENTO": gerador.integers(0, 10, n),
        "TEMPO_VOO": gerador.integers(40, 600, n),
        "N_TRECHOS": gerador.integers(1, 4, n),
    })
    return preparar_matriz(base, "2025-06-01", "2025-12-01")


@pytest.fixture(scope="module")
def pipeline_ajustado(contrato):
    pipeline = criar_pipeline_random_forest(contrato["preprocessador"], **HIPERPARAMETROS_TESTE)
    return pipeline.fit(contrato["x"]["treino"], contrato["y"]["treino"])


@pytest.fixture(scope="module")
def tabela(pipeline_ajustado, contrato):
    return expl.importancia_no_contrato(
        pipeline_ajustado, contrato, SCORER_TESTE, n_repeats=N_REPETICOES_TESTE,
    )


# --- Reprodutibilidade --------------------------------------------------------


def test_duas_execucoes_devolvem_o_mesmo_ranking(tabela, pipeline_ajustado, contrato):
    """E o "Como verificar" do card: rodar duas vezes e conferir o ranking identico."""
    de_novo = expl.importancia_no_contrato(
        pipeline_ajustado, contrato, SCORER_TESTE, n_repeats=N_REPETICOES_TESTE,
    )
    pd.testing.assert_frame_equal(tabela, de_novo)


def test_paralelismo_nao_muda_o_ranking(tabela, pipeline_ajustado, contrato):
    """A semente de cada embaralhamento nao pode depender de quantos processos rodam."""
    paralela = expl.importancia_no_contrato(
        pipeline_ajustado, contrato, SCORER_TESTE, n_repeats=N_REPETICOES_TESTE, n_jobs=2,
    )
    pd.testing.assert_frame_equal(tabela, paralela)


def test_semente_padrao_e_a_do_projeto():
    padrao = inspect.signature(expl.calcular_importancia).parameters["random_state"].default
    assert padrao == expl.SEMENTE_PADRAO == 42
    assert expl.N_REPETICOES >= 5


# --- Formato do ranking -------------------------------------------------------


def test_uma_linha_por_feature_original_do_contrato(tabela, contrato):
    """Nenhum nome de coluna one-hot: o ranking e sobre o que o contrato entrega."""
    assert sorted(tabela.index) == sorted(contrato["x"]["treino"].columns)
    assert tabela.index.name == "feature"
    assert "TIER_VIAGEM" in tabela.index
    assert not any("__" in feature for feature in tabela.index)


def test_colunas_posicao_e_ordem(tabela):
    assert tuple(tabela.columns) == expl.COLUNAS_TABELA
    assert list(tabela["posicao"]) == list(range(1, len(tabela) + 1))
    assert tabela["queda_media"].is_monotonic_decreasing
    assert (tabela["queda_desvio"] >= 0).all()


def test_sinal_plantado_fica_em_primeiro(tabela):
    """Com o alvo dependendo so de ATRASO_CHEGADA, ela tem de liderar."""
    assert tabela.index[0] == "ATRASO_CHEGADA"
    assert expl.features_no_topo(tabela)[0] == "ATRASO_CHEGADA"
    assert len(expl.features_no_topo(tabela)) == expl.N_TOPO


def test_empate_e_desfeito_pelo_nome(pipeline_ajustado, contrato, monkeypatch):
    """Duas quedas iguais nao podem trocar de lugar conforme a ordem das colunas."""
    class ResultadoFalso:
        importances_mean = np.zeros(contrato["x"]["validacao"].shape[1])
        importances_std = np.zeros(contrato["x"]["validacao"].shape[1])

    monkeypatch.setattr(expl, "permutation_importance", lambda *a, **k: ResultadoFalso())
    tabela = expl.importancia_no_contrato(pipeline_ajustado, contrato, SCORER_TESTE)
    assert list(tabela.index) == sorted(contrato["x"]["validacao"].columns)


# --- Travas de entrada --------------------------------------------------------


def test_recusa_a_particao_de_treino(pipeline_ajustado, contrato):
    with pytest.raises(ValueError, match="treino"):
        expl.importancia_no_contrato(pipeline_ajustado, contrato, SCORER_TESTE, particao="treino")


def test_recusa_particao_fora_do_contrato(pipeline_ajustado, contrato):
    with pytest.raises(ValueError, match="fora do contrato"):
        expl.importancia_no_contrato(pipeline_ajustado, contrato, SCORER_TESTE, particao="avaliacao")


def test_particao_padrao_e_a_validacao(pipeline_ajustado, contrato, monkeypatch):
    recebido = {}

    def espiao(pipeline, x, y, scoring, **kwargs):
        recebido["x"], recebido["y"] = x, y
        return "ok"

    monkeypatch.setattr(expl, "calcular_importancia", espiao)
    expl.importancia_no_contrato(pipeline_ajustado, contrato, SCORER_TESTE)
    assert recebido["x"] is contrato["x"]["validacao"]
    assert recebido["y"] is contrato["y"]["validacao"]


def test_recusa_scoring_ausente(pipeline_ajustado, contrato):
    with pytest.raises(ValueError, match="scoring"):
        expl.importancia_no_contrato(pipeline_ajustado, contrato, None)


def test_recusa_uma_repeticao_so(pipeline_ajustado, contrato):
    with pytest.raises(ValueError, match="n_repeats"):
        expl.importancia_no_contrato(pipeline_ajustado, contrato, SCORER_TESTE, n_repeats=1)


def test_recusa_matriz_transformada(pipeline_ajustado, contrato):
    """A matriz que saiu do ColumnTransformer espalharia as categoricas no ranking."""
    with pytest.raises(TypeError, match="cru"):
        expl.calcular_importancia(
            pipeline_ajustado, contrato["matrizes"]["validacao"],
            contrato["y"]["validacao"], SCORER_TESTE,
        )


def test_recusa_colunas_diferentes_das_do_ajuste(pipeline_ajustado, contrato):
    x = contrato["x"]["validacao"].drop(columns="N_TRECHOS")
    with pytest.raises(ValueError, match="features com que o pipeline foi ajustado"):
        expl.calcular_importancia(pipeline_ajustado, x, contrato["y"]["validacao"], SCORER_TESTE)


def test_recusa_pipeline_sem_ajuste(contrato):
    virgem = criar_pipeline_random_forest(contrato["preprocessador"], **HIPERPARAMETROS_TESTE)
    with pytest.raises(NotFittedError, match="ajustado no treino"):
        expl.importancia_no_contrato(virgem, contrato, SCORER_TESTE)


def test_recusa_feature_da_pesquisa_de_nps(contrato):
    """O "Como revisar" do card: nenhuma feature da propria pesquisa no ranking."""
    x_treino = contrato["x"]["treino"].assign(NPS_PRINCIPAL=0)
    pipeline = criar_pipeline_random_forest(contrato["preprocessador"], **HIPERPARAMETROS_TESTE)
    pipeline.fit(x_treino, contrato["y"]["treino"])
    x_avaliacao = contrato["x"]["validacao"].assign(NPS_PRINCIPAL=0)
    with pytest.raises(ValueError, match="NPS"):
        expl.calcular_importancia(pipeline, x_avaliacao, contrato["y"]["validacao"], SCORER_TESTE)


# --- Escolha do melhor ensemble ----------------------------------------------


def test_escolhe_o_de_maior_f2():
    escolha = expl.escolher_melhor_ensemble({
        "Random Forest": {"F2": 0.41, "ROC-AUC": 0.70},
        "Gradient Boosting": {"F2": 0.44, "ROC-AUC": 0.68},
    })
    assert escolha["vencedor"] == "Gradient Boosting"
    assert escolha["metrica"] == "F2"
    assert escolha["comparacao_completa"] is True
    assert escolha["empate"] is False


def test_ensemble_sem_numero_fica_fora_e_e_sinalizado():
    """Com o #190 pendente, o Random Forest nao pode ser anunciado como vencedor da disputa."""
    escolha = expl.escolher_melhor_ensemble({
        "Random Forest": {"F2": 0.41},
        "Gradient Boosting": None,
    })
    assert escolha["vencedor"] == "Random Forest"
    assert escolha["ausentes"] == ["Gradient Boosting"]
    assert escolha["comparacao_completa"] is False


def test_nan_de_avaliar_nao_disputa():
    escolha = expl.escolher_melhor_ensemble({
        "Random Forest": {"F2": 0.30},
        "Gradient Boosting": {"F2": float("nan")},
    })
    assert escolha["vencedor"] == "Random Forest"
    assert escolha["ausentes"] == ["Gradient Boosting"]


def test_empate_e_sinalizado():
    escolha = expl.escolher_melhor_ensemble({"A": {"F2": 0.4}, "B": {"F2": 0.4}})
    assert escolha["vencedor"] == "A"
    assert escolha["empate"] is True


def test_sem_nenhum_numero_levanta_erro():
    with pytest.raises(ValueError, match="Nenhum ensemble"):
        expl.escolher_melhor_ensemble({"Random Forest": None, "Gradient Boosting": None})


# --- Comparacao com a EDA, grafico e artefato ---------------------------------


def test_comparacao_com_a_eda_usa_o_nome_do_contrato(tabela):
    comparacao = expl.comparar_com_eda(tabela)
    assert list(comparacao.index) == ["ATRASO_CHEGADA", "FAIXA_ATRASO", "N_TRECHOS"]
    assert comparacao.loc["FAIXA_ATRASO", "feature_no_contrato"] == "ESTATISTICA_ATRASOSAIDA"
    assert comparacao.loc["ATRASO_CHEGADA", "posicao"] == 1
    assert bool(comparacao.loc["ATRASO_CHEGADA", "no_topo"]) is True


def test_feature_da_eda_ausente_nao_some_da_comparacao(tabela):
    comparacao = expl.comparar_com_eda(tabela, {"FAIXA_ATRASO": "FAIXA_ATRASO"})
    assert comparacao.loc["FAIXA_ATRASO", "posicao"] is None
    assert bool(comparacao.loc["FAIXA_ATRASO", "no_topo"]) is False


def test_grafico_mostra_media_e_desvio_de_cada_feature(tabela):
    import matplotlib
    matplotlib.use("Agg")
    from matplotlib.container import BarContainer
    figura = expl.plotar_importancia(tabela)
    ax = figura.axes[0]
    assert len(ax.patches) == len(tabela)
    # As barras de erro sao o desvio padrao: sem elas o CR04 nao se cumpre.
    barras = next(c for c in ax.containers if isinstance(c, BarContainer))
    assert barras.errorbar is not None
    assert len(barras.errorbar.lines[2][0].get_segments()) == len(tabela)
    assert ax.get_yticklabels()[-1].get_text() == tabela.index[0]
    matplotlib.pyplot.close(figura)


def test_artefato_guarda_configuracao_e_ranking(tabela, tmp_path):
    escolha = expl.escolher_melhor_ensemble({"Random Forest": {"F2": 0.4}, "Gradient Boosting": None})
    caminho = expl.salvar_ranking(
        tabela, escolha, scoring_nome="scorer_f2", n_repeats=N_REPETICOES_TESTE,
        caminho=tmp_path / "importancia.json",
    )
    registro = expl.carregar_ranking(caminho)
    assert registro["ensemble"] == "Random Forest"
    assert registro["comparacao_completa"] is False
    assert registro["particao"] == "validacao"
    assert registro["n_repeats"] == N_REPETICOES_TESTE
    assert registro["random_state"] == 42
    assert registro["scoring"] == "scorer_f2"
    assert registro["topo"] == expl.features_no_topo(tabela)
    assert [linha["feature"] for linha in registro["ranking"]] == list(tabela.index)
    assert all(isinstance(linha["posicao"], int) for linha in registro["ranking"])
    assert not math.isnan(registro["ranking"][0]["queda_media"])
    # So agregados: nenhum identificador de Cliente ou de resposta no arquivo.
    texto = json.dumps(registro)
    assert "ID_GOLDENRECORD" not in texto and "RESPONDENT_ID" not in texto
