"""Testes do primeiro modelo candidato da secao 4.3.

O que estes testes protegem nao e a metrica do modelo, que depende da base e sai
no notebook: e o que faria essa metrica mentir sem quebrar nada. Sao tres riscos,
e cada um deles devolveria um numero melhor, nunca um erro.

1. Hiperparametro implicito. `early_stopping="auto"` liga a parada antecipada
   sozinha acima de dez mil linhas e separa uma fatia aleatoria do ajuste, que
   ignora o agrupamento por Cliente da secao 3.
2. Pre-processador ajustado fora do fold. A mediana da imputacao e a escala
   passariam a carregar informacao das linhas usadas como validacao naquele fold.
3. Modelo reaproveitado entre folds. O segundo fold comecaria do ajuste do
   primeiro e a media dos cinco mediria quem ja viu quase todo o treino.

Todos usam dados sinteticos, sem tocar nas bases da Azul.

Executar com:  pytest tests/test_modelo.py -v
"""
import numpy as np
import pandas as pd
import pytest
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.dummy import DummyClassifier
from sklearn.preprocessing import StandardScaler

from modelo import (HIPERPARAMETROS_CANDIDATO, METRICA_PRINCIPAL,
                    SEMENTE_PADRAO, avaliar_nos_folds, comparar_nos_folds,
                    conferir_ganho_sobre_os_pisos, criar_candidato)


