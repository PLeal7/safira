"""Testes do particionamento temporal e por Cliente da seção 4.3.

O que interessa aqui não é confirmar que a divisão funciona quando tudo está
certo, e sim que ela **recusa** o que comprometeria a métrica de teste: Cliente
presente em dois conjuntos, sobreposição temporal, linha em nenhuma partição e
escolha implícita sobre as linhas sem data. Cada teste abaixo corresponde a uma
forma concreta de o número final ficar otimista sem ninguém perceber.

Todos usam dados sintéticos, sem tocar nas bases da Azul.

Executar com:  pytest tests/test_split.py -v
"""
import pandas as pd
import pytest

from split import (conferir, dividir, resumo,
                   verificar_anterioridade_sem_data)


@pytest.fixture
def base():
    """Seis respostas de quatro Clientes, cobrindo os três períodos.

    O Cliente 10 aparece no treino e no teste, e o 20 no treino e na validação:
    são eles que exercitam a regra de desempate por recorrência.
    """
    return pd.DataFrame({
        "RESPONDENT_ID": [1, 2, 3, 4, 5, 6],
        "ID_GOLDENRECORD": [10, 10, 20, 20, 30, 40],
        "DATA_STD": ["2024-03-01", "2026-02-01", "2024-05-01",
                     "2025-09-01", "2024-07-01", "2026-03-01"],
        "DETRATOR": [1, 0, 1, 0, 1, 0],
    })


CORTES = {"corte_validacao": "2025-07-01", "corte_teste": "2026-01-01"}


# ------------------------------------------------------- desempate por Cliente

def test_cliente_do_teste_nao_permanece_no_treino(base):
    particoes, _ = dividir(base, **CORTES)
    assert 10 not in set(particoes["treino"]["ID_GOLDENRECORD"])
    assert 10 in set(particoes["teste"]["ID_GOLDENRECORD"])


def test_cliente_da_validacao_nao_permanece_no_treino(base):
    particoes, _ = dividir(base, **CORTES)
    assert 20 not in set(particoes["treino"]["ID_GOLDENRECORD"])
    assert 20 in set(particoes["validacao"]["ID_GOLDENRECORD"])


def test_perda_por_recorrencia_e_contabilizada(base):
    """A remoção precisa aparecer nos metadados, não sumir da contagem."""
    _, meta = dividir(base, **CORTES)
    assert meta["linhas_removidas_por_recorrencia"] == 2
    assert meta["linhas_removidas_do_treino_por_validacao"] == 1


def test_conferir_dispara_com_cliente_em_dois_conjuntos(base):
    particoes, _ = dividir(base, **CORTES)
    # Devolve ao treino a linha do Cliente que está no teste, que é exatamente o
    # vazamento que a divisão por grupo existe para impedir.
    particoes["treino"] = pd.concat([particoes["treino"], base.loc[[0]]])
    with pytest.raises(AssertionError, match="Cliente"):
        conferir(particoes)


# ------------------------------------------------------------- ordem temporal

def test_conferir_dispara_com_sobreposicao_temporal(base):
    """Uma data do período de treino aparecendo na validação precisa falhar.

    A linha injetada tem índice e Cliente novos, para que a asserção de
    interseção e a de Cliente compartilhado não disparem antes e mascarem o que
    este teste verifica.
    """
    particoes, _ = dividir(base, **CORTES)
    intrusa = pd.DataFrame(
        {"RESPONDENT_ID": [99], "ID_GOLDENRECORD": [990],
         "DATA_STD": ["2024-02-01"], "DETRATOR": [1]},
        index=[99],
    )
    particoes["validacao"] = pd.concat([particoes["validacao"], intrusa])
    with pytest.raises(AssertionError, match="sobreposicao temporal"):
        conferir(particoes)


def test_intervalos_sao_fechados_a_esquerda(base):
    """A linha datada no dia do corte pertence ao conjunto que começa nele."""
    no_corte = pd.DataFrame({
        "RESPONDENT_ID": [7], "ID_GOLDENRECORD": [70],
        "DATA_STD": ["2025-07-01"], "DETRATOR": [1],
    })
    particoes, _ = dividir(pd.concat([base, no_corte], ignore_index=True), **CORTES)
    assert 70 in set(particoes["validacao"]["ID_GOLDENRECORD"])
    assert 70 not in set(particoes["treino"]["ID_GOLDENRECORD"])


# ----------------------------------------------------------- linhas sem dados

def test_linha_sem_data_nunca_vai_para_validacao_ou_teste(base):
    sem_data = pd.DataFrame({
        "RESPONDENT_ID": [8], "ID_GOLDENRECORD": [80],
        "DATA_STD": [None], "DETRATOR": [1],
    })
    df = pd.concat([base, sem_data], ignore_index=True)
    for politica in ("excluir", "treino"):
        particoes, _ = dividir(df, **CORTES, sem_data=politica)
        assert 80 not in set(particoes["validacao"]["ID_GOLDENRECORD"])
        assert 80 not in set(particoes["teste"]["ID_GOLDENRECORD"])


