"""Custo de ajuste das duas bibliotecas de boosting candidatas (card 04A, #185).

**O que este modulo resolve.** A dupla de Modelos de Ensemble precisa escolher
entre o `HistGradientBoostingClassifier`, que ja vem no scikit-learn, e o
`XGBClassifier`, que acrescenta uma dependencia ao projeto e a sessao do Colab.
A escolha nao e de gosto: os cards seguintes (#186, #187 e #188) rodam uma busca
aleatoria de 40 iteracoes sobre os folds do contrato, e uma sessao do Colab cai
depois de algumas horas. Se um ajuste unico custa tempo demais, a busca nao cabe
na sessao e o card seguinte trava. Este modulo produz o numero que sustenta a
decisao: quanto custa **um** ajuste completo de cada biblioteca sobre a matriz
que o contrato entrega.

**Por que a medicao e de um ajuste so, sem busca e sem validacao cruzada.** O que
se quer estimar e o custo unitario; a busca e a validacao sao multiplicadores
conhecidos, e `estimar_busca` faz essa conta. Medir com busca embutida misturaria
o custo da biblioteca com o custo do protocolo e ainda criaria, aqui, uma segunda
particao alem da do contrato, que e exatamente o que a secao 3 proibe. Por isso
este modulo nunca instancia particionador nem validador proprio: ele recebe a
matriz de treino ja transformada e o alvo, e nada mais.

**Por que os hiperparametros sao iguais nos dois lados.** Comparar tempo de
bibliotecas com configuracoes diferentes nao mede biblioteca, mede configuracao.
`HIPERPARAMETROS_COMPARACAO` declara o par equivalente termo a termo, com mesmo
passo, mesmo numero de arvores, mesmo numero de folhas, mesmo numero de bins,
mesma semente e histograma nos dois; os nomes de cada biblioteca sao traduzidos
logo abaixo. Os valores vem de `modelo.HIPERPARAMETROS_CANDIDATO`, para que o
tempo medido seja o tempo do modelo que o projeto realmente treina, e nao o de um
modelo de brinquedo.

**Por que a memoria e medida por RSS amostrado, e nao por `tracemalloc`.** As duas
bibliotecas alocam a maior parte da memoria em codigo nativo, fora do alocador do
Python; `tracemalloc` enxerga so o lado Python e devolveria um numero pequeno e
errado. O `psutil` le o RSS do processo, que inclui as alocacoes nativas, e uma
amostragem em thread separada captura o pico durante o ajuste.
"""

from __future__ import annotations

import sys
import threading
import time
from pathlib import Path

import numpy as np
import pandas as pd
import psutil
from sklearn.base import clone
from sklearn.ensemble import HistGradientBoostingClassifier
from xgboost import XGBClassifier

# O modulo localiza os proprios vizinhos em vez de depender de quem o importa,
# pelo mesmo motivo de `matriz.py` e `modelo.py`: sob pytest o conftest prepara o
# caminho, no Colab e na execucao direta nao ha ninguem para preparar.
_RAIZ = Path(__file__).resolve().parents[1]
for _pasta in ("src", "scripts"):
    _caminho = str(_RAIZ / _pasta)
    if _caminho not in sys.path:
        sys.path.insert(0, _caminho)

import modelo  # noqa: E402

SEMENTE_PADRAO = modelo.SEMENTE_PADRAO

# Intervalo da amostragem de memoria. Curto o bastante para nao perder o pico de
# um ajuste de poucos segundos, longo o bastante para o proprio amostrador nao
# disputar CPU com a biblioteca que esta sendo medida.
INTERVALO_AMOSTRAGEM_S = 0.05

# Numero de bins do histograma. E o padrao do `HistGradientBoostingClassifier` e
# esta declarado dos dois lados porque e ele, e nao o numero de linhas, que manda
# no custo de um boosting por histograma: deixar o padrao de cada biblioteca
# valer sozinho compararia duas discretizacoes diferentes.
BINS_HISTOGRAMA = 255

# Par equivalente termo a termo. A chave e o conceito; a traducao para o nome de
# cada biblioteca esta em `_parametros_hist` e `_parametros_xgb`.
HIPERPARAMETROS_COMPARACAO = {
    "passo": modelo.HIPERPARAMETROS_CANDIDATO["learning_rate"],
    "arvores": modelo.HIPERPARAMETROS_CANDIDATO["max_iter"],
    "folhas": modelo.HIPERPARAMETROS_CANDIDATO["max_leaf_nodes"],
    "bins": BINS_HISTOGRAMA,
}


