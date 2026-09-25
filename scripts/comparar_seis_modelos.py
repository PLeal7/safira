"""Reproduz localmente a avaliação dos seis modelos, sem versionar outputs.

Execute da raiz com `.venv/bin/python scripts/comparar_seis_modelos.py`.
O parquet deve existir em data/processed/base_analitica.parquet; a saída agregada
fica em out/comparacao_seis_modelos.json, diretório ignorado pelo Git.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import ExtraTreesClassifier
from sklearn.model_selection import cross_val_score
from sklearn.pipeline import Pipeline

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))

from avaliacao import avaliar  # noqa: E402
from ensembles import criar_pipeline_random_forest, melhor_gradient_boosting  # noqa: E402
from matriz import preparar_matriz  # noqa: E402
from modelo import limiar_por_capacidade  # noqa: E402
from pipeline_arvore import criar_pipeline as criar_arvore  # noqa: E402
from pipeline_logistica import criar_pipeline as criar_logistica  # noqa: E402
from scorer_f2 import scorer_f2  # noqa: E402
from validacao import criar_folds  # noqa: E402

PARQUET = RAIZ / "data/processed/base_analitica.parquet"
SAIDA = RAIZ / "out/comparacao_seis_modelos.json"
CAPACIDADE = 9050


def executar(parquet: Path = PARQUET, saida: Path = SAIDA) -> dict:
    """Ajusta no treino, mede validação/teste e calcula CV dos dois não tunados.

    O F2 de CV usa predict() nos folds agrupados; o F2 operacional usa o
    limiar da fila. O teste nunca participa da escolha de hiperparâmetros.
    """
    preparo = preparar_matriz(pd.read_parquet(parquet), "2025-07-01", "2026-01-01")
    prep = preparo["preprocessador"]
    log = json.loads((RAIZ / "assets/hiperparametros_logistica.json").read_text())[0]
    arvore = json.loads((RAIZ / "src/hiperparametros_arvore.json").read_text())
    boosting = json.loads((RAIZ / "assets/hiperparametros_gradient_boosting.json").read_text())

    extra = ExtraTreesClassifier(
        n_estimators=300, max_features="sqrt", min_samples_leaf=5,
        class_weight="balanced", random_state=42, n_jobs=1,
    )
    modelos = {
        "classe majoritária": (DummyClassifier(strategy="most_frequent"), "matrizes", None),
        "regressão logística tunada": (
            criar_logistica(prep, max_iter=log["max_iter"], C=log["C"],
                            class_weight=log["class_weight"], solver=log["solver"],
                            l1_ratio=log["l1_ratio"]), "x", log["f2"],
        ),
        "árvore de decisão tunada": (
            criar_arvore(prep, **arvore["hiperparametros"]), "x",
            arvore["f2_validacao_cruzada"],
        ),
        "gradient boosting tunado": (
            melhor_gradient_boosting(prep), "x", boosting["melhor_score_medio"],
        ),
        "random forest padrão (sem busca)": (
            criar_pipeline_random_forest(prep), "x", None,
        ),
        "extra trees inicial (sem busca)": (extra, "matrizes", None),
    }

    resultado = {
        "split": {p: len(preparo["y"][p]) for p in ("treino", "validacao", "teste")},
        "capacidade": CAPACIDADE,
        "modelos": {},
    }
    # A preparação de cada Pipeline é clonada, para que os folds ajustem
    # imputer/scaler/encoder apenas nas linhas de treino de cada fold.
    folds = criar_folds(preparo["x"]["treino"], preparo["grupos"]["treino"])
    for nome, (estimador, matriz, f2_cv) in modelos.items():
        inicio = time.monotonic()
        if f2_cv is None and nome.startswith("random forest"):
            f2_cv = float(np.mean(cross_val_score(
                estimador, preparo["x"]["treino"], preparo["y"]["treino"],
                scoring=scorer_f2, cv=folds, n_jobs=4,
            )))
        elif f2_cv is None and nome.startswith("extra trees"):
            pipeline_cv = Pipeline([("preparo", clone(prep)), ("modelo", clone(extra))])
            f2_cv = float(np.mean(cross_val_score(
                pipeline_cv, preparo["x"]["treino"], preparo["y"]["treino"],
                scoring=scorer_f2, cv=folds, n_jobs=4,
            )))

        estimador.fit(preparo[matriz]["treino"], preparo["y"]["treino"])
        registro = {"f2_cv_predict": f2_cv, "particoes": {}}
        for particao in ("validacao", "teste"):
            x = preparo[matriz][particao]
            y = preparo["y"][particao]
            scores = estimador.predict_proba(x)[:, 1]
            limiar = limiar_por_capacidade(scores, CAPACIDADE)
            rotulos = (scores >= limiar).astype(int)
            registro["particoes"][particao] = {
                "metricas_limiar_capacidade": avaliar(y, rotulos, scores),
                "f2_predict_padrao": avaliar(y, estimador.predict(x), scores)["F2"],
                "limiar": float(limiar),
                "fila": int(rotulos.sum()),
            }
        registro["tempo_total_s"] = round(time.monotonic() - inicio, 1)
        resultado["modelos"][nome] = registro
        # Checkpoint agregado local, inclusive se uma execução longa for interrompida.
        saida.parent.mkdir(parents=True, exist_ok=True)
        saida.write_text(json.dumps(resultado, ensure_ascii=False, indent=2) + "\n")
    return resultado


if __name__ == "__main__":
    executar()
