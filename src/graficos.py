"""
SAFIRA | Secao 4.2.1 - Geracao das figuras da exploracao de dados.

Divisao de responsabilidades entre as bibliotecas, deliberada e documentada na
secao 4.2.1: seaborn responde pela gramatica estatistica, pela camada de dados
e pelo tema (barplot, lineplot, heatmap, relplot, set_theme); matplotlib
responde pelo que o seaborn nao abstrai, isto e, eixos secundarios, anotacoes
posicionais, formatacao dos ticks e composicao de subplots com proporcoes
assimetricas.

Cada funcao recebe o DataFrame limpo e devolve a Figure, para que o grafico
apareca como saida de celula no notebook. A escrita em disco acontece apenas
quando o modulo e executado como script.
"""
from __future__ import annotations

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.ticker import FuncFormatter, MaxNLocator

from clean import faixa_antecedencia

# ------------------------------------------------------------------- constantes
PALETA_AZUL = ["#00A0DF", "#2E5FA3", "#E8871E", "#C0392B"]
AZ_ESC, AZ_CLA, CINZA, VERM, LARANJA = "#0A2A6B", "#00A0DF", "#9AA5B1", "#C0392B", "#E8871E"
# Familia extra, exclusiva do G1: separa visualmente o painel de vies do
# painel de detracao, sem reaproveitar cores ja associadas a outro
# significado no restante do documento.
ROXO_CLA, ROXO_ESC = "#9482B0", "#3D2C52"

ORD_ATRASO = ["a. Sem Atraso", "b. 15m - 60m", "c. 61m - 120m", "d. >120m"]
LAB_ATRASO = ["Sem atraso\n(<15 min)", "15 a 60 min", "61 a 120 min", "Acima de 120 min"]

TIERS = ["Sem cadastro", "Azul Fidelidade", "Topazio", "Safira", "Diamante"]

BINS_LIMIAR = [-1, 0, 5, 10, 15, 20, 30, 45, 60, 90, 120, 180, 240, 10_000]
LAB_LIMIAR = ["0", "1-5", "6-10", "11-15", "16-20", "21-30", "31-45", "46-60",
              "61-90", "91-120", "121-180", "181-240", ">240"]

# Acima deste incremento em pontos percentuais a curva de risco muda de regime.
# Usado para colorir as barras, tracar a linha de referencia e localizar a
# faixa de inflexao: um valor so, para os tres nao poderem divergir.
LIMIAR_MARGINAL = 4

OUT_DIR = os.environ.get("SAFIRA_OUT_DIR", "out/figuras")


def aplicar_tema() -> None:
    """Tema visual unico para todas as figuras, com a paleta institucional."""
    sns.set_theme(
        style="whitegrid", context="notebook", palette=PALETA_AZUL,
        rc={"grid.linestyle": "--", "grid.alpha": 0.25, "axes.edgecolor": "#333"},
    )
    plt.rcParams.update({
        "font.family": "DejaVu Sans",
        "axes.titleweight": "bold",
        "axes.spines.top": False,
        "axes.spines.right": False,
        "figure.dpi": 130,
        "savefig.bbox": "tight",
    })


def virgula(v: float, casas: int = 1, sufixo: str = "") -> str:
    """Formata numero com separador decimal em virgula, conforme a norma."""
    return f"{v:.{casas}f}".replace(".", ",") + sufixo


def _fmt(casas: int = 0, sufixo: str = "") -> FuncFormatter:
    """Formatador de eixo com virgula decimal, independente do locale."""
    return FuncFormatter(lambda v, _pos: virgula(v, casas, sufixo))


def rotulos(matriz, casas: int = 1):
    """Anotacoes de heatmap com virgula decimal, ja que o fmt do seaborn usa ponto."""
    return np.array([["" if pd.isna(v) else virgula(v, casas) for v in linha]
                     for linha in np.asarray(matriz)])


def _rodape(ax, texto: str, y: float = -0.20) -> None:
    ax.text(0, y, texto, transform=ax.transAxes, fontsize=8.5, color="#555")


aplicar_tema()


