"""Teste de fumaca das bibliotecas de boosting candidatas (card 04A, #185).

Este arquivo nao mede qualidade de modelo: a metrica sai no notebook, sobre a
base real. O que ele protege e a validade da **medicao de custo** que decide qual
biblioteca o projeto vai usar nos cards #186, #187 e #188. Sao quatro riscos, e
todos eles devolveriam um tempo menor que o real, nunca um erro:

1. Medir sobre uma matriz que nao veio do contrato. Um pre-processamento proprio,
   mais simples que o do contrato, produziria menos colunas e um ajuste mais
   rapido do que o que a busca vai enfrentar.
2. Criar particao ou validacao cruzada aqui. Alem de contrariar a secao 3, uma
   fatia aleatoria menor que o treino do contrato tambem mediria menos.
3. Reaproveitar um modelo ja ajustado entre medicoes. A segunda biblioteca
   comecaria de um estado pronto e pareceria mais barata.
4. Comparar as duas com configuracoes diferentes. O tempo passaria a medir
   hiperparametro, e nao biblioteca.

A partir do card 08A (#187) o arquivo cobre tambem o pipeline do Random Forest:
que ele e montado sobre o pre-processador do contrato sem remonta-lo, que dois
ajustes com a mesma semente dao previsoes identicas (CR03) e que a linha de base
so e medida pela funcao `avaliar` recebida, sem metrica nem particao propria.

Todos usam dados sinteticos, sem tocar nas bases da Azul.

Executar com:  pytest tests/test_ensembles.py -v
"""
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.exceptions import NotFittedError
from sklearn.utils.validation import check_is_fitted

from ensembles import (
    HIPERPARAMETROS_COMPARACAO,
    PASSO_MODELO,
    PASSO_PREPARO,
    construir_candidatos,
    criar_pipeline_random_forest,
    escolher_biblioteca,
    estimar_busca,
    medir_ajuste,
    medir_bibliotecas,
    medir_linha_de_base,
)
from matriz import preparar_matriz

RAIZ = Path(__file__).resolve().parents[1]

CORTE_VALIDACAO = "2025-06-01"
CORTE_TESTE = "2025-12-01"

# Os nomes proibidos sao montados por partes de proposito. O CR03 pede que a
# busca por eles no diff volte vazia, e um arquivo de teste que os escrevesse por
# extenso apareceria nessa busca e derrubaria a propria evidencia que deveria
# produzir.
PARTICIONADORES_PROIBIDOS = (
    "K" + "Fold",
    "Stratified" + "K" + "Fold",
    "Group" + "K" + "Fold",
    "train" + "_test_" + "split",
    # CR02 do #187: a linha de base e medida so por `avaliar`, entao validacao
    # cruzada propria tambem conta como particao fora do contrato.
    "cross" + "_val_" + "score",
)

ARQUIVOS_DO_CARD = (
    RAIZ / "src" / "ensembles.py",
    Path(__file__),
)


@pytest.fixture(scope="module")
def base_sintetica():
    """Base com as colunas que o contrato exige, em escala de teste.

    Os clientes se repetem para que o agrupamento por `ID_GOLDENRECORD` tenha o
    que agrupar, e as datas cobrem os dois cortes para que as tres particoes
    existam.
    """
    gerador = np.random.default_rng(7)
    n = 1200
    datas = pd.to_datetime("2024-01-01") + pd.to_timedelta(
        gerador.integers(0, 900, size=n), unit="D"
    )
    return pd.DataFrame({
        "RESPONDENT_ID": np.arange(n),
        "ID_GOLDENRECORD": gerador.integers(1, 400, size=n),
        "DATA_STD": datas.strftime("%Y-%m-%d"),
        "DETRATOR": (gerador.random(n) < 0.2).astype(int),
        "TIER_VIAGEM": gerador.choice(["Diamante", "Safira", "Sem cadastro"], n),
        "VOO_TIPO": gerador.choice(["Direto", "Conexao"], n),
        "TIPO_ENTRETENIMENTO": gerador.choice(["Tela", "Streaming", "Sem"], n),
        "CANAL_COMPRA": gerador.choice(["Web", "Mobile", "Agency"], n),
        "SEGMENTO": gerador.choice(["Lazer", "Corporativo"], n),
        "ESTATISTICA_ATRASOSAIDA": gerador.integers(0, 300, n),
        "ATRASO_CHEGADA": gerador.integers(0, 300, n),
        "CANCELAMENTO_VOO": gerador.random(n) < 0.05,
        "ANTECEDENCIA_CANCELAMENTO": gerador.integers(0, 10, n),
        "TEMPO_VOO": gerador.integers(40, 600, n),
        "N_TRECHOS": gerador.integers(1, 4, n),
    })


