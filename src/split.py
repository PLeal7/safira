"""Particionamento temporal e por Cliente dos conjuntos de treino, validacao e teste.

O corte e temporal, e nao aleatorio, porque o Safira preve a detracao de um voo
que ainda vai acontecer a partir do que se sabe ate hoje. Embaralhar as linhas
colocaria voos de 2026 no treino e voos de 2024 no teste, e a metrica resultante
mediria uma tarefa que a operacao nunca enfrenta: prever o passado conhecendo o
futuro. A secao 4.2.1 reforca essa escolha ao documentar um efeito de periodo em
2024Q4, quando a detracao sobe acima do que a variacao de atrasos explica; com
divisao aleatoria esse periodo vazaria para os tres conjuntos e o modelo
pareceria melhor do que e.

O corte temporal sozinho, porem, nao basta. A hipotese 4 da secao 4.2.3 mostrou
que quem detratou uma vez volta a detratar com chance 4,75 vezes maior, e que
esse efeito persiste depois de controlado o voo. Um mesmo Cliente presente no
treino e no teste faria o modelo reconhecer a pessoa em vez de aprender o
fenomeno, e a metrica de teste ficaria otimista. Por isso a particao e tambem
por Cliente: cada `ID_GOLDENRECORD` pertence a um unico conjunto.

Este modulo generaliza para tres conjuntos a divisao de dois que existe em
`scripts/preprocessamento_nps.dividir_treino_teste_temporal_por_cliente`, que
atende ao pre-processamento mas nao a modelagem, e que levanta excecao na base
analitica por causa das linhas sem data tratadas aqui.

As datas de corte sao parametro, nunca constante deste modulo: elas pertencem ao
registro de decisao da politica de particionamento, e fixa-las aqui criaria uma
segunda fonte de verdade que poderia divergir da documentada.
"""

from __future__ import annotations

import pandas as pd

COLUNA_DATA = "DATA_STD"
COLUNA_CLIENTE = "ID_GOLDENRECORD"
# Identificador sequencial da resposta, usado como prova de ordem cronologica
# quando a data esta ausente: ver verificar_anterioridade_sem_data.
COLUNA_ORDEM = "RESPONDENT_ID"
PARTICOES = ("treino", "validacao", "teste")

# Destinos aceitos para as linhas sem data. Nao ha escolha implicita entre eles
# porque a decisao muda a base de treino e precisa ser deliberada: ver a
# docstring de dividir.
DESTINOS_SEM_DATA = ("excluir", "treino")


def _serie_data(df: pd.DataFrame, coluna_data: str) -> pd.Series:
    if coluna_data not in df.columns:
        raise KeyError(f"coluna de data ausente na base: {coluna_data!r}")
    return pd.to_datetime(df[coluna_data], errors="coerce")