def _parametros_hist(random_state: int) -> dict[str, object]:
    return {
        "learning_rate": HIPERPARAMETROS_COMPARACAO["passo"],
        "max_iter": HIPERPARAMETROS_COMPARACAO["arvores"],
        "max_leaf_nodes": HIPERPARAMETROS_COMPARACAO["folhas"],
        "max_bins": HIPERPARAMETROS_COMPARACAO["bins"],
        # Mesma razao do #103: no padrao "auto" a biblioteca separaria sozinha
        # uma fatia aleatoria do ajuste, ignorando o agrupamento por Cliente. Uma
        # medicao de tempo com parada antecipada ligada tambem mediria menos
        # arvores do que as declaradas, e a comparacao perderia o sentido.
        "early_stopping": False,
        "random_state": random_state,
    }


def _parametros_xgb(random_state: int) -> dict[str, object]:
    return {
        "learning_rate": HIPERPARAMETROS_COMPARACAO["passo"],
        "n_estimators": HIPERPARAMETROS_COMPARACAO["arvores"],
        # O XGBoost cresce por profundidade no padrao; `lossguide` com
        # `max_depth=0` e o modo que corresponde ao crescimento por folhas do
        # scikit-learn, que e o que torna `max_leaves` comparavel a
        # `max_leaf_nodes`.
        "grow_policy": "lossguide",
        "max_depth": 0,
        "max_leaves": HIPERPARAMETROS_COMPARACAO["folhas"],
        "max_bin": HIPERPARAMETROS_COMPARACAO["bins"],
        "tree_method": "hist",
        "random_state": random_state,
    }


def construir_candidatos(random_state: int = SEMENTE_PADRAO) -> dict[str, object]:
    """Devolve as duas bibliotecas configuradas com o par equivalente.

    A chave e o nome pelo qual a decisao sera escrita, e e ela que aparece na
    tabela de medicao e no markdown do notebook.
    """
    return {
        "HistGradientBoostingClassifier": HistGradientBoostingClassifier(
            **_parametros_hist(random_state)
        ),
        "XGBClassifier": XGBClassifier(**_parametros_xgb(random_state)),
    }


class _AmostradorDeMemoria:
    """Le o RSS do processo em intervalos fixos e guarda o maior valor visto."""

    def __init__(self, intervalo_s: float = INTERVALO_AMOSTRAGEM_S) -> None:
        self._intervalo_s = intervalo_s
        self._processo = psutil.Process()
        self._parar = threading.Event()
        self._thread = threading.Thread(target=self._amostrar, daemon=True)
        self.inicial_bytes = self._processo.memory_info().rss
        self.pico_bytes = self.inicial_bytes

    def _amostrar(self) -> None:
        while not self._parar.is_set():
            self.pico_bytes = max(self.pico_bytes, self._processo.memory_info().rss)
            self._parar.wait(self._intervalo_s)

    def __enter__(self) -> "_AmostradorDeMemoria":
        self._thread.start()
        return self

    def __exit__(self, *_excecao) -> None:
        self._parar.set()
        self._thread.join()
        # Uma ultima leitura fecha a janela entre a penultima amostra e o fim do
        # ajuste, onde o pico pode acontecer sem nenhuma amostra o ver.
        self.pico_bytes = max(self.pico_bytes, self._processo.memory_info().rss)


def medir_ajuste(
    estimador,
    matriz_treino,
    y_treino,
    random_state: int = SEMENTE_PADRAO,
) -> dict[str, object]:
    """Ajusta o estimador **uma** vez e devolve tempo, pico e delta de memoria.

    O estimador chega clonado para que a medicao nunca aproveite um ajuste
    anterior: um modelo reaproveitado mediria um tempo menor do que o real, que e
    justamente o erro que faria a decisao da biblioteca sair errada.
    """
    candidato = clone(estimador)
    with _AmostradorDeMemoria() as amostrador:
        inicio = time.perf_counter()
        candidato.fit(matriz_treino, y_treino)
        tempo_s = time.perf_counter() - inicio

    mb = 1024 * 1024
    return {
        "tempo_ajuste_s": tempo_s,
        "pico_memoria_mb": amostrador.pico_bytes / mb,
        "delta_memoria_mb": (amostrador.pico_bytes - amostrador.inicial_bytes) / mb,
        "random_state": random_state,
        "n_linhas": int(np.shape(matriz_treino)[0]),
        "n_colunas": int(np.shape(matriz_treino)[1]),
        "estimador": candidato,
    }