# ------------------------------------------- G1: atraso, detracao e vies de resposta
def _cabecalho_painel(ax, indice: str, titulo: str, subtitulo: str):
    """Regua preta e cabecalho numerado que abrem um painel do Grafico 1.

    Identifica cada painel como uma leitura distinta do mesmo fenomeno (a
    associacao com a detracao e o vies amostral) antes que o leitor chegue
    as barras. Devolve o texto do subtitulo para quem precisar medir sua
    largura e emendar um trecho adicional na mesma linha.
    """
    ax.plot([0, 1], [1.32, 1.32], transform=ax.transAxes, color="#111",
            lw=1.6, clip_on=False, solid_capstyle="butt")
    ax.text(0, 1.20, indice, transform=ax.transAxes, fontsize=9,
            color=CINZA, fontweight="bold", va="bottom")
    ax.text(0.055, 1.185, titulo, transform=ax.transAxes, fontsize=14,
            color="#111", fontweight="bold", va="bottom")
    return ax.text(0, 1.075, subtitulo, transform=ax.transAxes, fontsize=9.5,
                    color="#666", va="bottom")


def _barras_painel(ax, serie: pd.Series, rotulos_x: list[str], cor_base: str,
                    cor_destaque: str, casas_eixo: int, casas_rotulo: int,
                    sufixo: str) -> None:
    """Barras de uma faixa de atraso com a ultima faixa destacada.

    Usada pelos dois paineis do Grafico 1: mesma grade de categorias no eixo
    x, cores e formato de rotulo diferentes por painel, para a leitura lado
    a lado funcionar sem forcar as duas escalas no mesmo eixo.
    """
    dados = serie.reindex(ORD_ATRASO).reset_index()
    dados.columns = ["FAIXA_ATRASO", "VALOR"]
    cores = [cor_base] * (len(dados) - 1) + [cor_destaque]
    sns.barplot(data=dados, x="FAIXA_ATRASO", y="VALOR", order=ORD_ATRASO,
                hue="FAIXA_ATRASO", palette=cores, legend=False, width=0.6, ax=ax)

    ax.set_facecolor("#FAF9F6")
    ax.set(xlabel="", ylabel="")
    ax.margins(x=0.09)
    ax.grid(axis="y", color="#D8D5CF", lw=0.8, zorder=0)
    ax.grid(axis="x", visible=False)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.set_xticks(range(len(dados)))
    ax.set_xticklabels(rotulos_x, fontsize=10, color="#333")
    ax.tick_params(axis="y", labelsize=10, colors="#555", length=0)
    ax.tick_params(axis="x", length=0, pad=8)
    ax.get_xticklabels()[-1].set_fontweight("bold")
    ax.get_xticklabels()[-1].set_color("#111")
    ax.yaxis.set_major_formatter(_fmt(casas_eixo, sufixo))
    ax.set_ylim(0, serie.max() * 1.28)
    for i, v in enumerate(dados["VALOR"].to_numpy()):
        cor_rotulo = cor_destaque if i == len(dados) - 1 else "#222"
        ax.text(i, v + serie.max() * 0.035, virgula(v, casas_rotulo, sufixo),
                ha="center", va="bottom", fontsize=12.5, fontweight="bold",
                color=cor_rotulo)


