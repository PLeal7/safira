"""Espacos de busca aleatoria do Random Forest e do Gradient Boosting (#186).

**Por que RandomizedSearchCV e nao a grade fatorial do #104.** O #104 buscou tres
eixos do candidato unico com doze combinacoes, numero que ainda cabe inteiro no
documento. Random Forest e Gradient Boosting tem cinco a sete eixos cada, e uma
grade fatorial dessa dimensao custaria centenas de ajustes sobre os 341.962
registros do treino para cobrir uma fracao pequena do espaco. A busca aleatoria
troca cobertura exaustiva por cobertura proporcional ao numero de amostras
sorteadas, que e a troca certa quando o objetivo e encontrar uma vizinhanca boa
do espaco, e nao mapear cada aresta dele.

**#185 ainda nao decidiu a biblioteca de boosting.** O card pede para manter as
duas versoes, `HistGradientBoostingClassifier` e `XGBClassifier`, ate a decisao
do #185 e remover a descartada no mesmo dia em que ela sair. Como o #185 segue
aberto, `ESPACO_GRADIENT_BOOSTING_HISTGB` e `ESPACO_GRADIENT_BOOSTING_XGBOOST`
convivem aqui, cada um com o proprio custo por ajuste ainda por medir: os
intervalos abaixo vem da literatura de cada biblioteca e da mesma logica de
regularizacao do #103, nao de um perfil de tempo de execucao que o #185 ainda
nao produziu. Quando a decisao sair, o espaco da biblioteca descartada e o bloco
correspondente deste modulo saem no mesmo commit.

**Os numeros que ancoram os intervalos.** A base analitica tem 484.915 registros
e 20,44% de Detratores (secao 4.2.1 da documentacao); o treino usado pela busca,
apos o split por Cliente do #102, tem 341.962 linhas. O contrato de features do
card 01 (`FEATURE_SET_V1`, em `scripts/preprocessamento_nps.py`) declara 11
features brutas. Esse numero e pequeno para os padroes que motivam os valores
padrao de `max_features` (`"sqrt"` e `"log2"` datam de bases com centenas de
colunas) e por isso o espaco do Random Forest usa fracao continua em vez desses
atalhos, como o comentario de `ESPACO_RANDOM_FOREST` detalha.

**scipy.stats onde o eixo e continuo, lista onde e categorico.** `RandomizedSearchCV`
aceita as duas formas no mesmo dicionario: distribuicoes com `.rvs()` para eixos
numericos, e listas para amostragem uniforme quando o eixo e uma escolha (a
biblioteca de reponderacao, por exemplo, nao tem escala). Forcar uma distribuicao
scipy sobre uma escolha categorica exigiria uma `rv_discrete` a mais so para
imitar `random.choice`, sem nenhum ganho sobre a lista.
"""

from __future__ import annotations

import time
from typing import Callable

from scipy import stats
from sklearn.base import clone
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.pipeline import Pipeline
from xgboost import XGBClassifier

SEMENTE_PADRAO = 42

# Proporcao negativos/positivos da base (385.775 / 99.140), usada para calibrar
# os eixos de reponderacao do Random Forest e do XGBoost. Documentada aqui, e
# nao recalculada a cada busca, para que os dois espacos usem o mesmo numero.
RAZAO_DESBALANCEAMENTO = 385_775 / 99_140