def dividir(
    df: pd.DataFrame,
    corte_validacao: str,
    corte_teste: str,
    coluna_data: str = COLUNA_DATA,
    coluna_cliente: str = COLUNA_CLIENTE,
    sem_data: str = "excluir",
) -> tuple[dict[str, pd.DataFrame], dict[str, object]]:
    """Divide a base em treino, validacao e teste por data e por Cliente.

    Retorna as tres particoes e os metadados da divisao, que registram o que foi
    removido e por que. Os metadados existem para que a Secao 4.3 possa relatar a
    composicao sem recalcula-la, e para que a perda por recorrencia seja
    auditavel em vez de silenciosa.

    O intervalo de cada particao e fechado a esquerda e aberto a direita, de modo
    que uma linha datada exatamente em `corte_validacao` pertence a validacao e
    nao ao treino. Sem essa convencao explicita, o dia do corte cairia nos dois
    conjuntos ou em nenhum, conforme o operador de comparacao usado.

    **Regra de desempate por Cliente.** Quando o mesmo `ID_GOLDENRECORD` aparece
    em mais de um periodo, ele e mantido apenas no conjunto mais recente em que
    ocorre, e suas linhas anteriores sao descartadas. A direcao importa: preservar
    o conjunto mais recente mantem teste e validacao intactos, que sao os que
    medem o desempenho, e concentra a perda no treino, que e o mais abundante.

    **Linhas sem data.** Na base analitica sao 120.000, cerca de um quarto do
    total. Elas vem das fontes que nao trazem a coluna `DATA_STD`, e nao de datas
    corrompidas: `normalizar_data_std` levanta excecao diante de data invalida,
    entao o que sobra ausente e ausencia de origem.

    A anterioridade delas em relacao ao periodo datado **e verificavel**, ainda
    que a data nao exista, e `verificar_anterioridade_sem_data` a checa: o
    `RESPONDENT_ID` acompanha a ordem cronologica com correlacao de Spearman de
    0,9999 nas linhas datadas, e o maior ID sem data e menor que o menor ID
    datado. Os dois blocos nao se sobrepoem, de modo que as linhas sem data
    precedem 06/01/2024, a data mais antiga da base. A taxa de detracao mais
    baixa nesse bloco, 16,5% contra 21,8%, e coerente com isso, porque a secao
    4.2.1 documenta detracao crescente ao longo do periodo.

    Por isso 'treino' e o destino adequado: sao as observacoes mais antigas
    disponiveis, exatamente o lugar de dados de treino, e descarta-las jogaria
    fora um quarto da base sem ganho de rigor. 'excluir' permanece disponivel
    para o caso de a verificacao de anterioridade falhar em uma base futura.

    Nunca sao enviadas para validacao ou teste: la a data e necessaria para
    situar cada linha dentro do periodo avaliado, e nao apenas antes dele.

    **Linhas sem Cliente.** Sao excluidas dos tres conjuntos. O nulo impede saber
    se duas dessas linhas sao da mesma pessoa, e trata-las como Clientes
    distintos reintroduziria o vazamento que a divisao por grupo evita.
    """
    if sem_data not in DESTINOS_SEM_DATA:
        raise ValueError(
            f"sem_data deve ser um de {DESTINOS_SEM_DATA}, recebido {sem_data!r}"
        )
    if coluna_cliente not in df.columns:
        raise KeyError(f"coluna de Cliente ausente na base: {coluna_cliente!r}")

    limite_validacao = pd.Timestamp(corte_validacao)
    limite_teste = pd.Timestamp(corte_teste)
    if not limite_validacao < limite_teste:
        raise ValueError(
            "corte_validacao deve ser anterior a corte_teste: "
            f"{limite_validacao.date()} nao e anterior a {limite_teste.date()}"
        )

    data = _serie_data(df, coluna_data)
    cliente = df[coluna_cliente]
    tem_cliente = cliente.notna()
    datada = data.notna()

    base = df[tem_cliente]
    data_base, cliente_base = data[tem_cliente], cliente[tem_cliente]
    datada_base = data_base.notna()

    mascaras = {
        "treino": datada_base & (data_base < limite_validacao),
        "validacao": datada_base & (data_base >= limite_validacao) & (data_base < limite_teste),
        "teste": datada_base & (data_base >= limite_teste),
    }
    if sem_data == "treino":
        mascaras["treino"] = mascaras["treino"] | ~datada_base

    # Desempate por Cliente, do conjunto mais recente para o mais antigo: quem
    # esta no teste sai da validacao e do treino; quem sobra na validacao sai do
    # treino. A ordem garante que teste e validacao fiquem intactos.
    clientes_teste = set(cliente_base[mascaras["teste"]])
    mascaras["validacao"] &= ~cliente_base.isin(clientes_teste)
    mascaras["treino"] &= ~cliente_base.isin(clientes_teste)

    clientes_validacao = set(cliente_base[mascaras["validacao"]])
    perdidas_treino = int((mascaras["treino"] & cliente_base.isin(clientes_validacao)).sum())
    mascaras["treino"] &= ~cliente_base.isin(clientes_validacao)

    particoes = {nome: base[m] for nome, m in mascaras.items()}

    # As linhas que sobram fora das particoes tem duas causas distintas, e
    # somá-las num numero so esconderia qual delas pesa: as sem data, quando a
    # politica e 'excluir', e as descartadas por o Cliente aparecer num conjunto
    # mais recente. A segunda e obtida por diferenca depois de isolar a primeira.
    fora = len(base) - sum(len(p) for p in particoes.values())
    sem_data_excluidas = int((~datada_base).sum()) if sem_data == "excluir" else 0

    metadados = {
        "corte_validacao": str(limite_validacao.date()),
        "corte_teste": str(limite_teste.date()),
        "politica_sem_data": sem_data,
        "linhas_sem_cliente_excluidas": int((~tem_cliente).sum()),
        "linhas_sem_data": int((~datada).sum()),
        "linhas_sem_data_excluidas": sem_data_excluidas,
        "linhas_removidas_por_recorrencia": int(fora - sem_data_excluidas),
        "linhas_removidas_do_treino_por_validacao": perdidas_treino,
        "clientes_treino": int(particoes["treino"][coluna_cliente].nunique()),
        "clientes_validacao": int(particoes["validacao"][coluna_cliente].nunique()),
        "clientes_teste": int(particoes["teste"][coluna_cliente].nunique()),
    }
    return particoes, metadados