def test_politica_sem_data_muda_o_destino_da_linha(base):
    sem_data = pd.DataFrame({
        "RESPONDENT_ID": [8], "ID_GOLDENRECORD": [80],
        "DATA_STD": [None], "DETRATOR": [1],
    })
    df = pd.concat([base, sem_data], ignore_index=True)
    excluida, _ = dividir(df, **CORTES, sem_data="excluir")
    mantida, _ = dividir(df, **CORTES, sem_data="treino")
    assert 80 not in set(excluida["treino"]["ID_GOLDENRECORD"])
    assert 80 in set(mantida["treino"]["ID_GOLDENRECORD"])


def test_recusa_politica_sem_data_desconhecida(base):
    """Não existe escolha implícita: um valor não previsto precisa falhar."""
    with pytest.raises(ValueError, match="sem_data"):
        dividir(base, **CORTES, sem_data="imputar")


def test_linha_sem_cliente_fica_fora_dos_tres_conjuntos(base):
    sem_cliente = pd.DataFrame({
        "RESPONDENT_ID": [9], "ID_GOLDENRECORD": [None],
        "DATA_STD": ["2024-04-01"], "DETRATOR": [1],
    })
    df = pd.concat([base, sem_cliente], ignore_index=True)
    particoes, meta = dividir(df, **CORTES)
    assert meta["linhas_sem_cliente_excluidas"] == 1
    assert 9 not in set(pd.concat(particoes.values())["RESPONDENT_ID"])


# -------------------------------------------- anterioridade das linhas sem data

def _com_sem_data(ids_sem_data):
    """Base em que RESPONDENT_ID acompanha a cronologia, com linhas sem data."""
    datadas = pd.DataFrame({
        "RESPONDENT_ID": [100, 200, 300, 400],
        "ID_GOLDENRECORD": [10, 20, 30, 40],
        "DATA_STD": ["2024-03-01", "2024-06-01", "2025-09-01", "2026-02-01"],
        "DETRATOR": [1, 0, 1, 0],
    })
    sem = pd.DataFrame({
        "RESPONDENT_ID": ids_sem_data,
        "ID_GOLDENRECORD": [50 + i for i in range(len(ids_sem_data))],
        "DATA_STD": [None] * len(ids_sem_data),
        "DETRATOR": [1] * len(ids_sem_data),
    })
    return pd.concat([sem, datadas], ignore_index=True)


def test_anterioridade_confirmada_quando_ids_precedem_as_datadas():
    resultado = verificar_anterioridade_sem_data(_com_sem_data([10, 20]))
    assert resultado["linhas_sem_data"] == 2
    assert resultado["maior_id_sem_data"] < resultado["menor_id_datado"]


def test_anterioridade_dispara_quando_os_blocos_se_sobrepoem():
    """Um ID sem data acima do menor datado invalida a conclusão de anterioridade."""
    with pytest.raises(AssertionError, match="sobrepoem"):
        verificar_anterioridade_sem_data(_com_sem_data([10, 250]))


def test_anterioridade_dispara_quando_o_id_nao_acompanha_a_cronologia():
    df = _com_sem_data([10, 20])
    # Inverte a ordem dos identificadores entre as linhas datadas, quebrando a
    # monotonicidade que sustenta o argumento.
    datadas = df["DATA_STD"].notna()
    df.loc[datadas, "RESPONDENT_ID"] = [400, 300, 200, 100]
    with pytest.raises(AssertionError, match="cronologia"):
        verificar_anterioridade_sem_data(df)


def test_anterioridade_e_dispensavel_quando_nao_ha_linha_sem_data(base):
    assert verificar_anterioridade_sem_data(base)["linhas_sem_data"] == 0


# ------------------------------------------------------------- parametros e contrato

def test_recusa_cortes_fora_de_ordem(base):
    with pytest.raises(ValueError, match="anterior"):
        dividir(base, corte_validacao="2026-01-01", corte_teste="2025-07-01")


def test_recusa_base_sem_coluna_de_data(base):
    with pytest.raises(KeyError, match="data"):
        dividir(base.drop(columns=["DATA_STD"]), **CORTES)


def test_recusa_base_sem_coluna_de_cliente(base):
    with pytest.raises(KeyError, match="Cliente"):
        dividir(base.drop(columns=["ID_GOLDENRECORD"]), **CORTES)


def test_conferir_dispara_quando_falta_registro(base):
    particoes, _ = dividir(base, **CORTES)
    with pytest.raises(AssertionError, match="ficaram fora"):
        conferir(particoes, total_esperado=len(base) + 1)


def test_resumo_traz_n_intervalo_e_taxa_do_alvo(base):
    particoes, _ = dividir(base, **CORTES)
    tabela = resumo(particoes)
    assert list(tabela.index) == ["treino", "validacao", "teste"]
    for coluna in ("n", "pct_do_total", "clientes", "data_inicio", "data_fim", "taxa_alvo_pct"):
        assert coluna in tabela.columns