@pytest.fixture(scope="module")
def contrato(base_sintetica):
    """A unica origem de `x`, `y`, `grupos` e do `ColumnTransformer` nos testes."""
    return preparar_matriz(base_sintetica, CORTE_VALIDACAO, CORTE_TESTE)


@pytest.fixture(scope="module")
def candidatos_rapidos():
    """As duas bibliotecas com poucas arvores, so para o caminho ser exercitado.

    O numero de arvores da comparacao real esta em `HIPERPARAMETROS_COMPARACAO` e
    vale no notebook; aqui ele so faria a suite demorar sem proteger nada a mais.
    """
    candidatos = construir_candidatos()
    candidatos["HistGradientBoostingClassifier"].set_params(max_iter=10)
    candidatos["XGBClassifier"].set_params(n_estimators=10)
    return candidatos


# ------------------------------------------------------- origem da matriz medida
def test_matriz_medida_vem_inteira_do_contrato(contrato):
    """`x`, `y`, `grupos` e a matriz transformada saem todos de `preparar_matriz`."""
    assert {"x", "y", "grupos", "matrizes", "preprocessador"} <= set(contrato)

    treino = contrato["matrizes"]["treino"]
    assert treino.shape[0] == len(contrato["y"]["treino"]) == len(contrato["grupos"]["treino"])
    assert treino.shape[1] == contrato["metadados"]["colunas_da_matriz"]
    # O agrupamento por Cliente existe de fato: sem repeticao, o `grupos` do
    # contrato nao teria nada a agrupar e a medicao estaria olhando outra base.
    assert contrato["grupos"]["treino"].nunique() < len(contrato["grupos"]["treino"])


def test_medicao_nao_reajusta_o_pre_processador_do_contrato(contrato, candidatos_rapidos):
    """A transformacao da validacao e identica antes e depois da medicao.

    Se alguma etapa do modulo reajustasse o `ColumnTransformer`, a mediana da
    imputacao e a escala passariam a carregar informacao de fora do treino e a
    saida abaixo mudaria.
    """
    preprocessador = contrato["preprocessador"]
    antes = preprocessador.transform(contrato["x"]["validacao"])

    medir_bibliotecas(
        contrato["matrizes"]["treino"],
        contrato["y"]["treino"],
        candidatos=candidatos_rapidos,
    )

    depois = preprocessador.transform(contrato["x"]["validacao"])
    np.testing.assert_array_equal(antes, depois)


# ------------------------------------------------------------ tabela de medicao
def test_tabela_traz_tempo_pico_e_semente_das_duas_bibliotecas(contrato, candidatos_rapidos):
    """O que o CR04 pede, por biblioteca, na tabela que vai para o notebook."""
    tabela = medir_bibliotecas(
        contrato["matrizes"]["treino"],
        contrato["y"]["treino"],
        candidatos=candidatos_rapidos,
    )

    assert list(tabela.index) == ["HistGradientBoostingClassifier", "XGBClassifier"]
    assert {"tempo_ajuste_s", "pico_memoria_mb", "random_state"} <= set(tabela.columns)
    assert (tabela["tempo_ajuste_s"] > 0).all()
    assert (tabela["pico_memoria_mb"] > 0).all()
    assert tabela["random_state"].nunique() == 1
    assert (tabela["n_linhas"] == contrato["matrizes"]["treino"].shape[0]).all()


