"""Travas do treinamento do Extra Trees no notebook integrado.

O notebook e' a unidade executavel desta entrega. Estes testes leem sua fonte sem
executar dados do parceiro e impedem que uma alteracao posterior ajuste o candidato
na validacao ou no teste.
"""

import json
from pathlib import Path


NOTEBOOK = Path(__file__).resolve().parents[1] / "notebooks" / "comparacao_modelos.ipynb"


def _codigo_da_secao_extra_trees() -> str:
    notebook = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    for celula in notebook["cells"]:
        codigo = "".join(celula.get("source", []))
        if "modelo_extra_trees = ExtraTreesClassifier(" in codigo:
            return codigo
    raise AssertionError("a secao de treinamento do Extra Trees nao foi encontrada")


def test_extra_trees_tem_configuracao_reproduzivel_e_balanceada():
    codigo = _codigo_da_secao_extra_trees()

    for trecho in (
        "n_estimators=300",
        'max_features="sqrt"',
        "min_samples_leaf=5",
        'class_weight="balanced"',
        "random_state=42",
        "n_jobs=-1",
    ):
        assert trecho in codigo


def test_extra_trees_e_ajustado_somente_no_treino_e_registrado():
    codigo = _codigo_da_secao_extra_trees()

    assert "modelo_extra_trees.fit(X_treino, y_treino)" in codigo
    assert 'modelos["Extra Trees"] = modelo_extra_trees' in codigo
    assert "X_validacao" not in codigo
    assert "X_teste" not in codigo