ESPACO_RANDOM_FOREST = {
    # 200 a 600 arvores. Com 341.962 linhas no treino, a variancia de cada
    # arvore ja e pequena; acima de algumas centenas o ganho de agregar mais
    # arvores fica marginal e o custo segue linear no numero delas, ao
    # contrario do Gradient Boosting, onde mais iteracoes tambem mudam o vies.
    "n_estimators": stats.randint(200, 601),
    # 3 a 20 folhas de profundidade. O teto vem de log2(341.962) ~= 18,4: uma
    # arvore balanceada raramente precisa de mais niveis do que isso para
    # separar o treino inteiro, e permitir profundidade ilimitada (`None`)
    # arriscaria arvores memorizando Cliente em vez de aprender o fenomeno, o
    # mesmo risco que a secao de `min_samples_leaf` do #103 documenta.
    "max_depth": stats.randint(3, 21),
    # 1 a 100 observacoes por folha. Cem e o valor que o #103 escolheu para o
    # Gradient Boosting nesta mesma base, pela mesma razao: folha menor do que
    # isso descreve ruido de um punhado de respostas. O piso em 1 mantem a
    # ponta nao regularizada do espaco disponivel para a busca comparar.
    "min_samples_leaf": stats.randint(1, 101),
    # Fracao continua de 0,3 a 1,0 das colunas por split, e nao `"sqrt"` ou
    # `"log2"`. As duas strings datam de bases com centenas de features; aqui o
    # contrato do card 01 declara 11 features brutas, `"sqrt"` amostraria
    # cerca de 3 delas por split e jogaria fora a maior parte do sinal
    # disponivel a cada arvore. Uma fracao ampla preserva a decorrelacao entre
    # arvores sem sufocar o sinal.
    "max_features": stats.uniform(0.3, 0.7),
    # Sem reponderacao, reponderacao pelas classes observadas neste ajuste, e
    # reponderacao por arvore (efeito parecido com sub-amostrar a classe
    # majoritaria a cada bootstrap). As tres entram porque a taxa de 20,44% de
    # detracao e desbalanceamento moderado, e ao contrario do candidato unico
    # do #103 (onde a reponderacao so atrapalharia a probabilidade calibrada
    # de um `HistGradientBoostingClassifier`), o Random Forest nao usa a saida
    # como probabilidade de risco por construcao: cada arvore vota, e a
    # reponderacao pode ajudar a fronteira sem o mesmo custo de calibracao.
    # A busca decide empiricamente, nesta base, qual das tres funciona melhor.
    "class_weight": ["balanced", "balanced_subsample", None],
}


ESPACO_GRADIENT_BOOSTING_HISTGB = {
    # Escala log de 0,01 a 0,3. O #103 fixou 0,05 (metade do padrao de 0,1) e
    # a grade do #104 testou 0,05 e 0,10; a busca aleatoria amplia essa faixa
    # para os dois lados. Log-uniforme, e nao uniforme, porque o efeito do
    # passo e multiplicativo sobre o numero de iteracoes necessario: 0,01 para
    # 0,02 muda o ajuste tanto quanto 0,15 para 0,30.
    "learning_rate": stats.loguniform(0.01, 0.3),
    # 15 a 127 folhas por arvore. O #103 usa o padrao de 31 e a grade do #104
    # testou 31 e 63; o teto de 127 (2^7 - 1) da a busca uma arvore ainda mais
    # profunda para comparar sem passar a ordem de grandeza de `max_iter`.
    "max_leaf_nodes": stats.randint(15, 128),
    # 100 a 600 iteracoes, cobrindo os tres pontos da grade do #104 (150, 300 e
    # 600) e as bordas em torno deles. Sem parada antecipada (fixa em `False`
    # em `criar_candidato`, por causa do vazamento por Cliente que o #103
    # documenta), este numero segue sendo o unico limite do ensemble.
    "max_iter": stats.randint(100, 601),
    # 0,0 a 2,0 de regularizacao L2. O #103 fixou 1,0 contra o padrao 0,0 da
    # biblioteca; o intervalo cobre o padrao original e o dobro da escolha do
    # #103 para a busca decidir se penalizar mais ou menos folhas com pouca
    # evidencia melhora a precisao media.
    "l2_regularization": stats.uniform(0.0, 2.0),
    # 20 a 200 observacoes por folha, com o mesmo raciocinio de
    # `ESPACO_RANDOM_FOREST`: folha pequena sobre 341.962 linhas memoriza
    # Cliente. O piso de 20 e o padrao da biblioteca, mantido para a busca
    # tambem considerar o extremo pouco regularizado.
    "min_samples_leaf": stats.randint(20, 201),
    # Sem reponderacao e reponderacao balanceada. O #103 documenta por que
    # `class_weight=None` foi a escolha do candidato unico: as duas metricas
    # de seleção dependem so da ordenacao do score, e reponderar deslocaria a
    # probabilidade predita para longe da frequencia observada, o que piora o
    # Brier da secao 6 e o limiar por capacidade da secao 7. O eixo entra na
    # busca mesmo assim para que a comparacao empirica, e nao so o argumento
    # teorico, sustente a escolha final.
    "class_weight": [None, "balanced"],
}


