"""Testes dos espacos de busca do Random Forest e do Gradient Boosting (#186).

O risco aqui nao e o intervalo estar mal escolhido, que e leitura do markdown:
e uma amostra sorteada do espaco chegar ao estimador e ele recusar, o que so
apareceria no meio de uma `RandomizedSearchCV` de dezenas de minutos em vez de
num teste de segundos. CR02 pede pelo menos 40 combinacoes por espaco com
semente fixa, e ele entra aqui como parametrizacao sobre `ESTIMADOR_POR_ESPACO`
para que um quarto espaco, se `#185` decidir manter as duas bibliotecas por
mais tempo, ganhe cobertura sem precisar de um teste novo.

Executar com:  pytest tests/test_ensembles.py -v
"""
from __future__ import annotations

import pytest
from sklearn.model_selection import ParameterSampler

from ensembles import (ESPACO_GRADIENT_BOOSTING_HISTGB,
                        ESPACO_GRADIENT_BOOSTING_XGBOOST,
                        ESPACO_RANDOM_FOREST, ESPACOS_GRADIENT_BOOSTING,
                        ESTIMADOR_POR_ESPACO, RAZAO_DESBALANCEAMENTO,
                        SEMENTE_PADRAO)

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