def g1_atraso_dose_resposta(df: pd.DataFrame, dist: pd.DataFrame):
    """Dois paineis de barras, lado a lado, para a detracao e o vies do item (e).

    A versao anterior sobrepunha as duas leituras num so eixo com escala
    secundaria (linha para a razao, barras para a taxa); a comparacao ficava
    dificil porque as duas grandezas nao compartilham unidade nem intuicao
    de eixo. Separar em dois paineis com a mesma ordem de categorias no eixo
    x preserva a leitura conjunta (os mesmos rotulos, lado a lado) sem forcar
    percentual e razao na mesma reta.
    """
    base = (df.groupby("FAIXA_ATRASO", observed=True)["DETRATOR"]
              .mean().mul(100).reindex(ORD_ATRASO))

    pop = dist.groupby("DELAY_DEPARTURE_RANGE")["PERC_PAX"].sum()
    pop = (pop / pop.sum() * 100).reindex(ORD_ATRASO)
    amo = df["FAIXA_ATRASO"].value_counts(normalize=True).mul(100).reindex(ORD_ATRASO)
    razao = (amo / pop).reindex(ORD_ATRASO)

    # Paineis mais estreitos que um grafico de largura plena: o rotulo da
    # ultima faixa quebra em duas linhas para nao colidir com o vizinho.
    rotulos_x = LAB_ATRASO[:-1] + [LAB_ATRASO[-1].replace(" 120", "\n120")]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5.6))
    fig.patch.set_facecolor("#FAF9F6")
    fig.subplots_adjust(top=0.72, bottom=0.16, wspace=0.32)

    _barras_painel(ax1, base, rotulos_x, AZ_CLA, AZ_ESC, 0, 1, "%")
    _cabecalho_painel(ax1, "01", "Associação: taxa de detratores",
                       "% de respondentes classificados como detratores, por faixa de atraso")

    _barras_painel(ax2, razao, rotulos_x, ROXO_CLA, ROXO_ESC, 1, 2, "×")
    ax2.axhline(1, color=VERM, lw=1.4, ls="--", zorder=1)
    ax2.text(-0.11, 1, "1,0×", transform=ax2.get_yaxis_transform(), color=VERM,
              fontsize=10, fontweight="bold", ha="right", va="center")
    subtitulo = _cabecalho_painel(ax2, "02", "Viés: sobre e sub-representação",
                                   "Participação na pesquisa ÷ participação na população de PAX ·")
    fig.canvas.draw()
    caixa = subtitulo.get_window_extent(renderer=fig.canvas.get_renderer())
    caixa_eixo = caixa.transformed(ax2.transAxes.inverted())
    ax2.text(caixa_eixo.x1, 1.075, " tracejado = sem viés", transform=ax2.transAxes,
              fontsize=9.5, color=VERM, va="bottom", fontweight="bold")

    return fig


# ------------------------------------------------- G2: evolucao trimestral (item e)
def g2_serie_temporal(df: pd.DataFrame):
    """Serie trimestral da detracao contra a incidencia de atrasos.

    O contraste entre as duas series e o que sustenta a leitura de efeito de
    periodo em 2024Q4: a detracao sobe acima do que a operacao explica.
    """
    fig, ax = plt.subplots(figsize=(10, 5))

    t = (df.groupby("TRIMESTRE", observed=True)
           .agg(Detratores=("DETRATOR", "mean"),
                Atrasos=("FAIXA_ATRASO", lambda s: (s != ORD_ATRASO[0]).mean()))
           .mul(100).reset_index())
    longo = t.melt("TRIMESTRE", var_name="Série", value_name="pct")

    sns.lineplot(data=longo, x="TRIMESTRE", y="pct", hue="Série", style="Série",
                 markers=["o", "s"], dashes=False, lw=2.4, markersize=7,
                 palette=[VERM, AZ_CLA], ax=ax)

    # A anotacao fica acima das duas series, nunca em coordenada fixa.
    topo = float(t[["Detratores", "Atrasos"]].to_numpy().max())
    piso = float(t[["Detratores", "Atrasos"]].to_numpy().min())
    i = int(t["Detratores"].idxmax())
    pico, v = t.loc[i, "TRIMESTRE"], float(t.loc[i, "Detratores"])
    ax.axvspan(i - 0.5, i + 0.5, color=LARANJA, alpha=0.13, zorder=0)
    ax.annotate(f"Pico de {pico}\n{virgula(v, 1, '%')} de detratores",
                (i, v), xytext=(i + 1.2, topo + 3.5),
                fontsize=9.5, fontweight="bold", color=VERM,
                arrowprops=dict(arrowstyle="->", color=VERM, lw=1.4))

    ax.set(xlabel="", ylabel="Percentual", ylim=(piso - 4, topo + 9))
    ax.yaxis.set_major_formatter(_fmt(0, "%"))
    ax.legend(frameon=False, loc="upper left", title=None)
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
    ax.set_title("Evolução trimestral da detração e da incidência de atrasos", pad=12)
    _rodape(ax, "A detração de 2024Q4 sobe acima do que a variação de atrasos "
                "explica, indicando efeito de período.", y=-0.30)
    return fig