ESPACO_GRADIENT_BOOSTING_XGBOOST = {
    # Mesma faixa e mesma razao log-uniforme do HistGB: o efeito do passo
    # sobre o numero de arvores necessario e multiplicativo nas duas
    # bibliotecas, por serem as duas gradient boosting sobre arvores.
    "learning_rate": stats.loguniform(0.01, 0.3),
    # 3 a 10 niveis. O XGBoost limita a arvore por profundidade, e nao por
    # numero de folhas como o HistGB; 10 niveis já produzem ate 2^10 folhas,
    # bem acima do teto de 127 usado no espaco irmao, entao o eixo comparavel
    # entre as duas bibliotecas e a ordem de interacao alcancada, nao o numero
    # bruto do parametro.
    "max_depth": stats.randint(3, 11),
    # 100 a 600 arvores, no mesmo intervalo de `max_iter` do HistGB, para que
    # o custo por ajuste medido no #185 seja comparavel entre as duas
    # bibliotecas sob o mesmo orcamento de iteracoes.
    "n_estimators": stats.randint(100, 601),
    # 1 a 20, o equivalente do XGBoost a `min_samples_leaf`: soma minima de
    # peso das observacoes numa folha antes dela poder ser criada. O teto de
    # 20 acompanha a mesma logica de regularizacao contra folha memorizando
    # Cliente, numa escala distinta da do HistGB porque o parametro pesa
    # gradiente e nao conta linhas diretamente.
    "min_child_weight": stats.randint(1, 21),
    # 0,0 a 2,0 de regularizacao L2, mesma faixa de `l2_regularization` do
    # HistGB, pelo nome equivalente no XGBoost.
    "reg_lambda": stats.uniform(0.0, 2.0),
    # 0,6 a 1,0 das linhas por arvore. Sub-amostrar linhas e o mecanismo de
    # regularizacao do XGBoost que nao tem par direto no HistGB (que discretiza
    # em histogramas em vez de amostrar), entao o piso de 0,6 evita perder
    # tanta informacao por arvore que o ensemble precisasse de muito mais
    # iteracoes para compensar.
    "subsample": stats.uniform(0.6, 0.4),
    # 0,5 a 1,0 das colunas por arvore, equivalente a `max_features` do Random
    # Forest e sujeito ao mesmo argumento: com 11 features brutas no contrato
    # do card 01, um piso baixo deixaria cada arvore enxergar poucas colunas.
    "colsample_bytree": stats.uniform(0.5, 0.5),
    # 1,0 (sem reponderacao) a RAZAO_DESBALANCEAMENTO (~3,89, a proporcao
    # negativos/positivos da base). O XGBoost nao tem versao "balanced" pronta
    # como o scikit-learn; `scale_pos_weight` e o parametro que multiplica o
    # gradiente da classe positiva, e o teto no valor exato da proporcao
    # observada e o ponto em que a reponderacao neutraliza o desbalanceamento
    # por completo.
    "scale_pos_weight": stats.uniform(1.0, RAZAO_DESBALANCEAMENTO - 1.0),
}