def verificar_anterioridade_sem_data(
    df: pd.DataFrame,
    coluna_data: str = COLUNA_DATA,
    coluna_ordem: str = COLUNA_ORDEM,
    correlacao_minima: float = 0.99,
) -> dict[str, object]:
    """Verifica que as linhas sem data precedem as datadas, pela ordem de registro.

    Enviar as linhas sem data para o treino so e defensavel se elas forem
    anteriores ao periodo datado. Sem a data, a evidencia vem do identificador de
    resposta, que e atribuido sequencialmente: se ele acompanha a cronologia nas
    linhas datadas, e se todo identificador sem data e menor que o menor
    identificador datado, entao o bloco sem data precede o datado.

    Levanta `AssertionError` quando qualquer uma das duas condicoes falha, para
    que uma base futura com outro padrao de ausencia nao herde silenciosamente
    uma conclusao que valia para esta.
    """
    if coluna_ordem not in df.columns:
        raise KeyError(f"coluna de ordem ausente na base: {coluna_ordem!r}")

    data = _serie_data(df, coluna_data)
    datada = data.notna()
    if not (~datada).any():
        return {"linhas_sem_data": 0, "verificacao": "nao aplicavel"}

    correlacao = (
        df.loc[datada, coluna_ordem]
        .corr(data[datada].astype("int64"), method="spearman")
    )
    assert correlacao >= correlacao_minima, (
        f"{coluna_ordem} nao acompanha a cronologia: correlacao de Spearman "
        f"{correlacao:.4f}, abaixo do minimo {correlacao_minima}. Sem essa "
        "monotonicidade nao se pode afirmar que as linhas sem data sao anteriores"
    )

    maior_sem_data = df.loc[~datada, coluna_ordem].max()
    menor_datada = df.loc[datada, coluna_ordem].min()
    assert maior_sem_data < menor_datada, (
        f"os blocos se sobrepoem: o maior {coluna_ordem} sem data "
        f"({maior_sem_data}) nao e menor que o menor datado ({menor_datada}), "
        "entao as linhas sem data nao sao todas anteriores ao periodo datado"
    )

    return {
        "linhas_sem_data": int((~datada).sum()),
        "correlacao_spearman": round(float(correlacao), 4),
        "maior_id_sem_data": int(maior_sem_data),
        "menor_id_datado": int(menor_datada),
        "data_mais_antiga": str(data[datada].min().date()),
    }