def test_medicao_nao_reaproveita_ajuste_anterior(contrato, candidatos_rapidos):
    """O estimador recebido continua sem ajuste; quem treina e a copia."""
    original = candidatos_rapidos["HistGradientBoostingClassifier"]

    medicao = medir_ajuste(original, contrato["matrizes"]["treino"], contrato["y"]["treino"])

    check_is_fitted(medicao["estimador"])
    with pytest.raises(NotFittedError):
        check_is_fitted(original)


def test_hiperparametros_sao_equivalentes_nos_dois_lados():
    """Mesmo passo, mesmas arvores, mesmas folhas, mesmos bins e mesma semente."""
    candidatos = construir_candidatos(random_state=7)
    hist = candidatos["HistGradientBoostingClassifier"].get_params()
    xgb = candidatos["XGBClassifier"].get_params()

    assert hist["learning_rate"] == xgb["learning_rate"] == HIPERPARAMETROS_COMPARACAO["passo"]
    assert hist["max_iter"] == xgb["n_estimators"] == HIPERPARAMETROS_COMPARACAO["arvores"]
    assert hist["max_leaf_nodes"] == xgb["max_leaves"] == HIPERPARAMETROS_COMPARACAO["folhas"]
    assert hist["max_bins"] == xgb["max_bin"] == HIPERPARAMETROS_COMPARACAO["bins"]
    assert hist["random_state"] == xgb["random_state"] == 7
    # Sem parada antecipada dos dois lados: com ela, o tempo medido seria o de
    # menos arvores do que as declaradas.
    assert hist["early_stopping"] is False
    assert xgb["early_stopping_rounds"] is None


# ------------------------------------------------------- estimativa e criterio
def test_estimativa_multiplica_iteracoes_por_folds():
    assert estimar_busca(3600, n_iteracoes=1, n_folds=1) == pytest.approx(1.0)
    assert estimar_busca(36, n_iteracoes=40, n_folds=5) == pytest.approx(2.0)


@pytest.mark.parametrize("n_iteracoes,n_folds", [(0, 5), (40, 0), (-1, 5)])
def test_estimativa_recusa_busca_vazia(n_iteracoes, n_folds):
    with pytest.raises(ValueError):
        estimar_busca(10, n_iteracoes=n_iteracoes, n_folds=n_folds)


def test_criterio_prefere_a_biblioteca_sem_dependencia_extra_quando_ela_cabe():
    tabela = pd.DataFrame(
        {"tempo_ajuste_s": [10.0, 5.0]},
        index=["HistGradientBoostingClassifier", "XGBClassifier"],
    )

    decisao = escolher_biblioteca(tabela, orcamento_horas=3.0)

    assert decisao["escolhida"] == "HistGradientBoostingClassifier"
    assert "dependencia" in decisao["justificativa"]


def test_criterio_descarta_quem_estoura_o_orcamento_da_sessao():
    """Estourar a sessao nao e ser mais lento; e nao ser uma opcao."""
    tabela = pd.DataFrame(
        {"tempo_ajuste_s": [600.0, 5.0]},
        index=["HistGradientBoostingClassifier", "XGBClassifier"],
    )

    decisao = escolher_biblioteca(tabela, orcamento_horas=3.0)

    assert decisao["escolhida"] == "XGBClassifier"
    assert decisao["estimativas_horas"]["HistGradientBoostingClassifier"] > 3.0