# Agrupa os dois espacos de Gradient Boosting pela biblioteca a que pertencem,
# para que o notebook e os testes iterem sem repetir os dois nomes soltos. A
# chave e o nome da biblioteca, nao um rotulo livre, porque e exatamente essa
# chave que sai do dicionario no dia em que o #185 decidir qual descartar.
ESPACOS_GRADIENT_BOOSTING = {
    "hist_gradient_boosting": ESPACO_GRADIENT_BOOSTING_HISTGB,
    "xgboost": ESPACO_GRADIENT_BOOSTING_XGBOOST,
}


# Espaco -> estimador que o consome, para os testes instanciarem cada amostra
# sorteada sem repetir a associacao em cada teste.
ESTIMADOR_POR_ESPACO = {
    "random_forest": (RandomForestClassifier, ESPACO_RANDOM_FOREST),
    "gradient_boosting_hist_gradient_boosting": (
        HistGradientBoostingClassifier, ESPACO_GRADIENT_BOOSTING_HISTGB,
    ),
    "gradient_boosting_xgboost": (XGBClassifier, ESPACO_GRADIENT_BOOSTING_XGBOOST),
}


# ---------------------------------------------------------------------------
# Pipeline do Gradient Boosting (card 11, #188)
# ---------------------------------------------------------------------------
#
# O card 11 foi dividido para liberar o D3 inteiro para a busca do #190: o
# Gradient Boosting entra aqui como um unico objeto que encadeia o
# pre-processador do contrato e o estimador, pela mesma razao do pipeline da
# logistica (#208) e do Random Forest (#187). Enquanto o `ColumnTransformer`
# vive solto, quem ajusta decide onde ajustar, e a escolha mais comoda, ajustar
# uma vez no treino inteiro e so transformar dentro dos folds, e a que vaza.
# Dentro de um `Pipeline`, a busca do #190 chama `fit` no objeto inteiro a cada
# fold e o pre-processador e reajustado ali.
#
# A biblioteca e o `HistGradientBoostingClassifier`: o #185 decidiu por ele em
# vez do `XGBClassifier` porque e o gradient boosting do proprio scikit-learn,
# ja fixado no requirements, sem dependencia extra para o Colab instalar.

# Nomes dos passos, iguais aos de `pipeline_logistica` (#208): a busca do #190
# enderecada hiperparametro por `passo__parametro`, e os testes deste modulo
# leem o estimador ajustado pelo mesmo nome.
PASSO_PREPARO = "preparo"
PASSO_MODELO = "modelo"


def criar_pipeline_gradient_boosting(
    preprocessador,
    random_state: int = SEMENTE_PADRAO,
    **hiperparametros,
) -> Pipeline:
    """Encadeia o pre-processador do contrato e o `HistGradientBoostingClassifier`.

    `preprocessador` e `preparo["preprocessador"]`, o `ColumnTransformer` que
    `matriz.preparar_matriz` monta a partir da allowlist. Ele entra **clonado**:
    mesma especificacao, sem o estado que `preparar_matriz` ja ajustou no
    treino. Remontar o `ColumnTransformer` aqui criaria uma segunda definicao do
    contrato; aproveitar o objeto ja ajustado faria o primeiro `fit` do fold
    partir de medianas e quartis que viram as linhas de validacao daquele fold.

    Sem `hiperparametros`, o estimador nasce no padrao da biblioteca em todo
    eixo de busca (`learning_rate`, `max_iter`, `max_leaf_nodes`,
    `l2_regularization`, `min_samples_leaf`), que e o que o card pede para a
    linha de base: quem escolhe esses valores e a busca do D3 (#190), nao esta
    funcao. `**hiperparametros` existe para a busca e os testes montarem uma
    combinacao especifica sem escrever o `Pipeline` a mao.

    O unico padrao que esta funcao nao deixa passar e `early_stopping`. No
    padrao `"auto"` da biblioteca, ele liga sozinho acima de 10 mil linhas e
    separa uma fatia **aleatoria** do ajuste para medir a parada antecipada;
    essa fatia nao respeita `ID_GOLDENRECORD`, entao respostas do mesmo Cliente
    cairiam dos dois lados, o mesmo vazamento que `modelo.HIPERPARAMETROS_CANDIDATO`
    (#103) documenta e evita. A validacao deste projeto sao os folds do
    contrato, e nenhuma outra; por isso `early_stopping=False` e fixado aqui, e
    nao deixado como argumento de `hiperparametros`, para que nenhuma chamada
    religue-o por engano.

    `random_state` e obrigatorio no sentido pratico: o `HistGradientBoostingClassifier`
    sorteia o subamostra dos bins do histograma, e sem semente fixa dois ajustes
    identicos produzem arvores diferentes, o que tornaria qualquer diferenca de
    metrica na busca do #190 indistinguivel de sorte.
    """
    parametros = {**hiperparametros, "early_stopping": False, "random_state": random_state}
    return Pipeline([
        (PASSO_PREPARO, clone(preprocessador)),
        (PASSO_MODELO, HistGradientBoostingClassifier(**parametros)),
    ])