# -------------------------------------------------- G3: heatmap tier x faixa atraso
def g3_heatmap_tier_atraso(df: pd.DataFrame):
    """Mapa de calor da detracao por tier de fidelidade e faixa de atraso.

    Expoe a interacao entre fidelizacao e falha operacional, invisivel em
    analises marginais.
    """
    fig, ax = plt.subplots(figsize=(8.5, 5))

    tiers = [t for t in TIERS if t in set(df["TIER_VIAGEM"].dropna())]
    h = (df[df["TIER_VIAGEM"].isin(tiers)]
         .pivot_table(index="TIER_VIAGEM", columns="FAIXA_ATRASO",
                      values="DETRATOR", aggfunc="mean", observed=True)
         .reindex(index=tiers, columns=ORD_ATRASO) * 100)

    sns.heatmap(h, annot=rotulos(h, 1), fmt="", cmap="RdYlBu_r", vmin=8, vmax=85,
                linewidths=0.6, linecolor="white", ax=ax,
                annot_kws={"fontweight": "bold", "fontsize": 10.5},
                cbar_kws={"label": "Taxa de detratores (%)"})
    ax.collections[0].colorbar.ax.yaxis.set_major_formatter(_fmt(0))
    ax.set_xticklabels(LAB_ATRASO, rotation=0, fontsize=9.5)
    ax.set(xlabel="", ylabel="")
    ax.set_title("Taxa de detratores por tier de fidelidade e faixa de atraso", pad=12)
    _rodape(ax, "A penalização por atraso cresce com o tier: o Cliente Diamante "
                "detrata mais que o sem cadastro em todas as faixas.", y=-0.24)
    return fig


# ------------------------------------------------------- G5: correlacao de Spearman
def g5_correlacao(df: pd.DataFrame):
    """Matriz triangular de correlacao de Spearman entre numericas e o alvo.

    Spearman e nao Pearson porque todas as numericas apresentam forte
    assimetria positiva e o alvo e binario.
    """
    fig, ax = plt.subplots(figsize=(7.5, 6))

    cols = ["DETRATOR", "ESTATISTICA_ATRASOSAIDA", "ATRASO_CHEGADA", "TEMPO_VOO",
            "N_TRECHOS", "QTDE_VIAGENS_12M", "QTDE_VIAGENS_24M", "QTDE_VIAGENS_36M"]
    c = df[cols].corr(method="spearman")
    mask = np.triu(np.ones_like(c, dtype=bool), k=1)

    sns.heatmap(c, mask=mask, annot=rotulos(c, 2), fmt="", cmap="RdBu_r", center=0,
                vmin=-1, vmax=1, square=True, linewidths=0.6, linecolor="white",
                ax=ax, annot_kws={"fontsize": 9, "fontweight": "bold"},
                cbar_kws={"label": "Correlação de Spearman", "shrink": 0.8})
    ax.collections[0].colorbar.ax.yaxis.set_major_formatter(_fmt(2))
    ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha="right", fontsize=9)
    ax.set_yticklabels(ax.get_yticklabels(), rotation=0, fontsize=9)
    ax.set_title("Correlação entre variáveis operacionais e a detração", pad=12)
    return fig


