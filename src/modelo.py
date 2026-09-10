"""Primeiro modelo candidato do score de detracao: gradient boosting sobre arvores.

**Por que arvores e nao um modelo aditivo.** A secao 4.2.1 mediu que nenhuma
variavel operacional isolada tem correlacao forte com a detracao, sendo a maior a
de `ATRASO_CHEGADA`, com 0,296. A hipotese 5 da secao 4.2.3 mediu a outra metade
do argumento: a interacao entre fidelizacao e falha operacional existe e foi
confirmada (p = 0,0048 na comparacao direta entre `DIAMANTE` e `SEM CADASTRO`).
Um modelo linear representa cada variavel por um peso fixo e so alcanca essa
combinacao se alguem escrever o termo de interacao a mao. O boosting sobre
arvores a encontra por construcao, e e exatamente isso que este candidato precisa
mostrar contra o piso logistico da secao 2: se ele nao superar a logistica, a
interacao ou nao existe ou nao foi captada, e a escolha do algoritmo perde o
argumento.

**Por que o `HistGradientBoostingClassifier`.** E o gradient boosting do proprio
scikit-learn, ja declarado no `requirements.txt`, entao nao acrescenta dependencia
ao projeto nem uma segunda biblioteca para o Colab instalar. Ele discretiza cada
variavel em histogramas antes de crescer as arvores, o que faz o custo depender do
numero de bins e nao do numero de linhas, e por isso ele treina em segundos sobre
as 341.962 linhas do treino.

**Nenhum hiperparametro implicito.** O DoD do #103 exige que os hiperparametros
estejam explicitos, e `HIPERPARAMETROS_CANDIDATO` existe para isso: ele declara
tambem os que coincidem com o padrao da biblioteca, porque padrao nao declarado e
decisao que ninguem tomou. Dois deles mudam o resultado e estao comentados um a
um la embaixo, com destaque para `early_stopping=False`: no padrao `"auto"` a
biblioteca separaria sozinha uma fatia **aleatoria** do ajuste para parar cedo, e
essa fatia ignoraria o agrupamento por Cliente que a secao 3 construiu, colocando
respostas da mesma pessoa nos dois lados. A validacao deste projeto sao os folds
do #102, e nenhuma outra.

A avaliacao vive aqui junto com o modelo porque as duas decisoes andam juntas: um
numero de validacao so e comparavel se o candidato e os pisos passarem pelos
mesmos folds, com o pre-processador reajustado dentro de cada um.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Callable

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.pipeline import Pipeline

# O modulo localiza os proprios vizinhos em vez de depender de quem o importa,
# pelo mesmo motivo de `matriz.py` e `validacao.py`: sob pytest o conftest prepara
# o caminho, no Colab e na execucao direta nao ha ninguem para preparar.
_RAIZ = Path(__file__).resolve().parents[1]
for _pasta in ("src", "scripts"):
    _caminho = str(_RAIZ / _pasta)
    if _caminho not in sys.path:
        sys.path.insert(0, _caminho)

SEMENTE_PADRAO = 42

# Metrica principal da comparacao. A precisao media resume a curva de precisao
# contra revocacao, que e a leitura certa quando so um em cada cinco Clientes e
# Detrator: a acuracia premia quem nunca preve a classe rara, como a secao 2.2
# mostrou no piso trivial.
METRICA_PRINCIPAL = "precisao_media"

HIPERPARAMETROS_CANDIDATO = {
    # Passo curto, metade do padrao de 0,1: cada arvore corrige menos, o modelo
    # erra menos por excesso de confianca numa unica particao do espaco, e o
    # custo e precisar de mais iteracoes, compensado logo abaixo.
    "learning_rate": 0.05,
    # 300 arvores, tres vezes o padrao de 100, para compensar o passo curto. Sem
    # parada antecipada este numero e o unico limite do ensemble, entao ele e uma
    # decisao e nao um teto de seguranca.
    "max_iter": 300,
    # Padrao da biblioteca, declarado: com 31 folhas cada arvore ja representa
    # interacao de varias ordens, que e a razao de ter escolhido arvores.
    "max_leaf_nodes": 31,
    # Sem limite de profundidade porque quem limita o tamanho da arvore aqui e
    # `max_leaf_nodes`; fixar os dois esconderia qual dos dois esta agindo.
    "max_depth": None,
    # Cinco vezes o padrao de 20. Com 341 mil linhas, folha de 20 observacoes
    # descreve ruido de um punhado de respostas, e o modelo memoriza Cliente em
    # vez de aprender o fenomeno.
    "min_samples_leaf": 100,
    # Regularizacao L2 ligada, contra o padrao 0.0, pela mesma razao: penaliza
    # folha com pouca evidencia por tras.
    "l2_regularization": 1.0,
    # **Decisao critica.** No padrao "auto" a biblioteca liga a parada antecipada
    # sozinha acima de 10 mil linhas e separa uma fatia aleatoria do ajuste para
    # medir. Essa fatia nao respeita `ID_GOLDENRECORD`, entao respostas da mesma
    # pessoa cairiam no ajuste e na medicao interna, que e o vazamento que a
    # secao 3 existe para evitar. A validacao deste projeto sao os folds do #102.
    "early_stopping": False,
    # Sem reponderacao de classe, ao contrario da logistica da secao 2.3. La ela
    # era necessaria para o piso nao colapsar na classe majoritaria; aqui as duas
    # metricas usadas dependem so da ordenacao do score, que a reponderacao nao
    # melhora, e ela deslocaria a probabilidade predita para longe da frequencia
    # observada, estragando o escore de Brier da secao 6 e o limiar por
    # capacidade da secao 7.
    "class_weight": None,
}


def criar_candidato(
    semente: int = SEMENTE_PADRAO,
    **ajustes: object,
) -> HistGradientBoostingClassifier:
    """Devolve o candidato com os hiperparametros declarados e a semente fixada.

    `ajustes` sobrescreve `HIPERPARAMETROS_CANDIDATO` sem alterar o dicionario
    original, e existe para a busca da secao 5 (#104) variar um parametro por vez
    sem reescrever a configuracao inteira aqui. A semente entra sempre, tambem
    quando a chamada vem da busca, porque duas execucoes do mesmo ajuste precisam
    dar o mesmo numero para que a comparacao entre ajustes signifique alguma coisa.
    """
    desconhecidos = set(ajustes) - set(HIPERPARAMETROS_CANDIDATO)
    if desconhecidos:
        raise ValueError(
            "ajuste de hiperparametro fora da configuracao declarada: "
            f"{sorted(desconhecidos)}. Acrescente-o a HIPERPARAMETROS_CANDIDATO "
            "com a justificativa, em vez de passa-lo solto."
        )
    return HistGradientBoostingClassifier(
        **{**HIPERPARAMETROS_CANDIDATO, **ajustes},
        random_state=semente,
    )


def avaliar_nos_folds(
    fabrica: Callable[[], object],
    x_treino: pd.DataFrame,
    y_treino: pd.Series,
    folds: list[tuple[np.ndarray, np.ndarray]],
    preprocessador: object,
) -> pd.DataFrame:
    """Mede um modelo nos folds do #102 e devolve uma linha por fold.

    Recebe uma **fabrica**, e nao um modelo pronto, porque cada fold precisa de um
    estimador novo: reaproveitar a mesma instancia faria o segundo fold comecar do
    ajuste do primeiro, e a media dos cinco mediria um modelo que ja viu quase
    todo o treino.

    O pre-processador e clonado e **reajustado dentro de cada fold**, junto com o
    modelo. O `preparar_matriz` da secao 1.4 ajusta o pre-processador na particao
    de treino inteira, o que e o certo para o modelo final, mas usar aquela versao
    aqui deixaria a mediana da imputacao e a escala carregarem informacao das
    linhas que o fold usa como validacao. O efeito seria pequeno e invisivel, que
    e a pior combinacao possivel num numero que decide hiperparametro.

    Os indices dos folds sao posicionais, como todo `split` do scikit-learn, entao
    a selecao e por `.iloc`. As particoes de `preparar_matriz` preservam o indice
    original da base, que nao e um `RangeIndex`, e trocar um pelo outro
    selecionaria silenciosamente as linhas erradas.
    """
    if not folds:
        raise ValueError("nenhum fold recebido: chame validacao.criar_folds antes")
    if len(x_treino) != len(y_treino):
        raise ValueError(
            "x_treino e y_treino precisam ter o mesmo tamanho: "
            f"{len(x_treino)} contra {len(y_treino)}"
        )

    linhas = []
    for numero, (ajuste, validacao) in enumerate(folds, start=1):
        pipeline = Pipeline([
            ("preparo", clone(preprocessador)),
            ("modelo", fabrica()),
        ])
        pipeline.fit(x_treino.iloc[ajuste], y_treino.iloc[ajuste])

        y_validacao = y_treino.iloc[validacao]
        score = pipeline.predict_proba(x_treino.iloc[validacao])[:, 1]
        linhas.append({
            "fold": numero,
            "n_ajuste": len(ajuste),
            "n_validacao": len(validacao),
            METRICA_PRINCIPAL: float(average_precision_score(y_validacao, score)),
            "roc_auc": float(roc_auc_score(y_validacao, score)),
        })
    return pd.DataFrame(linhas).set_index("fold")


def comparar_nos_folds(
    fabricas: dict[str, Callable[[], object]],
    x_treino: pd.DataFrame,
    y_treino: pd.Series,
    folds: list[tuple[np.ndarray, np.ndarray]],
    preprocessador: object,
) -> pd.DataFrame:
    """Media e desvio por modelo, todos medidos nos mesmos folds.

    O desvio entre folds entra ao lado da media porque uma diferenca de media
    menor do que a variacao entre folds nao sustenta a afirmacao de que um modelo
    e melhor do que o outro, e e essa comparacao, e nao a media sozinha, que a
    secao 4.3 precisa reportar.
    """
    linhas = []
    for nome, fabrica in fabricas.items():
        por_fold = avaliar_nos_folds(fabrica, x_treino, y_treino, folds, preprocessador)
        linhas.append({
            "modelo": nome,
            METRICA_PRINCIPAL: por_fold[METRICA_PRINCIPAL].mean(),
            f"{METRICA_PRINCIPAL}_desvio": por_fold[METRICA_PRINCIPAL].std(),
            "roc_auc": por_fold["roc_auc"].mean(),
            "roc_auc_desvio": por_fold["roc_auc"].std(),
        })
    return pd.DataFrame(linhas).set_index("modelo")


def conferir_ganho_sobre_os_pisos(
    comparacao: pd.DataFrame,
    candidato: str,
    pisos: list[str],
    metrica: str = METRICA_PRINCIPAL,
) -> None:
    """Interrompe a execucao se o candidato nao superar todos os pisos.

    E o CR02 do #103 virando trava: sem ela, um candidato pior do que a regressao
    logistica seguiria para as secoes de ajuste e de metricas sem que nada no
    caminho recusasse, e a tabela comparativa da secao 9 so denunciaria o problema
    no fim. A conferencia e na media dos folds, nunca no teste, que continua
    intocado ate a secao 6.
    """
    faltando = [nome for nome in [candidato, *pisos] if nome not in comparacao.index]
    if faltando:
        raise KeyError(f"modelos ausentes da comparacao: {faltando}")

    valor_candidato = comparacao.loc[candidato, metrica]
    perdeu_para = [
        nome for nome in pisos if valor_candidato <= comparacao.loc[nome, metrica]
    ]
    if perdeu_para:
        raise AssertionError(
            f"o candidato nao supera {perdeu_para} em {metrica} na validacao: "
            f"{valor_candidato:.4f} contra "
            + ", ".join(f"{nome}={comparacao.loc[nome, metrica]:.4f}" for nome in pisos)
            + ". Rever a escolha do algoritmo antes de seguir para a secao 5."
        )