def medir_linha_de_base(
    pipeline: Pipeline,
    x_treino,
    y_treino,
    x_avaliacao,
    y_avaliacao,
    avaliar: Callable,
) -> dict[str, object]:
    """Ajusta o pipeline no treino, pontua a avaliacao e devolve o que `avaliar` calcular.

    E a referencia do card: o desempenho do Gradient Boosting **antes** de
    qualquer busca. Sem ela, o ganho que o #190 reportar nao tem contra o que
    ser lido.

    `x_treino` e `preparo["x"]["treino"]`, a matriz **crua**, e nao
    `preparo["matrizes"]["treino"]`: passar a matriz ja transformada faria o
    `ColumnTransformer` do pipeline ser ajustado sobre a saida de outro, sem
    erro nenhum e com colunas que a base nao tem. `x_avaliacao`/`y_avaliacao`
    sao a particao de validacao de `preparo`, e nao um recorte novo: um
    splitter proprio aqui seria a terceira particao que o card proibe, competindo
    com a temporal do card 01 e os folds do contrato.

    `avaliar` e a funcao do card 05 (#241), e entra como argumento por dois
    motivos: o modulo continua importavel enquanto aquele card nao esta em
    `develop` (o pipeline e os testes deste card sao commitados com dados
    sinteticos e a medicao entra assim que `avaliar` chegar), e nenhuma metrica
    e nenhuma particao e definida aqui. O dicionario de metricas volta como
    `avaliar` o devolveu, sem renomear chave, porque a tabela comparativa do
    card 18A.1 depende de as quatro duplas falarem a mesma lingua. `y_proba` e a
    coluna 1 de `predict_proba`, a probabilidade de Detrator: Precisao Media e
    ROC-AUC sao calculadas sobre o score continuo, e a coluna errada devolveria
    um numero valido e errado.
    """
    if not callable(avaliar):
        raise TypeError(
            "avaliar precisa ser a funcao do card 05 (#241), com assinatura "
            "avaliar(y_true, y_pred, y_proba)"
        )

    inicio = time.perf_counter()
    pipeline.fit(x_treino, y_treino)
    y_pred = pipeline.predict(x_avaliacao)
    y_proba = pipeline.predict_proba(x_avaliacao)[:, 1]
    metricas = avaliar(y_avaliacao, y_pred, y_proba)
    tempo_total_s = time.perf_counter() - inicio

    return {
        "metricas": metricas,
        "tempo_total_s": tempo_total_s,
        "random_state": pipeline.named_steps[PASSO_MODELO].random_state,
        "n_treino": int(len(y_treino)),
        "n_avaliacao": int(len(y_avaliacao)),
    }