# ------------------------------------------------------------ G7: limiar de atraso
def g7_limiar_atraso(df: pd.DataFrame):
    """Curva de risco por minuto de atraso e o impacto marginal entre faixas.

    Responde a pergunta 5 do escopo da Azul. A composicao com proporcoes
    assimetricas (2,2 para 1) e feita com gridspec do matplotlib, porque o
    painel inferior e leitura de apoio e nao tem o mesmo peso visual.
    """
    fig, (ax, ax2) = plt.subplots(2, 1, figsize=(9, 7), sharex=True,
                                  gridspec_kw={"height_ratios": [2.2, 1]})

    faixa = pd.cut(df["ESTATISTICA_ATRASOSAIDA"], BINS_LIMIAR, labels=LAB_LIMIAR)
    r = (df.groupby(faixa, observed=False)["DETRATOR"].mean().mul(100)
           .reset_index())
    r.columns = ["faixa", "taxa"]
    r = r.dropna(subset=["taxa"]).reset_index(drop=True)
    r["marginal"] = r["taxa"].diff()

    sns.lineplot(data=r, x="faixa", y="taxa", marker="o", color=VERM,
                 lw=2.6, markersize=7, ax=ax)
    ax.fill_between(range(len(r)), r["taxa"], color=VERM, alpha=0.10)

    media = df["DETRATOR"].mean() * 100
    ax.axhline(media, color=CINZA, ls=":", lw=1.5)
    ax.text(0.3, media + 2.5, f"média geral {virgula(media, 1, '%')}",
            color="#666", fontsize=8.5, ha="left")

    # Janela de inflexao localizada pelo rotulo, nao por posicao fixa.
    # Ponto de inflexao: primeira faixa cujo custo marginal ultrapassa o limiar.
    # A faixa e localizada pelos dados, e o rotulo sai das bordas do proprio bin,
    # para que texto e regiao sombreada nao possam divergir.
    acelera = r.index[r["marginal"] >= LIMIAR_MARGINAL]
    if len(acelera):
        i = int(acelera[0])
        pos = LAB_LIMIAR.index(str(r.loc[i, "faixa"]))
        inicio, fim = BINS_LIMIAR[pos], BINS_LIMIAR[pos + 1]
        ax.axvspan(i - 0.5, i + 0.5, color=LARANJA, alpha=0.16, zorder=0)
        ax.annotate(f"Ponto de inflexão\n{inicio} a {fim} min",
                    (i, float(r.loc[i, "taxa"])),
                    xytext=(i + 2, max(media - 13, 4)), fontsize=10,
                    fontweight="bold", color=LARANJA,
                    arrowprops=dict(arrowstyle="->", color=LARANJA, lw=1.6))

    ax.set(xlabel="", ylabel="Taxa de detratores")
    ax.yaxis.set_major_formatter(_fmt(0, "%"))
    ax.set_title("Limiar de atraso: curva de risco e impacto marginal", pad=12)

    rotulo_acima = f"Acima de {LIMIAR_MARGINAL} p.p."
    rotulo_ate = f"Até {LIMIAR_MARGINAL} p.p."
    r["acelera"] = np.where(r["marginal"] >= LIMIAR_MARGINAL, rotulo_acima, rotulo_ate)
    sns.barplot(data=r, x="faixa", y="marginal", hue="acelera",
                palette={rotulo_ate: AZ_CLA, rotulo_acima: LARANJA},
                dodge=False, width=0.6, ax=ax2)
    ax2.axhline(LIMIAR_MARGINAL, color=LARANJA, ls="--", lw=1.2)
    if ax2.get_legend() is not None:
        ax2.get_legend().remove()
    ax2.set(ylabel="Variação em p.p. vs.\nfaixa anterior",
            xlabel="Atraso na saída (minutos)")
    ax2.yaxis.set_major_formatter(_fmt(0))
    ax2.yaxis.set_major_locator(MaxNLocator(integer=True))
    plt.setp(ax2.get_xticklabels(), rotation=45, ha="right")
    _rodape(ax2, "Até 15 min o custo marginal é estável, na ordem de 2 p.p. por "
                 "faixa. A partir de 20 min ele dobra e segue acelerando até 90 min.",
            y=-0.85)
    return fig