def test_criterio_devolve_a_decisao_para_o_grupo_quando_nenhuma_cabe():
    tabela = pd.DataFrame(
        {"tempo_ajuste_s": [900.0, 600.0]},
        index=["HistGradientBoostingClassifier", "XGBClassifier"],
    )

    decisao = escolher_biblioteca(tabela, orcamento_horas=3.0)

    assert decisao["escolhida"] == "XGBClassifier"
    assert "Metricas e Decisoes" in decisao["justificativa"]


# --------------------------------------------------------------------- travas
@pytest.mark.parametrize("arquivo", ARQUIVOS_DO_CARD, ids=lambda p: p.name)
def test_card_nao_cria_particao_nem_validacao_propria(arquivo):
    """CR03: nenhum particionador fora do contrato aparece no codigo do card."""
    fonte = arquivo.read_text(encoding="utf-8")
    encontrados = [nome for nome in PARTICIONADORES_PROIBIDOS if nome in fonte]
    assert not encontrados, (
        f"{arquivo.name} instancia particionador proprio: {encontrados}. "
        "A validacao deste projeto sao os folds do contrato, e nenhuma outra."
    )


# ------------------------------------------- pipeline do random forest (#187)
# Poucas arvores bastam para exercitar o caminho; a floresta padrao da linha de
# base roda no notebook, sobre a base real.
ARVORES_TESTE = 10


def _avaliar_falso(chamadas):
    """Substituto de `avaliar(y_true, y_pred, y_proba)` que so registra o que recebeu.

    O card 05 (#241) ainda nao esta em `develop`; o que se protege aqui e o
    contrato da chamada, nao a metrica.
    """
    def avaliar(y_true, y_pred, y_proba):
        chamadas.append({"y_true": y_true, "y_pred": y_pred, "y_proba": y_proba})
        return {"metrica_falsa": 0.5}
    return avaliar


def test_pipeline_encadeia_o_pre_processador_do_contrato_e_o_random_forest(contrato):
    """CR01: o primeiro passo e o `ColumnTransformer` do contrato, clonado e virgem."""
    original = contrato["preprocessador"]

    pipeline = criar_pipeline_random_forest(original, random_state=7)

    assert [nome for nome, _ in pipeline.steps] == [PASSO_PREPARO, PASSO_MODELO]
    preparo = pipeline.named_steps[PASSO_PREPARO]
    assert isinstance(preparo, ColumnTransformer)
    assert preparo is not original
    # Mesma especificacao: mesmos blocos, mesmas colunas, mesmos passos internos.
    assert [(n, c) for n, _, c in preparo.transformers] == [
        (n, c) for n, _, c in original.transformers
    ]
    assert preparo.get_params(deep=True).keys() == original.get_params(deep=True).keys()
    # Nasce sem o ajuste que `preparar_matriz` ja fez no treino.
    with pytest.raises(NotFittedError):
        check_is_fitted(preparo)

    modelo_rf = pipeline.named_steps[PASSO_MODELO]
    assert isinstance(modelo_rf, RandomForestClassifier)
    assert modelo_rf.random_state == 7


def test_pipeline_nasce_nos_hiperparametros_padrao_da_biblioteca(contrato):
    """A linha de base nao escolhe hiperparametro; quem escolhe e a busca do #189."""
    padrao = RandomForestClassifier().get_params()
    modelo_rf = criar_pipeline_random_forest(contrato["preprocessador"]).named_steps[PASSO_MODELO]
    montado = modelo_rf.get_params()

    diferentes = {
        chave for chave in padrao
        if chave not in {"random_state", "n_jobs"} and montado[chave] != padrao[chave]
    }
    assert not diferentes


def test_hiperparametros_repassados_nao_sobrescrevem_a_semente(contrato):
    pipeline = criar_pipeline_random_forest(
        contrato["preprocessador"], random_state=3, n_estimators=ARVORES_TESTE
    )
    modelo_rf = pipeline.named_steps[PASSO_MODELO]
    assert modelo_rf.n_estimators == ARVORES_TESTE
    assert modelo_rf.random_state == 3


