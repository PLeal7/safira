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
def g1_atraso_dose_resposta(df: pd.DataFrame, dist: pd.DataFrame):
    """Barras de detracao por faixa de atraso com a razao amostra/populacao.

    Sobrepoe os dois fenomenos que o item (e) trata em conjunto: o efeito
    dose-resposta do atraso e a sobre-representacao das faixas mais graves.
    """
    fig, ax = plt.subplots(figsize=(9, 5))

    base = (df.groupby("FAIXA_ATRASO", observed=True)["DETRATOR"]
              .mean().mul(100).reindex(ORD_ATRASO).reset_index())
    sns.barplot(data=base, x="FAIXA_ATRASO", y="DETRATOR", order=ORD_ATRASO,
                hue="FAIXA_ATRASO", palette=PALETA_AZUL, legend=False,
                width=0.55, ax=ax)
    for i, v in enumerate(base["DETRATOR"]):
        ax.text(i, v + 1.8, virgula(v, 1, "%"), ha="center",
                fontweight="bold", fontsize=11)

    pop = dist.groupby("DELAY_DEPARTURE_RANGE")["PERC_PAX"].sum()
    pop = (pop / pop.sum() * 100).reindex(ORD_ATRASO)
    amo = df["FAIXA_ATRASO"].value_counts(normalize=True).mul(100).reindex(ORD_ATRASO)
    razao = (amo / pop).to_numpy()

    ax.set(xlabel="", ylabel="Taxa de detratores", ylim=(0, base["DETRATOR"].max() * 1.22))
    ax.set_xticks(range(4))
    ax.set_xticklabels(LAB_ATRASO)
    ax.yaxis.set_major_formatter(_fmt(0, "%"))

    # matplotlib: eixo secundario para a razao de representatividade.
    ax2 = ax.twinx()
    ax2.grid(False)
    sns.lineplot(x=range(4), y=razao, marker="o", color=AZ_ESC, lw=2,
                 markersize=8, linestyle="--", ax=ax2)
    ax2.axhline(1, color=CINZA, lw=1.2, ls=":")
    ax2.set(ylabel="Amostra dividida pela população de PAX",
            ylim=(0, max(2.2, float(razao.max()) * 1.45)))
    ax2.yaxis.set_major_formatter(_fmt(1))
    ax2.yaxis.label.set_color(AZ_ESC)
    ax2.tick_params(axis="y", colors=AZ_ESC)
    for i, r in enumerate(razao):
        # Rotulo acima ou abaixo do marcador conforme a altura, com fundo branco,
        # para nunca colidir com o rotulo da barra.
        desloc = (0, 12) if r < razao.max() * 0.6 else (0, -18)
        ax2.annotate(virgula(r, 2, "x"), (i, r), textcoords="offset points",
                     xytext=desloc, ha="center", color=AZ_ESC,
                     fontsize=9, fontweight="bold",
                     bbox=dict(boxstyle="round,pad=.15", fc="white", ec="none", alpha=.75))

    ax.set_title("Atraso na saída: efeito sobre a detração e viés de resposta", pad=14)
    _rodape(ax, "Barras: taxa de detratores por faixa. Linha: razão entre a "
                "participação na pesquisa e na população de passageiros.")
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
