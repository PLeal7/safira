"""Permutation importance do melhor ensemble (card 14A, #191).

**O que este modulo resolve.** A Azul precisa saber quais fatores operacionais
mais pesam na previsao de detracao, e o grupo decidiu nao usar SHAP. A resposta
aqui e a permutation importance: embaralhar uma feature de cada vez na particao
de avaliacao e medir quanto a metrica da busca cai. Uma queda grande diz que o
modelo depende daquela feature para acertar; uma queda nula diz que ele passa
bem sem ela.

**A trava que justifica o card: a importancia e das features originais do
contrato.** O pipeline dos ensembles comeca no `ColumnTransformer` do contrato,
que abre cada categorica em varias colunas one-hot e acrescenta indicadores de
ausencia. Medir a importancia depois dele espalharia `TIER_VIAGEM`, por exemplo,
em uma coluna por tier, e o ranking passaria a comparar pedacos de feature com
features inteiras. Por isso `calcular_importancia` recebe o **pipeline inteiro**
e a matriz **crua** da particao: o `permutation_importance` embaralha as colunas
que o contrato entrega, e o pre-processador roda depois, dentro do pipeline,
sobre a coluna ja embaralhada. Uma matriz transformada e recusada.

**As outras tres travas, e onde cada uma mora:**

- **particao de avaliacao, nunca treino** (CR03). `importancia_no_contrato` le
  a particao pelo nome do contrato e recusa `"treino"`: no treino, um modelo que
  memorizou uma feature parece depender dela, e o ranking premiaria memorizacao;
- **mesmo `scoring` da busca** (CR02). O argumento e obrigatorio e sem padrao,
  pelo mesmo motivo de `busca_random_forest`: um padrao aqui seria a porta para
  medir importancia por um criterio diferente do que escolheu o modelo;
- **`n_repeats` e `random_state` fixos** (CR02). Sem semente, dois
  embaralhamentos diferentes dao quedas diferentes, e um empate entre a terceira
  e a quarta feature trocaria o ranking de uma execucao para outra.

O que este modulo deliberadamente **nao** faz:

- **nao treina modelo.** Recebe o pipeline ja ajustado no treino, reconstruido
  pelo JSON da busca de cada ensemble;
- **nao calcula metrica propria.** A escolha do melhor ensemble le os
  dicionarios que `avaliar`, do card 05A.1 (#241), devolveu;
- **nao explica causa.** Importancia por permutacao mede o quanto o modelo
  **usa** a feature, nao o quanto ela **causa** detracao. A leitura causal fica
  proibida no texto do notebook, e o motivo esta la.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.exceptions import NotFittedError
from sklearn.inspection import permutation_importance
from sklearn.utils.validation import check_is_fitted

# O modulo localiza os proprios vizinhos em vez de depender de quem o importa,
# pelo mesmo motivo de `ensembles.py`: sob pytest o conftest prepara o caminho,
# no Colab e na execucao direta nao ha ninguem para preparar.
_RAIZ = Path(__file__).resolve().parents[1]
for _pasta in ("src", "scripts"):
    _caminho = str(_RAIZ / _pasta)
    if _caminho not in sys.path:
        sys.path.insert(0, _caminho)

import split  # noqa: E402
from ensembles import SEMENTE_PADRAO  # noqa: E402
from matriz import PREFIXOS_PROIBIDOS  # noqa: E402

# Dez embaralhamentos por feature. Com menos, o desvio padrao da queda fica
# instavel demais para dizer se a terceira e a quarta feature estao de fato
# separadas; com mais, o custo cresce linearmente (cada repeticao e uma previsao
# inteira da particao por feature) sem mudar a ordem das primeiras posicoes.
N_REPETICOES = 10

# A particao em que a importancia e medida. E a mesma em que a secao 8.2 mede o
# numero oficial com `avaliar`: o ranking explica o modelo exatamente onde o
# desempenho dele foi lido. O teste fica reservado para a comparacao final entre
# duplas (card 18A.1) e nao e consumido aqui.
PARTICAO_AVALIACAO = "validacao"

# Metrica de `avaliar` que decide o melhor ensemble. E o F2 porque e o mesmo
# criterio que as duas buscas otimizaram (#242) e o mesmo `scoring` que a
# permutation importance usa: escolher o modelo por uma metrica e explica-lo por
# outra misturaria duas perguntas.
METRICA_ESCOLHA = "F2"

# Quantas features vao para o ranking publicado. O #192 gera os graficos de
# dependencia parcial exatamente dessas tres.
N_TOPO = 3

# As tres features que a EDA apontou como mais associadas ao alvo, e o nome de
# cada uma no contrato. `FAIXA_ATRASO` nao esta na allowlist do Feature Set V1:
# ela e a discretizacao de `ESTATISTICA_ATRASOSAIDA` (secao 4.2 da
# documentacao), e a forma continua e que entra no modelo. Compara-la pelo nome
# original faria o ranking dizer que ela "sumiu", quando o modelo so a recebe
# sem discretizar.
FEATURES_EDA = {
    "ATRASO_CHEGADA": "ATRASO_CHEGADA",
    "FAIXA_ATRASO": "ESTATISTICA_ATRASOSAIDA",
    "N_TRECHOS": "N_TRECHOS",
}

# Artefato versionado. JSON, e nao CSV, pelo mesmo motivo de
# `busca_random_forest`: o `.gitignore` proibe `*.csv` por compromisso com o
# parceiro. O arquivo so tem nomes de feature e quedas agregadas.
ARQUIVO_IMPORTANCIA = _RAIZ / "assets" / "importancia_permutacao.json"

COLUNAS_TABELA = ("queda_media", "queda_desvio", "posicao")


def escolher_melhor_ensemble(
    metricas_por_modelo: dict[str, dict | None],
    metrica: str = METRICA_ESCOLHA,
) -> dict[str, object]:
    """Escolhe o ensemble de maior `metrica` entre os dicionarios de `avaliar`.

    `metricas_por_modelo` mapeia o nome do ensemble ao dicionario que `avaliar`
    devolveu para ele, ou a `None` quando aquele ensemble ainda nao tem numero
    medido. Um modelo sem numero ou com `nan` na metrica fica fora da disputa e
    aparece em `ausentes`: `nan` e o que `avaliar` devolve para um lote sem
    Detrator, e compara-lo com um numero valido daria um vencedor sem
    significado.

    `comparacao_completa` so e verdadeiro se todos os ensembles entraram na
    disputa. Com um so disponivel, a funcao devolve esse um, e o notebook
    registra que a escolha ainda nao comparou os dois, em vez de escrever que ele
    "venceu".

    Empate exato e decidido pela ordem do dicionario e sinalizado em `empate`,
    para o texto nao apresentar como vitoria o que foi desempate.
    """
    valores: dict[str, float] = {}
    ausentes: list[str] = []
    for nome, metricas in metricas_por_modelo.items():
        valor = None if metricas is None else metricas.get(metrica)
        if valor is None or (isinstance(valor, float) and math.isnan(valor)):
            ausentes.append(nome)
        else:
            valores[nome] = float(valor)

    if not valores:
        raise ValueError(
            f"Nenhum ensemble tem {metrica} medido por avaliar(); "
            f"sem numero: {ausentes}."
        )

    melhor_valor = max(valores.values())
    empatados = [nome for nome, valor in valores.items() if valor == melhor_valor]
    return {
        "vencedor": empatados[0],
        "metrica": metrica,
        "valores": valores,
        "ausentes": ausentes,
        "comparacao_completa": not ausentes,
        "empate": len(empatados) > 1,
    }


def cortes_do_preparo(preparo: dict[str, object]) -> dict[str, str]:
    """As duas datas de corte com que `preparar_matriz` montou as particoes.

    Sao elas que dizem de que validacao um numero saiu. Dois ensembles medidos
    sobre matrizes com cortes diferentes nao disputam a mesma prova, e a
    validacao de um pode cair dentro do treino do outro.
    """
    metadados = preparo["metadados"]
    return {
        "corte_validacao": str(metadados["corte_validacao"]),
        "corte_teste": str(metadados["corte_teste"]),
    }


def medir_ensembles(
    pipelines: dict[str, object | None],
    preparo: dict[str, object],
    avaliar,
    particao: str = PARTICAO_AVALIACAO,
) -> dict[str, object]:
    """Ajusta cada ensemble no treino de `preparo` e mede com `avaliar` na `particao`.

    **A trava que justifica a funcao: todos os ensembles passam pela mesma
    matriz.** A escolha do melhor ensemble so compara F2 que sairam da mesma
    validacao, e a importancia que vem depois so e valida se o vencedor foi
    ajustado no treino dessa mesma matriz. Receber as metricas prontas de cada
    secao do notebook abria espaco para um ensemble chegar medido sobre outro
    `preparo`, com outros cortes, sem erro nenhum. Aqui o ajuste e a medicao
    acontecem juntos, sobre um `preparo` so.

    Por isso cada pipeline precisa chegar **sem ajuste**, como devolvem
    `busca_random_forest.reconstruir_pipeline` e
    `ensembles.melhor_gradient_boosting`. Um pipeline ja ajustado e recusado: ele
    pode ter visto outro treino. Um ensemble sem pipeline (`None`, busca ainda
    nao executada) entra sem numero, e `escolher_melhor_ensemble` o deixa fora
    da disputa.

    Devolve `metricas` (o dicionario de `avaliar` por ensemble, ou `None`),
    `ajustados` (o pipeline ajustado por ensemble, ou `None`), a `particao` e os
    `cortes` do `preparo`.
    """
    if particao == "treino":
        raise ValueError(
            "Os ensembles nao podem ser medidos no treino: e nele que foram "
            f"ajustados. Use '{PARTICAO_AVALIACAO}'."
        )
    if particao not in split.PARTICOES:
        raise ValueError(f"Particao '{particao}' fora do contrato: {split.PARTICOES}.")

    x_treino, y_treino = preparo["x"]["treino"], preparo["y"]["treino"]
    x_avaliacao, y_avaliacao = preparo["x"][particao], preparo["y"][particao]

    metricas: dict[str, dict | None] = {}
    ajustados: dict[str, object | None] = {}
    for nome, pipeline in pipelines.items():
        if pipeline is None:
            metricas[nome], ajustados[nome] = None, None
            continue
        try:
            check_is_fitted(pipeline)
        except NotFittedError:
            pass
        else:
            raise ValueError(
                f"O pipeline de '{nome}' chegou ajustado. Passe o pipeline remontado "
                "pelo JSON e sem ajuste: um ajuste feito fora daqui pode ter usado "
                "outro treino, e a comparacao deixaria de ser na mesma matriz."
            )
        pipeline.fit(x_treino, y_treino)
        metricas[nome] = avaliar(
            y_avaliacao, pipeline.predict(x_avaliacao), pipeline.predict_proba(x_avaliacao)[:, 1]
        )
        ajustados[nome] = pipeline

    return {
        "metricas": metricas,
        "ajustados": ajustados,
        "particao": particao,
        "cortes": cortes_do_preparo(preparo),
    }


def _conferir_entrada(pipeline, x_avaliacao) -> None:
    """Recusa as entradas que devolveriam um ranking valido e errado."""
    try:
        check_is_fitted(pipeline)
    except NotFittedError as erro:
        raise NotFittedError(
            "O pipeline precisa chegar ajustado no treino: a importancia mede o "
            "modelo que foi avaliado, nao um reajuste feito aqui."
        ) from erro

    if not isinstance(x_avaliacao, pd.DataFrame):
        raise TypeError(
            "x_avaliacao precisa ser o DataFrame cru do contrato "
            "(preparo['x'][particao]). Uma matriz ja transformada espalharia cada "
            "categorica em varias colunas one-hot no ranking."
        )

    esperadas = getattr(pipeline, "feature_names_in_", None)
    if esperadas is not None and list(x_avaliacao.columns) != list(esperadas):
        raise ValueError(
            "As colunas de x_avaliacao nao sao as features com que o pipeline foi "
            f"ajustado. Esperadas: {list(esperadas)}; recebidas: {list(x_avaliacao.columns)}."
        )

    proibidas = [c for c in x_avaliacao.columns if str(c).startswith(PREFIXOS_PROIBIDOS)]
    if proibidas:
        raise ValueError(
            f"Features da propria pesquisa de NPS na matriz: {proibidas}. "
            "Elas nao existem no momento da predicao e nao podem entrar no ranking."
        )


def calcular_importancia(
    pipeline,
    x_avaliacao: pd.DataFrame,
    y_avaliacao,
    scoring,
    n_repeats: int = N_REPETICOES,
    random_state: int = SEMENTE_PADRAO,
    n_jobs: int | None = 1,
) -> pd.DataFrame:
    """Queda media e desvio da metrica ao embaralhar cada feature original.

    `pipeline` e o pipeline inteiro, pre-processador do contrato mais modelo, ja
    ajustado no treino. `x_avaliacao` e a matriz **crua** da particao, com as
    colunas do contrato: e isso que faz a importancia ser por feature original,
    como a docstring do modulo explica.

    `scoring` e obrigatorio: e o `scorer_f2` do #242, o mesmo que a busca
    otimizou. `n_repeats` e `random_state` ficam fixos pelo mesmo motivo da
    busca: com eles, duas execucoes sobre o mesmo modelo e a mesma particao
    devolvem a mesma tabela, numero a numero.

    Devolve uma linha por feature, indexada pelo nome, com `queda_media`,
    `queda_desvio` e `posicao` (1 e a mais influente), ordenada pela queda. Um
    empate na queda media e desfeito pelo nome, para a ordem nao depender da
    ordem das colunas.

    `n_jobs` fica em 1 por padrao pelo mesmo motivo de `ensembles`: a semente
    de cada embaralhamento nao depende do paralelismo, mas manter o calculo num
    processo so evita duplicar na memoria da sessao uma floresta de centenas de
    arvores por processo.
    """
    if scoring is None:
        raise ValueError(
            "scoring e obrigatorio: use o scorer_f2 do #242, o mesmo da busca."
        )
    if n_repeats < 2:
        raise ValueError(
            f"n_repeats={n_repeats}: com menos de duas repeticoes nao ha desvio "
            "padrao, e o grafico do CR04 ficaria sem a barra de incerteza."
        )
    _conferir_entrada(pipeline, x_avaliacao)

    resultado = permutation_importance(
        pipeline,
        x_avaliacao,
        y_avaliacao,
        scoring=scoring,
        n_repeats=n_repeats,
        random_state=random_state,
        n_jobs=n_jobs,
    )
    tabela = pd.DataFrame(
        {
            "queda_media": resultado.importances_mean,
            "queda_desvio": resultado.importances_std,
        },
        index=pd.Index(list(x_avaliacao.columns), name="feature"),
    )
    tabela = (
        tabela.reset_index()
        .sort_values(["queda_media", "feature"], ascending=[False, True])
        .set_index("feature")
    )
    tabela["posicao"] = np.arange(1, len(tabela) + 1)
    return tabela


def importancia_no_contrato(
    pipeline,
    preparo: dict[str, object],
    scoring,
    particao: str = PARTICAO_AVALIACAO,
    **kwargs,
) -> pd.DataFrame:
    """`calcular_importancia` sobre uma particao do contrato, lida pelo nome.

    E a funcao que o notebook chama, e o nome da particao e o argumento que
    serve de evidencia do CR03. `"treino"` e recusado: e nele que o modelo foi
    ajustado, e ali uma feature memorizada parece importante. Qualquer nome fora
    de `split.PARTICOES` tambem e recusado, para um erro de digitacao nao virar
    `KeyError` longe daqui.
    """
    if particao == "treino":
        raise ValueError(
            "A importancia nao pode ser medida no treino: o modelo foi ajustado "
            "nele, e uma feature memorizada pareceria importante. Use "
            f"'{PARTICAO_AVALIACAO}'."
        )
    if particao not in split.PARTICOES:
        raise ValueError(f"Particao '{particao}' fora do contrato: {split.PARTICOES}.")
    return calcular_importancia(
        pipeline,
        preparo["x"][particao],
        preparo["y"][particao],
        scoring,
        **kwargs,
    )


def features_no_topo(tabela: pd.DataFrame, n: int = N_TOPO) -> list[str]:
    """Nomes das `n` features de maior queda, na ordem do ranking."""
    return list(tabela.sort_values("posicao").index[:n])


def comparar_com_eda(
    tabela: pd.DataFrame,
    esperadas: dict[str, str] = FEATURES_EDA,
    n: int = N_TOPO,
) -> pd.DataFrame:
    """Posicao no ranking de cada feature que a EDA apontou como mais associada.

    Uma linha por feature da EDA, com o nome no contrato (`FAIXA_ATRASO` vira
    `ESTATISTICA_ATRASOSAIDA`, pelo motivo de `FEATURES_EDA`), a posicao no
    ranking e se ela esta entre as `n` primeiras. Uma feature da EDA que nao
    esteja na matriz aparece com posicao vazia, e nao some da tabela: a ausencia
    tambem e um resultado a comentar.
    """
    linhas = []
    for nome_eda, nome_contrato in esperadas.items():
        posicao = tabela["posicao"].get(nome_contrato)
        linhas.append({
            "feature_eda": nome_eda,
            "feature_no_contrato": nome_contrato,
            "posicao": None if posicao is None else int(posicao),
            "no_topo": posicao is not None and int(posicao) <= n,
        })
    return pd.DataFrame(linhas).set_index("feature_eda")


def plotar_importancia(
    tabela: pd.DataFrame,
    titulo: str = "Permutation importance do melhor ensemble",
    rotulo_metrica: str = "F2",
    n_topo: int = N_TOPO,
    ax=None,
):
    """Barras horizontais com a queda media e o desvio padrao por feature (CR04).

    A mais influente fica no alto. As `n_topo` primeiras ganham cor propria,
    porque sao elas que seguem para o #192. A linha vertical no zero separa as
    features de que o modelo depende das que ele poderia perder: uma barra cujo
    desvio cruza o zero nao se distingue de ruido do embaralhamento.
    """
    ordenada = tabela.sort_values("posicao", ascending=False)
    if ax is None:
        _, ax = plt.subplots(figsize=(8, 0.45 * len(ordenada) + 1.5))
    cores = ["#2E5FA3" if p <= n_topo else "#9AA5B1" for p in ordenada["posicao"]]
    ax.barh(
        ordenada.index,
        ordenada["queda_media"],
        xerr=ordenada["queda_desvio"],
        color=cores,
        ecolor="#333333",
        capsize=3,
    )
    ax.axvline(0, color="#333333", linewidth=0.8)
    ax.set_xlabel(f"Queda media do {rotulo_metrica} ao embaralhar a feature (barra: desvio padrao)")
    ax.set_ylabel("")
    ax.set_title(titulo)
    return ax.figure


def salvar_ranking(
    tabela: pd.DataFrame,
    escolha: dict[str, object],
    scoring_nome: str,
    particao: str = PARTICAO_AVALIACAO,
    n_repeats: int = N_REPETICOES,
    random_state: int = SEMENTE_PADRAO,
    caminho=None,
    *,
    cortes: dict[str, str],
) -> Path:
    """Grava o ranking e a configuracao que o produziu em JSON.

    E o artefato que o #192 le para saber de quais tres features gerar a
    dependencia parcial. Carrega tambem o ensemble escolhido, a metrica de cada
    um, a particao, os `cortes` da matriz, `n_repeats`, `random_state` e o
    `scoring`: sem eles, o ranking nao diria de que modelo e de que medicao saiu.

    `cortes` e obrigatorio e vem de `cortes_do_preparo`: o nome `"validacao"`
    sozinho nao identifica a particao, porque duas matrizes com cortes
    diferentes tem, as duas, uma validacao. Quem le o JSON confere os cortes
    contra o proprio `preparo` antes de usar o ranking.

    Sem caminho explicito, o arquivo vai para `ARQUIVO_IMPORTANCIA`, lido na hora
    da chamada, pelo mesmo motivo de `busca_random_forest.salvar_resultados`.
    """
    faltando = {"corte_validacao", "corte_teste"} - set(cortes)
    if faltando:
        raise ValueError(f"cortes sem {sorted(faltando)}: use cortes_do_preparo(preparo).")
    caminho = Path(caminho or ARQUIVO_IMPORTANCIA)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    ordenada = tabela.sort_values("posicao")
    registro = {
        "ensemble": escolha["vencedor"],
        "metrica_escolha": escolha["metrica"],
        "metricas_por_ensemble": escolha["valores"],
        "ensembles_sem_numero": escolha["ausentes"],
        "comparacao_completa": escolha["comparacao_completa"],
        "scoring": scoring_nome,
        "particao": particao,
        "corte_validacao": str(cortes["corte_validacao"]),
        "corte_teste": str(cortes["corte_teste"]),
        "n_repeats": int(n_repeats),
        "random_state": int(random_state),
        "topo": features_no_topo(ordenada),
        "ranking": [
            {
                "feature": str(feature),
                "posicao": int(linha["posicao"]),
                "queda_media": float(linha["queda_media"]),
                "queda_desvio": float(linha["queda_desvio"]),
            }
            for feature, linha in ordenada.iterrows()
        ],
    }
    caminho.write_text(json.dumps(registro, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return caminho


def carregar_ranking(caminho=None) -> dict[str, object]:
    """Le o registro gravado por `salvar_ranking`, no mesmo caminho padrao dela."""
    return json.loads(Path(caminho or ARQUIVO_IMPORTANCIA).read_text(encoding="utf-8"))
