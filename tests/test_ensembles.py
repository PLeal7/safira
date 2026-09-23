"""Testes dos espacos de busca (#186) e do pipeline do Gradient Boosting (#188).

O risco aqui nao e o intervalo estar mal escolhido, que e leitura do markdown:
e uma amostra sorteada do espaco chegar ao estimador e ele recusar, o que so
apareceria no meio de uma `RandomizedSearchCV` de dezenas de minutos em vez de
num teste de segundos. CR02 pede pelo menos 40 combinacoes por espaco com
semente fixa, e ele entra aqui como parametrizacao sobre `ESTIMADOR_POR_ESPACO`
para que um quarto espaco, se `#185` decidir manter as duas bibliotecas por
mais tempo, ganhe cobertura sem precisar de um teste novo.

A segunda metade cobre `criar_pipeline_gradient_boosting` e
`medir_linha_de_base` do card #188. Tudo roda sobre a fixture sintetica
`base`/`contrato`: o card 05 (#241) ainda nao esta em `develop`, entao os
testes de `medir_linha_de_base` usam um `avaliar` de mentira so para conferir
que os vetores certos chegam ate ele, sem depender da metrica real nem da
base do parceiro.

Executar com:  pytest tests/test_ensembles.py -v
"""
from __future__ import annotations

import ast
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.exceptions import NotFittedError
from sklearn.model_selection import ParameterSampler
from sklearn.utils.validation import check_is_fitted

import ensembles
from ensembles import (ESPACO_GRADIENT_BOOSTING_HISTGB,
                        ESPACO_GRADIENT_BOOSTING_XGBOOST,
                        ESPACO_RANDOM_FOREST, ESPACOS_GRADIENT_BOOSTING,
                        ESTIMADOR_POR_ESPACO, PASSO_MODELO, PASSO_PREPARO,
                        RAZAO_DESBALANCEAMENTO, SEMENTE_PADRAO,
                        criar_pipeline_gradient_boosting, medir_linha_de_base)
from matriz import preparar_matriz

N_AMOSTRAS_MINIMO = 40


def test_espacos_gradient_boosting_mantem_as_duas_bibliotecas_ate_o_185():
    """O card exige as duas versoes vivas enquanto o #185 nao decide.

    Quando a decisao sair, a chave da biblioteca descartada some deste
    dicionario no mesmo commit, e este teste e o primeiro a acusar se alguem
    esquecer de atualizar `ESTIMADOR_POR_ESPACO` junto.
    """
    assert set(ESPACOS_GRADIENT_BOOSTING) == {"hist_gradient_boosting", "xgboost"}
    assert ESPACOS_GRADIENT_BOOSTING["hist_gradient_boosting"] is ESPACO_GRADIENT_BOOSTING_HISTGB
    assert ESPACOS_GRADIENT_BOOSTING["xgboost"] is ESPACO_GRADIENT_BOOSTING_XGBOOST


@pytest.mark.parametrize("nome", sorted(ESTIMADOR_POR_ESPACO))
def test_amostras_do_espaco_sao_aceitas_pelo_estimador(nome):
    """CR02: 40 amostras sorteadas com semente fixa, cada uma vira um estimador."""
    estimador_cls, espaco = ESTIMADOR_POR_ESPACO[nome]
    amostras = list(
        ParameterSampler(espaco, n_iter=N_AMOSTRAS_MINIMO, random_state=SEMENTE_PADRAO)
    )

    assert len(amostras) == N_AMOSTRAS_MINIMO

    for parametros in amostras:
        modelo = estimador_cls(**parametros, random_state=SEMENTE_PADRAO)
        for nome_parametro, valor in parametros.items():
            assert modelo.get_params()[nome_parametro] == valor


@pytest.mark.parametrize("nome", sorted(ESTIMADOR_POR_ESPACO))
def test_amostragem_e_reprodutivel_com_a_mesma_semente(nome):
    """Duas buscas com a mesma semente precisam sortear as mesmas combinacoes."""
    _, espaco = ESTIMADOR_POR_ESPACO[nome]
    primeira = list(ParameterSampler(espaco, n_iter=N_AMOSTRAS_MINIMO, random_state=SEMENTE_PADRAO))
    segunda = list(ParameterSampler(espaco, n_iter=N_AMOSTRAS_MINIMO, random_state=SEMENTE_PADRAO))
    assert primeira == segunda