# ------------------------------------------- G8: antecedencia do aviso de cancelamento
def g8_antecedencia_cancelamento(df: pd.DataFrame):
    """Detracao e NPS medio por antecedencia do aviso, apenas voos cancelados.

    Mantem o evento negativo constante e varia so a comunicacao, o que isola o
    efeito do aviso.
    """
    fig, ax = plt.subplots(figsize=(9, 5))

    c = df[df["CANCELAMENTO_VOO"].astype(bool)].copy()
    # Faixas vindas de clean.py, para grafico e tabela nao poderem divergir.
    c["FX"] = faixa_antecedencia(c["ANTECEDENCIA_CANCELAMENTO"])
    s = (c.groupby("FX", observed=True)
           .agg(taxa=("DETRATOR", "mean"), nps=("NPS_PRINCIPAL", "mean"))
           .reset_index())
    s["taxa"] *= 100

    sns.barplot(data=s, x="FX", y="taxa", hue="FX", legend=False, dodge=False,
                width=0.6, palette=sns.color_palette("RdYlGn_r", len(s))[::-1], ax=ax)
    for i, v in enumerate(s["taxa"]):
        ax.text(i, v + 1.5, virgula(v, 1, "%"), ha="center",
                fontweight="bold", fontsize=10)

    ax.set(xlabel="", ylabel="Taxa de detratores", ylim=(0, 80))
    ax.yaxis.set_major_formatter(_fmt(0, "%"))
    plt.setp(ax.get_xticklabels(), rotation=20)

    # matplotlib: eixo secundario para o NPS medio, escala e sinal distintos.
    ax2 = ax.twinx()
    ax2.grid(False)
    sns.lineplot(x=range(len(s)), y=s["nps"], marker="o", color=AZ_ESC,
                 lw=2.4, markersize=7, ax=ax2)
    ax2.axhline(0, color=CINZA, ls=":", lw=1.2)
    ax2.set(ylabel="NPS médio", ylim=(-60, 60))
    ax2.yaxis.set_major_formatter(_fmt(0))
    ax2.yaxis.label.set_color(AZ_ESC)
    ax2.tick_params(axis="y", colors=AZ_ESC)

    ax.set_title("Cancelamento: efeito da antecedência do aviso sobre a detração", pad=12)
    n_cancel = f"{len(c):,}".replace(",", ".")
    _rodape(ax, f"Apenas voos cancelados (n = {n_cancel}). Barras: taxa de "
                "detratores. Linha: NPS médio.", y=-0.26)
    return fig


# ---------------------------------------------------------------- G9: sazonalidade
def g9_sazonalidade(df: pd.DataFrame):
    """Pequenos multiplos da detracao mensal, um painel por faixa de atraso.

    Controlar por faixa e o que separa sazonalidade propria de composicao
    operacional.
    """
    d = df.copy()
    d["Mês"] = d["DATA_STD"].dt.month
    d["Faixa"] = pd.Categorical(d["FAIXA_ATRASO"], categories=ORD_ATRASO, ordered=True)
    agr = (d.groupby(["Faixa", "Mês"], observed=True)["DETRATOR"]
             .mean().mul(100).reset_index())

    g = sns.relplot(data=agr, x="Mês", y="DETRATOR", col="Faixa", hue="Faixa",
                    kind="line", marker="o", lw=2.2, markersize=5,
                    palette=PALETA_AZUL, legend=False,
                    facet_kws={"sharey": False}, height=3.4, aspect=0.95)

    meses = ["J", "F", "M", "A", "M", "J", "J", "A", "S", "O", "N", "D"]
    for ax, chave, titulo, cor in zip(g.axes.flat, ORD_ATRASO, LAB_ATRASO, PALETA_AZUL):
        sub = agr[agr["Faixa"] == chave]
        ax.fill_between(sub["Mês"], sub["DETRATOR"].min() - 1, sub["DETRATOR"],
                        color=cor, alpha=0.12)
        ax.set_xticks(range(1, 13))
        ax.set_xticklabels(meses, fontsize=8)
        ax.set_title(titulo.replace("\n", " "), fontsize=10, fontweight="bold")
        ax.yaxis.set_major_formatter(_fmt(0, "%"))
        ax.set_xlabel("")
    g.axes.flat[0].set_ylabel("Taxa de detratores")
    g.figure.suptitle("Sazonalidade da detração, controlada por faixa de atraso",
                      fontweight="bold", y=1.05)
    g.figure.text(0.09, -0.06, "O padrão de dezembro alto e agosto baixo persiste "
                  "dentro de todas as faixas: não é apenas composição operacional.",
                  fontsize=8.5, color="#555")
    return g.figure


# ------------------------------- A.1: histogramas do teste de normalidade (Anexos)
def milhar(v: float) -> str:
    """Separador de milhar com ponto, conforme a norma adotada no documento."""
    return f"{int(v):,}".replace(",", ".")


def _fmt_milhar() -> FuncFormatter:
    return FuncFormatter(lambda v, _pos: milhar(v))