def conferir(
    particoes: dict[str, pd.DataFrame],
    total_esperado: int | None = None,
    coluna_data: str = COLUNA_DATA,
    coluna_cliente: str = COLUNA_CLIENTE,
) -> None:
    """Verifica por assercao que a divisao e valida.

    As quatro conferencias cobrem falhas que passam despercebidas em inspecao
    visual: linha em duas particoes, linha em nenhuma, datas fora de ordem e
    Cliente presente em mais de um conjunto. Esta ultima e a que um olhar
    distraido mais deixa passar, porque o corte por data parece resolve-la e nao
    resolve: Clientes recorrentes viajam em periodos diferentes.
    """
    indices = {nome: set(p.index) for nome, p in particoes.items()}

    for a, b in (("treino", "validacao"), ("treino", "teste"), ("validacao", "teste")):
        comum = indices[a] & indices[b]
        assert not comum, (
            f"{len(comum)} registro(s) em {a} e {b} ao mesmo tempo; "
            "a intersecao entre particoes deve ser vazia"
        )
        clientes_a = set(particoes[a][coluna_cliente].dropna())
        clientes_b = set(particoes[b][coluna_cliente].dropna())
        compartilhados = clientes_a & clientes_b
        assert not compartilhados, (
            f"{len(compartilhados)} Cliente(s) presentes em {a} e {b}; "
            "a divisao por grupo impede que o mesmo Cliente apareca nos dois"
        )

    if total_esperado is not None:
        soma = sum(len(p) for p in particoes.values())
        assert soma == total_esperado, (
            f"a uniao das particoes tem {soma} registros e o total esperado e "
            f"{total_esperado}: {abs(total_esperado - soma)} registro(s) "
            "ficaram fora da divisao"
        )

    # A ordem e verificada sobre as datas reais, e nao sobre os parametros de
    # corte: se o filtro estiver errado, o parametro continuaria coerente.
    maximos, minimos = {}, {}
    for nome, p in particoes.items():
        d = _serie_data(p, coluna_data).dropna()
        if not d.empty:
            maximos[nome], minimos[nome] = d.max(), d.min()

    for anterior, posterior in (("treino", "validacao"), ("validacao", "teste")):
        if anterior in maximos and posterior in minimos:
            assert maximos[anterior] < minimos[posterior], (
                f"a maior data de {anterior} ({maximos[anterior].date()}) nao e "
                f"anterior a menor data de {posterior} "
                f"({minimos[posterior].date()}): ha sobreposicao temporal"
            )


def resumo(
    particoes: dict[str, pd.DataFrame],
    coluna_data: str = COLUNA_DATA,
    coluna_cliente: str = COLUNA_CLIENTE,
    alvo: str | None = "DETRATOR",
) -> pd.DataFrame:
    """Tabela com n, intervalo de datas, Clientes e taxa do alvo por particao.

    A taxa do alvo entra ao lado do tamanho porque um corte temporal pode
    produzir particoes de tamanho correto e prevalencia muito diferente, e e essa
    diferenca, e nao o tamanho, que compromete a leitura das metricas.
    """
    total = sum(len(p) for p in particoes.values())
    linhas = []
    for nome in PARTICOES:
        p = particoes[nome]
        d = _serie_data(p, coluna_data).dropna()
        linha = {
            "particao": nome,
            "n": len(p),
            "pct_do_total": round(len(p) / total * 100, 1) if total else 0.0,
            "clientes": int(p[coluna_cliente].nunique()) if len(p) else 0,
            "data_inicio": d.min().date() if not d.empty else None,
            "data_fim": d.max().date() if not d.empty else None,
            "sem_data": int(len(p) - len(d)),
        }
        if alvo and alvo in p.columns and len(p):
            linha["taxa_alvo_pct"] = round(p[alvo].mean() * 100, 2)
        linhas.append(linha)
    return pd.DataFrame(linhas).set_index("particao")