@pytest.fixture
def treino():
    """60 respostas com sinal previsivel, indice fora do RangeIndex.

    O indice comeca em 500 de proposito: as particoes de `preparar_matriz`
    preservam o indice original da base, entao um `.loc` no lugar de `.iloc`
    quebraria aqui em vez de selecionar as linhas erradas em silencio.
    """
    n = 60
    x = pd.DataFrame(
        {"ATRASO": np.arange(n, dtype=float), "VIAGENS": np.arange(n, dtype=float) % 7},
        index=range(500, 500 + n),
    )
    y = pd.Series([0, 1] * (n // 2), index=x.index, name="DETRATOR")
    return x, y


@pytest.fixture
def folds():
    """Tres folds com as duas classes na validacao de cada um."""
    posicoes = np.arange(60)
    return [
        (posicoes[posicoes % 3 != k], posicoes[posicoes % 3 == k]) for k in range(3)
    ]


class PreprocessadorEspiao(BaseEstimator, TransformerMixin):
    """Escalonador que registra quantas vezes foi ajustado e com quantas linhas."""

    def __init__(self):
        self.ajustes = []

    def fit(self, x, y=None):
        self.ajustes.append(len(x))
        self.media_ = np.asarray(x).mean(axis=0)
        return self

    def transform(self, x):
        return np.asarray(x) - self.media_


def test_candidato_declara_todos_os_hiperparametros_da_configuracao():
    """DoD: nenhum hiperparametro fica no padrao implicito da biblioteca."""
    parametros = criar_candidato().get_params()
    for nome, valor in HIPERPARAMETROS_CANDIDATO.items():
        assert parametros[nome] == valor, f"{nome} nao chegou ao estimador"


def test_parada_antecipada_desligada():
    """No padrao "auto" a biblioteca separaria uma fatia aleatoria do ajuste.

    Essa fatia nao respeita `ID_GOLDENRECORD`, entao respostas da mesma pessoa
    cairiam no ajuste e na medicao interna: o vazamento que a secao 3 evita.
    """
    assert criar_candidato().get_params()["early_stopping"] is False


def test_semente_fixada_e_repassada_ao_estimador():
    assert criar_candidato().get_params()["random_state"] == SEMENTE_PADRAO
    assert criar_candidato(semente=7).get_params()["random_state"] == 7


def test_ajuste_fora_da_configuracao_declarada_e_recusado():
    """A busca do #104 varia o que esta declarado, nao inventa parametro solto."""
    with pytest.raises(ValueError, match="fora da configuracao declarada"):
        criar_candidato(profundidade_maxima=3)


def test_ajuste_declarado_sobrescreve_sem_alterar_a_configuracao(treino):
    original = dict(HIPERPARAMETROS_CANDIDATO)
    assert criar_candidato(max_iter=5).get_params()["max_iter"] == 5
    assert HIPERPARAMETROS_CANDIDATO == original


def test_mesma_semente_produz_o_mesmo_score(treino):
    """CR: rodar duas vezes seguidas tem que dar o mesmo numero."""
    x, y = treino
    ajuste = {"max_iter": 5, "min_samples_leaf": 5}
    primeiro = criar_candidato(**ajuste).fit(x, y).predict_proba(x)[:, 1]
    segundo = criar_candidato(**ajuste).fit(x, y).predict_proba(x)[:, 1]
    assert np.array_equal(primeiro, segundo)


def test_preprocessador_e_reajustado_dentro_de_cada_fold(treino, folds):
    """O template recebido nao pode sair ajustado, nem ser ajustado uma vez so."""
    x, y = treino
    espiao = PreprocessadorEspiao()

    avaliar_nos_folds(lambda: DummyClassifier(strategy="prior"), x, y, folds, espiao)

    assert espiao.ajustes == [], "o template foi ajustado em vez de clonado"
    assert not hasattr(espiao, "media_")


def test_cada_fold_ajusta_apenas_com_as_linhas_do_proprio_ajuste(treino, folds):
    x, y = treino
    vistos = []

    class Fabrica(BaseEstimator):
        """Classificador minimo que registra quantas linhas viu no ajuste."""

        def fit(self, x, y=None):
            vistos.append(len(x))
            self.classes_ = np.unique(y)
            return self

        def predict_proba(self, x):
            return np.tile([0.5, 0.5], (len(x), 1))

    avaliar_nos_folds(Fabrica, x, y, folds, StandardScaler())

    assert vistos == [len(ajuste) for ajuste, _ in folds]
    assert sum(vistos) < len(x) * len(folds), "algum fold ajustou com o treino inteiro"


def test_avaliacao_devolve_uma_linha_por_fold(treino, folds):
    x, y = treino
    tabela = avaliar_nos_folds(
        lambda: criar_candidato(max_iter=5, min_samples_leaf=5), x, y, folds,
        StandardScaler(),
    )
    assert list(tabela.index) == [1, 2, 3]
    assert {METRICA_PRINCIPAL, "roc_auc"} <= set(tabela.columns)
    assert tabela["n_validacao"].sum() == len(x)


def test_lista_de_folds_vazia_e_recusada(treino):
    x, y = treino
    with pytest.raises(ValueError, match="nenhum fold"):
        avaliar_nos_folds(DummyClassifier, x, y, [], StandardScaler())


def test_alvo_de_tamanho_diferente_e_recusado(treino, folds):
    x, y = treino
    with pytest.raises(ValueError, match="mesmo tamanho"):
        avaliar_nos_folds(DummyClassifier, x, y.iloc[:-1], folds, StandardScaler())


def test_comparacao_traz_media_e_desvio_de_cada_modelo(treino, folds):
    x, y = treino
    comparacao = comparar_nos_folds(
        {
            "trivial": lambda: DummyClassifier(strategy="prior"),
            "candidato": lambda: criar_candidato(max_iter=5, min_samples_leaf=5),
        },
        x, y, folds, StandardScaler(),
    )
    assert list(comparacao.index) == ["trivial", "candidato"]
    assert f"{METRICA_PRINCIPAL}_desvio" in comparacao.columns


def test_trava_do_cr02_falha_quando_o_candidato_nao_supera_o_piso():
    comparacao = pd.DataFrame(
        {METRICA_PRINCIPAL: [0.30, 0.42]},
        index=pd.Index(["candidato", "logistica"], name="modelo"),
    )
    with pytest.raises(AssertionError, match="nao supera"):
        conferir_ganho_sobre_os_pisos(comparacao, "candidato", ["logistica"])


def test_trava_do_cr02_passa_quando_o_candidato_supera_os_dois_pisos():
    comparacao = pd.DataFrame(
        {METRICA_PRINCIPAL: [0.55, 0.42, 0.20]},
        index=pd.Index(["candidato", "logistica", "trivial"], name="modelo"),
    )
    conferir_ganho_sobre_os_pisos(comparacao, "candidato", ["logistica", "trivial"])


def test_trava_do_cr02_recusa_modelo_ausente_da_comparacao():
    comparacao = pd.DataFrame(
        {METRICA_PRINCIPAL: [0.55]}, index=pd.Index(["candidato"], name="modelo"),
    )
    with pytest.raises(KeyError, match="ausentes"):
        conferir_ganho_sobre_os_pisos(comparacao, "candidato", ["logistica"])