def a1_histograma_normalidade(serie: pd.Series, titulo: str, rotulo_x: str,
                              isolar_zero: bool = False, inteiros: bool = False):
    """Histograma de uma variavel quantitativa para a secao A.1.1.

    Fora de FIGURAS de proposito: recebe uma Serie, e nao o DataFrame de
    `clean.pkl` que o modo script consome, porque a base do anexo e a analitica
    de `data/processed`. Quem a chama e o notebook do anexo.

    Tres decisoes de desenho, porque sem elas a figura nao sustenta o texto que
    a descreve. O eixo de frequencia e logaritmico: em escala linear a barra
    dominante achata o resto contra o eixo e as tres variaveis ficam
    visualmente identicas. O eixo horizontal para no percentil 99, com os
    registros omitidos declarados no rodape, para a area do grafico nao ser
    tomada por valores extremos isolados. E, quando `isolar_zero`, o valor zero
    ganha barra propria: com intervalos uniformes ele se mistura aos valores
    baixos e a barra deixa de corresponder a proporcao citada no texto.
    """
    serie = serie.dropna()
    p99 = serie.quantile(0.99)
    acima_p99 = int((serie > p99).sum())

    if inteiros:
        # Variavel de contagem: um intervalo por valor inteiro, senao os
        # intervalos fracionarios criam vaos que nao existem nos dados.
        limites = np.arange(serie.min(), p99 + 2) - 0.5
    else:
        limites = np.linspace(0 if isolar_zero else serie.min(), p99, 41)
    largura = limites[1] - limites[0]

    fig, ax = plt.subplots(figsize=(9, 4.8))

    if isolar_zero:
        zeros = int((serie == 0).sum())
        ax.bar(-largura / 2, zeros, width=largura * 0.92, color=VERM,
               edgecolor="white", linewidth=0.4, zorder=2)
        ax.hist(serie[(serie > 0) & (serie <= p99)], bins=limites, color=AZ_CLA,
                edgecolor="white", linewidth=0.4, zorder=2)
        ax.set_xlim(-largura * 1.4, p99)
        ax.annotate(f"barra isolada do valor zero:\n{milhar(zeros)} registros "
                    f"({virgula(zeros / len(serie) * 100, 1, '%')})",
                    xy=(-largura / 2, zeros), xytext=(0.30, 0.80),
                    textcoords="axes fraction", fontsize=9, color=VERM,
                    arrowprops=dict(arrowstyle="->", color=VERM, lw=1.2))
    else:
        ax.hist(serie[serie <= p99], bins=limites, color=AZ_CLA,
                edgecolor="white", linewidth=0.4, zorder=2)

    ax.set_yscale("log")
    ax.set(xlabel=rotulo_x, ylabel="Frequência (escala logarítmica)")
    ax.yaxis.set_major_formatter(_fmt_milhar())
    ax.xaxis.set_major_formatter(_fmt_milhar())
    ax.set_title(titulo, pad=12)
    _rodape(ax, f"Eixo horizontal cortado no percentil 99; {milhar(acima_p99)} "
                "registros acima não exibidos.", y=-0.22)
    return fig


FIGURAS = {
    "g1_atraso_dose_resposta": g1_atraso_dose_resposta,
    "g2_serie_temporal": g2_serie_temporal,
    "g3_heatmap_tier_atraso": g3_heatmap_tier_atraso,
    "g5_correlacao": g5_correlacao,
    "g7_limiar_atraso": g7_limiar_atraso,
    "g8_antecedencia_cancelamento": g8_antecedencia_cancelamento,
    "g9_sazonalidade": g9_sazonalidade,
}


if __name__ == "__main__":
    import pickle

    import matplotlib
    matplotlib.use("Agg")   # apenas em execucao por script, nunca no notebook

    from clean import carregar_populacao

    with open("out/clean.pkl", "rb") as fh:
        base = pickle.load(fh)
    populacao = carregar_populacao()

    os.makedirs(OUT_DIR, exist_ok=True)
    for nome, fn in FIGURAS.items():
        fig = fn(base, populacao) if nome.startswith("g1_") else fn(base)
        fig.savefig(os.path.join(OUT_DIR, f"{nome}.png"))
        plt.close(fig)
        print(f"{nome} ok")