def medir_bibliotecas(
    matriz_treino,
    y_treino,
    random_state: int = SEMENTE_PADRAO,
    candidatos: dict[str, object] | None = None,
) -> pd.DataFrame:
    """Tabela de medicao do CR04: uma linha por biblioteca.

    Recebe a matriz **ja transformada** pelo pre-processador do contrato. Passar
    aqui as features cruas e reajustar qualquer coisa seria criar um segundo
    pre-processamento fora do contrato, e a comparacao deixaria de medir so a
    biblioteca.
    """
    candidatos = candidatos or construir_candidatos(random_state)
    linhas = []
    for nome, estimador in candidatos.items():
        medicao = medir_ajuste(estimador, matriz_treino, y_treino, random_state=random_state)
        medicao.pop("estimador")
        linhas.append({"biblioteca": nome, **medicao})
    return pd.DataFrame(linhas).set_index("biblioteca")


def estimar_busca(
    tempo_ajuste_s: float,
    n_iteracoes: int = 40,
    n_folds: int = 5,
) -> float:
    """Horas estimadas para a busca dos cards seguintes, em ajustes sequenciais.

    A conta e deliberadamente otimista: conta apenas os ajustes e ignora
    transformacao, calculo de metrica e o fato de cada fold custar quase o treino
    inteiro. Se nem essa estimativa couber na sessao do Colab, a busca com
    certeza nao cabe.
    """
    if n_iteracoes <= 0 or n_folds <= 0:
        raise ValueError("A busca precisa de pelo menos uma iteracao e um fold.")
    return tempo_ajuste_s * n_iteracoes * n_folds / 3600


def escolher_biblioteca(
    tabela: pd.DataFrame,
    orcamento_horas: float = 3.0,
    n_iteracoes: int = 40,
    n_folds: int = 5,
) -> dict[str, object]:
    """Aplica o criterio do CR05 sobre a tabela de medicao.

    O criterio tem uma ordem, e ela importa: primeiro descarta quem nao cabe no
    orcamento de sessao, porque uma biblioteca que estoura a sessao nao e uma
    opcao mais lenta, e uma opcao que nao existe. Entre as que cabem vence a mais
    barata de manter, e ai o `HistGradientBoostingClassifier` leva por nao
    acrescentar dependencia; ele so perde se for lento a ponto de tirar a busca
    do orcamento.
    """
    estimativas = {
        nome: estimar_busca(linha["tempo_ajuste_s"], n_iteracoes, n_folds)
        for nome, linha in tabela.iterrows()
    }
    cabem = {nome: horas for nome, horas in estimativas.items() if horas <= orcamento_horas}

    if not cabem:
        escolhida = min(estimativas, key=estimativas.get)
        motivo = (
            f"Nenhuma das duas cabe em {orcamento_horas:.1f}h de sessao com "
            f"{n_iteracoes} iteracoes vezes {n_folds} folds; a decisao sobe para a "
            f"dupla de Metricas e Decisoes reduzir a busca. A menos cara e "
            f"{escolhida}, com {estimativas[escolhida]:.2f}h."
        )
    elif "HistGradientBoostingClassifier" in cabem:
        escolhida = "HistGradientBoostingClassifier"
        motivo = (
            f"Cabe em {cabem[escolhida]:.2f}h, dentro do orcamento de "
            f"{orcamento_horas:.1f}h, e nao acrescenta dependencia ao projeto nem "
            f"instalacao a sessao do Colab."
        )
    else:
        escolhida = min(cabem, key=cabem.get)
        motivo = (
            f"O HistGradientBoostingClassifier nao cabe no orcamento de "
            f"{orcamento_horas:.1f}h; {escolhida} cabe, com {cabem[escolhida]:.2f}h, "
            f"e a dependencia extra se paga por viabilizar a busca."
        )

    return {
        "escolhida": escolhida,
        "estimativas_horas": estimativas,
        "orcamento_horas": orcamento_horas,
        "n_iteracoes": n_iteracoes,
        "n_folds": n_folds,
        "justificativa": motivo,
    }