def test_max_features_do_random_forest_e_fracao_dimensionada_pelo_contrato_do_card_01():
    """CR ligado ao DoR: `max_features` precisa caber no contrato de 11 features.

    O espaco usa fracao continua, entao o teste confere que a distribuicao so
    produz valores dentro de (0, 1], nunca uma contagem absoluta de colunas
    que passaria das 11 do contrato.
    """
    amostras = ESPACO_RANDOM_FOREST["max_features"].rvs(
        size=200, random_state=SEMENTE_PADRAO
    )
    assert amostras.min() > 0.0
    assert amostras.max() <= 1.0


def test_scale_pos_weight_do_xgboost_nao_passa_da_razao_observada():
    """O teto do eixo e a proporcao negativos/positivos da base (~3,89)."""
    amostras = ESPACO_GRADIENT_BOOSTING_XGBOOST["scale_pos_weight"].rvs(
        size=200, random_state=SEMENTE_PADRAO
    )
    assert amostras.min() >= 1.0
    assert amostras.max() <= RAZAO_DESBALANCEAMENTO


def test_nenhum_espaco_tem_fit_na_importacao():
    """CR01: os espacos sao dicionarios de distribuicoes, nunca um estimador ajustado."""
    for _, espaco in ESTIMADOR_POR_ESPACO.values():
        assert isinstance(espaco, dict)
        assert not hasattr(espaco, "fit")


# ---------------------------------------------------------------------------
# Pipeline do Gradient Boosting (#188)
# ---------------------------------------------------------------------------

CORTES = {"corte_validacao": "2025-07-01", "corte_teste": "2026-01-01"}