def test_mesma_semente_produz_previsoes_identicas(contrato):
    """CR03: dois ajustes independentes com o mesmo `random_state` sao o mesmo modelo."""
    probabilidades = []
    for _ in range(2):
        pipeline = criar_pipeline_random_forest(
            contrato["preprocessador"], random_state=11, n_estimators=ARVORES_TESTE
        )
        pipeline.fit(contrato["x"]["treino"], contrato["y"]["treino"])
        probabilidades.append(pipeline.predict_proba(contrato["x"]["validacao"]))

    np.testing.assert_array_equal(probabilidades[0], probabilidades[1])


def test_sementes_diferentes_produzem_florestas_diferentes(contrato):
    """Contraprova do CR03: se a semente nao chegasse ao estimador, o teste acima
    passaria igual, por sorte ou por acaso de implementacao."""
    probabilidades = []
    for semente in (11, 12):
        pipeline = criar_pipeline_random_forest(
            contrato["preprocessador"], random_state=semente, n_estimators=ARVORES_TESTE
        )
        pipeline.fit(contrato["x"]["treino"], contrato["y"]["treino"])
        probabilidades.append(pipeline.predict_proba(contrato["x"]["validacao"]))

    assert not np.array_equal(probabilidades[0], probabilidades[1])


def test_ajuste_do_pipeline_nao_mexe_no_pre_processador_do_contrato(contrato):
    """O `fit` do pipeline ajusta a copia; o objeto do contrato fica como estava."""
    preprocessador = contrato["preprocessador"]
    antes = preprocessador.transform(contrato["x"]["validacao"])

    pipeline = criar_pipeline_random_forest(preprocessador, n_estimators=ARVORES_TESTE)
    pipeline.fit(contrato["x"]["treino"], contrato["y"]["treino"])

    np.testing.assert_array_equal(antes, preprocessador.transform(contrato["x"]["validacao"]))


def test_linha_de_base_repassa_os_vetores_certos_para_avaliar(contrato):
    """CR02: a metrica vem de `avaliar`, que recebe rotulo, predicao e score de Detrator."""
    chamadas = []
    pipeline = criar_pipeline_random_forest(
        contrato["preprocessador"], random_state=5, n_estimators=ARVORES_TESTE
    )

    resultado = medir_linha_de_base(
        pipeline,
        contrato["x"]["treino"],
        contrato["y"]["treino"],
        contrato["x"]["validacao"],
        contrato["y"]["validacao"],
        avaliar=_avaliar_falso(chamadas),
    )

    assert len(chamadas) == 1
    recebido = chamadas[0]
    y_validacao = contrato["y"]["validacao"]
    assert recebido["y_true"] is y_validacao
    np.testing.assert_array_equal(
        recebido["y_pred"], pipeline.predict(contrato["x"]["validacao"])
    )
    # Coluna 1 de `predict_proba`: a probabilidade de Detrator, nao a de Neutro/Promotor.
    np.testing.assert_array_equal(
        recebido["y_proba"], pipeline.predict_proba(contrato["x"]["validacao"])[:, 1]
    )
    assert pipeline.classes_[1] == 1

    assert resultado["metricas"] == {"metrica_falsa": 0.5}
    assert resultado["random_state"] == 5
    assert resultado["tempo_total_s"] > 0
    assert resultado["n_treino"] == len(contrato["y"]["treino"])
    assert resultado["n_avaliacao"] == len(y_validacao)


def test_linha_de_base_recusa_avaliar_que_nao_e_funcao(contrato):
    pipeline = criar_pipeline_random_forest(contrato["preprocessador"], n_estimators=ARVORES_TESTE)
    with pytest.raises(TypeError, match="#241"):
        medir_linha_de_base(
            pipeline,
            contrato["x"]["treino"],
            contrato["y"]["treino"],
            contrato["x"]["validacao"],
            contrato["y"]["validacao"],
            avaliar=None,
        )