@pytest.fixture
def base():
    """Base sintetica com a allowlist completa e os tres periodos cobertos.

    Mesma forma da fixture de `tests/test_pipeline_logistica.py`: um Cliente por
    periodo, para que o desempate por recorrencia nao encolha as particoes, e
    datas crescentes dentro de cada periodo. As duas ultimas colunas sao de
    pesquisa, para que a trava de vazamento tenha o que recusar.
    """
    n = 60
    datas = (
        list(pd.date_range("2024-03-01", periods=30).astype(str))
        + list(pd.date_range("2025-09-01", periods=15).astype(str))
        + list(pd.date_range("2026-03-01", periods=15).astype(str))
    )
    return pd.DataFrame({
        "RESPONDENT_ID": range(1, n + 1),
        "ID_GOLDENRECORD": range(101, 101 + n),
        "DATA_STD": datas,
        "DETRATOR": ([1, 0] * (n // 2)),
        "TIER_VIAGEM": ["DIAMANTE", "SAFIRA"] * (n // 2),
        "VOO_TIPO": ["DIRETO", "CONEXAO"] * (n // 2),
        "TIPO_ENTRETENIMENTO": ["TELA"] * n,
        "CANAL_COMPRA": ["WEB", "AGENCIA"] * (n // 2),
        "SEGMENTO": ["CORPORATIVO", "LAZER"] * (n // 2),
        "ESTATISTICA_ATRASOSAIDA": np.arange(n, dtype=float),
        "ATRASO_CHEGADA": np.arange(n, dtype=float) * 2,
        "CANCELAMENTO_VOO": [False, True] * (n // 2),
        "ANTECEDENCIA_CANCELAMENTO": np.arange(n, dtype=float),
        "TEMPO_VOO": np.arange(n, dtype=float) + 60,
        "N_TRECHOS": (np.arange(n) % 3) + 1,
        "NPS_PRINCIPAL": [-100, 100] * (n // 2),
        "SUB_NOTA_TRIPULACAO": [1, 5] * (n // 2),
    })


@pytest.fixture
def contrato(base):
    """As saidas do contrato, exatamente como o notebook as consome."""
    return preparar_matriz(base, **CORTES)


@pytest.fixture
def treino(contrato):
    """`X` cru e `y` da particao de treino, que e o que o pipeline recebe."""
    return contrato["x"]["treino"], contrato["y"]["treino"]


@pytest.fixture
def avaliacao(contrato):
    """`X` cru e `y` da particao de validacao, usada como referencia da linha de base."""
    return contrato["x"]["validacao"], contrato["y"]["validacao"]


def test_criar_pipeline_nao_ajusta_o_preprocessador_que_recebeu(contrato):
    """CR01: o `ColumnTransformer` do contrato entra clonado, nunca remontado.

    Se o `clone` sair da funcao, o objeto que `preparar_matriz` ja ajustou sobre
    o treino inteiro passa a ser o mesmo de dentro do pipeline, e cada `fit` de
    fold o reajusta por baixo, sem aviso.
    """
    do_contrato = contrato["preprocessador"]
    pipeline = criar_pipeline_gradient_boosting(do_contrato)

    assert pipeline.named_steps[PASSO_PREPARO] is not do_contrato

    x, y = contrato["x"]["treino"], contrato["y"]["treino"]
    pipeline.fit(x, y)

    assert pipeline.named_steps[PASSO_PREPARO] is not contrato["preprocessador"]


def test_preprocessador_do_pipeline_nasce_nao_ajustado(contrato):
    """O `clone` copia a especificacao e descarta o estado ja ajustado."""
    pipeline = criar_pipeline_gradient_boosting(contrato["preprocessador"])

    with pytest.raises(NotFittedError):
        check_is_fitted(pipeline.named_steps[PASSO_PREPARO])


def test_pipeline_nasce_com_hiperparametros_padrao_exceto_early_stopping(contrato):
    """Linha de base do card: nenhum eixo de busca e tocado, so `early_stopping`.

    `early_stopping=False` nao e escolha de tuning, e a mesma trava de
    vazamento por Cliente que `modelo.HIPERPARAMETROS_CANDIDATO` (#103) ja
    documenta: no padrao `"auto"` a biblioteca separaria uma fatia aleatoria do
    ajuste que ignora `ID_GOLDENRECORD`.
    """
    padrao = HistGradientBoostingClassifier()
    estimador = criar_pipeline_gradient_boosting(
        contrato["preprocessador"]
    ).named_steps[PASSO_MODELO]

    assert estimador.early_stopping is False
    assert estimador.learning_rate == padrao.learning_rate
    assert estimador.max_iter == padrao.max_iter
    assert estimador.max_leaf_nodes == padrao.max_leaf_nodes
    assert estimador.l2_regularization == padrao.l2_regularization
    assert estimador.min_samples_leaf == padrao.min_samples_leaf


def test_semente_chega_ao_estimador_e_nao_fica_implicita(contrato):
    """Semente ausente e o defeito silencioso: o resultado muda sem nada quebrar."""
    estimador = criar_pipeline_gradient_boosting(
        contrato["preprocessador"]
    ).named_steps[PASSO_MODELO]
    assert estimador.random_state == SEMENTE_PADRAO

    outro = criar_pipeline_gradient_boosting(contrato["preprocessador"], random_state=7)
    assert outro.named_steps[PASSO_MODELO].random_state == 7


def test_pipeline_nao_importa_selecao_de_modelo():
    """CR02: o modulo nao pode tocar `sklearn.model_selection`.

    E de la que sairia `KFold`, `GroupKFold` ou `train_test_split`. A validacao
    deste projeto sao os folds do contrato; um splitter proprio aqui seria uma
    terceira particao competindo com as que o grupo ja acordou.
    """
    fonte = Path(ensembles.__file__).read_text(encoding="utf-8")
    arvore = ast.parse(fonte)
    modulos = {
        alias.name
        for no in ast.walk(arvore)
        if isinstance(no, ast.Import)
        for alias in no.names
    } | {
        no.module
        for no in ast.walk(arvore)
        if isinstance(no, ast.ImportFrom) and no.module
    }
    assert not [m for m in modulos if "model_selection" in m]


def test_criar_pipeline_gradient_boosting_nao_monta_pre_processamento_proprio():
    """CR01: o pre-processamento e so o do contrato, clonado."""
    fonte = Path(ensembles.__file__).read_text(encoding="utf-8")
    arvore = ast.parse(fonte)
    modulos = {
        alias.name
        for no in ast.walk(arvore)
        if isinstance(no, ast.Import)
        for alias in no.names
    } | {
        no.module
        for no in ast.walk(arvore)
        if isinstance(no, ast.ImportFrom) and no.module
    }
    pacotes = ("sklearn.preprocessing", "sklearn.compose", "sklearn.impute")
    assert not [m for m in modulos if m.startswith(pacotes)]


def test_duas_construcoes_com_a_mesma_semente_dao_a_mesma_previsao(treino, contrato):
    """CR03: mesma semente e mesma particao tem que devolver o mesmo resultado.

    Os dois pipelines sao construidos do zero, e nao reaproveitados: e isso que
    a busca do #190 faz a cada ponto sorteado, e o que quem revisa faz ao tentar
    repetir o resultado do notebook.
    """
    x, y = treino

    primeiro = criar_pipeline_gradient_boosting(contrato["preprocessador"]).fit(x, y)
    segundo = criar_pipeline_gradient_boosting(contrato["preprocessador"]).fit(x, y)

    assert np.array_equal(primeiro.predict_proba(x), segundo.predict_proba(x))
    assert np.array_equal(primeiro.predict(x), segundo.predict(x))


def test_medir_linha_de_base_repassa_a_probabilidade_da_classe_positiva(treino, avaliacao, contrato):
    """`y_proba` tem que ser a coluna 1 de `predict_proba`, a de Detrator.

    O `avaliar` real e do card 05 (#241), que ainda nao esta em `develop`: o
    espiao abaixo fica no lugar dele so para conferir que `medir_linha_de_base`
    passa os tres vetores certos adiante, sem calcular metrica nenhuma aqui.
    """
    x_treino, y_treino = treino
    x_avaliacao, y_avaliacao = avaliacao
    recebido = {}

    def avaliar_espiao(y_true, y_pred, y_proba):
        recebido.update(y_true=y_true, y_pred=y_pred, y_proba=y_proba)
        return {"F2": 0.5}

    pipeline = criar_pipeline_gradient_boosting(contrato["preprocessador"])
    devolvido = medir_linha_de_base(
        pipeline, x_treino, y_treino, x_avaliacao, y_avaliacao, avaliar_espiao
    )

    ajustado = pipeline  # medir_linha_de_base ajusta o pipeline recebido
    assert np.array_equal(recebido["y_proba"], ajustado.predict_proba(x_avaliacao)[:, 1])
    assert np.array_equal(recebido["y_pred"], ajustado.predict(x_avaliacao))
    assert recebido["y_true"] is y_avaliacao
    # O dicionario volta como `avaliar` devolveu, sem chave renomeada nem
    # metrica acrescentada: quem define o vocabulario da tabela do 18A.1 e o
    # card #241.
    assert devolvido["metricas"] == {"F2": 0.5}
    assert devolvido["n_treino"] == len(y_treino)
    assert devolvido["n_avaliacao"] == len(y_avaliacao)
    assert devolvido["random_state"] == SEMENTE_PADRAO


def test_medir_linha_de_base_recusa_avaliar_que_nao_e_funcao(treino, avaliacao, contrato):
    """Passar o dicionario de metricas no lugar da funcao e o engano provavel."""
    x_treino, y_treino = treino
    x_avaliacao, y_avaliacao = avaliacao
    pipeline = criar_pipeline_gradient_boosting(contrato["preprocessador"])

    with pytest.raises(TypeError, match="card 05"):
        medir_linha_de_base(
            pipeline, x_treino, y_treino, x_avaliacao, y_avaliacao, {"F2": 0.5}
        )


def test_medir_linha_de_base_nao_precisa_do_avaliar_real_do_card_05(treino, avaliacao, contrato):
    """Fallback do card: o pipeline e a medicao funcionam com um `avaliar` sintetico.

    Se o card 05 (#241) atrasar, este e o teste que prova que o pipeline e a
    medicao continuam commitaveis no D2: nenhuma importacao de `avaliacao` real
    e feita neste modulo.
    """
    x_treino, y_treino = treino
    x_avaliacao, y_avaliacao = avaliacao
    pipeline = criar_pipeline_gradient_boosting(contrato["preprocessador"])

    resultado = medir_linha_de_base(
        pipeline, x_treino, y_treino, x_avaliacao, y_avaliacao,
        lambda y_true, y_pred, y_proba: {"metrica_sintetica": 1.0},
    )

    assert resultado["metricas"] == {"metrica_sintetica": 1.0}
