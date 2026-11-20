# ---------------------------------------------------------------- Parte 6
def notebook_parte6():
    return [
        md_txt("""
# Parte 6 — Gráficos

**Três gráficos com Plotly**, salvos em `resultados/`.

Regras do enunciado, aplicadas aos três:

- cada gráfico **responde a uma pergunta**, escrita na célula de texto imediatamente acima;
- o **título carrega a mensagem principal** (não apenas o nome do gráfico);
- abaixo do título há uma **legenda de 2 linhas** com o que está sendo medido e como ler;
- caminhos **relativos com `Path`** — nada é escrito fora de `resultados/`;
- os CSVs de origem **não são sobrescritos**.

Taxa de letalidade = **% de acidentes fatais do grupo**, como em toda a Parte 5.
"""),

        md_txt("""
## 0. Base analítica e utilitários

Lida de `dados_tratados/`. Se ainda não existir, rode antes o notebook da Parte 4.
"""),
        SETUP,
        CARREGA_BASE,

        code_txt("""
import plotly.graph_objects as go

CIMA = "#b03a2e"     # acima da taxa global
BAIXO = "#7f8c8d"    # abaixo da taxa global
NEUTRO = "#2c3e50"
AZUL = "#1f4e79"
BARRA = "#c8d6e5"


def pct(valor: float, casas: int = 2) -> str:
    \"\"\"Percentual no padrão brasileiro — vírgula como separador decimal.\"\"\"
    return f"{valor * 100:.{casas}f}%".replace(".", ",")


def titulo(mensagem: str, legenda_l1: str, legenda_l2: str) -> dict:
    \"\"\"Título com a mensagem principal e a legenda de 2 linhas.\"\"\"
    return dict(
        text=f"<b>{mensagem}</b><br><sup>{legenda_l1}<br>{legenda_l2}</sup>",
        x=0.01, xanchor="left", y=0.99, yanchor="top",
        font=dict(size=16, color="#1a1a1a"),
    )


def salvar_grafico(fig, nome: str) -> None:
    \"\"\"Salva o gráfico em `resultados/` — HTML sempre, PNG quando houver Chrome.\"\"\"
    html = DIR_RESULTADOS / f"{nome}.html"
    fig.write_html(html, include_plotlyjs=True)
    salvos = [html.name]
    try:
        png = DIR_RESULTADOS / f"{nome}.png"
        fig.write_image(png, width=1600, height=900, scale=2)
        salvos.append(png.name)
    except Exception:
        print("PNG não gerado (kaleido precisa de Chrome instalado); HTML salvo.")
    print(f"resultados/: {', '.join(salvos)}")
    fig.show()
"""),

        # ---------------------------------------------------------------- G1
        md_txt("""
---

## Gráfico 1 — Que tipos de acidente elevam a chance de morte?

**Pergunta:** entre os tipos de acidente, quais têm taxa de letalidade acima da global e
o quanto a ultrapassam?

**Resposta:** dois tipos se destacam — **colisão frontal** (29,81%) e **atropelamento de
pedestre** (28,96%) —, ambos com cerca de **4 vezes** a taxa global de 7,16%. Nenhum outro
tipo passa de 8,73%.

Volume mínimo declarado: **100 acidentes por tipo**. Com esse filtro, 16 dos 17 tipos são
exibidos e apenas `Sinistro pessoal de trânsito` fica de fora.
"""),
        code_txt("""
MINIMO_G1 = 100

g1 = df.groupby("tipo_acidente").agg(
    acidentes=("acidente_fatal", "size"),
    fatais=("acidente_fatal", "sum"),
)
g1 = g1[g1["acidentes"] >= MINIMO_G1]
g1["taxa_letalidade"] = g1["fatais"] / g1["acidentes"]
g1["lift"] = g1["taxa_letalidade"] / TAXA_GLOBAL
g1 = g1.sort_values("taxa_letalidade", ascending=True)

excluidos = sorted(set(df["tipo_acidente"].dropna()) - set(g1.index))
top2 = g1["taxa_letalidade"].iloc[-2:]

fig = go.Figure(go.Bar(
    x=g1["taxa_letalidade"] * 100,
    y=g1.index,
    orientation="h",
    marker_color=[CIMA if v > TAXA_GLOBAL else BAIXO for v in g1["taxa_letalidade"]],
    text=[pct(v) for v in g1["taxa_letalidade"]],
    textposition="outside",
    customdata=np.stack([g1["acidentes"], g1["lift"],
                        [pct(v) for v in g1["taxa_letalidade"]]], axis=-1),
    hovertemplate=(
        "<b>%{y}</b><br>Taxa de letalidade: %{customdata[2]}<br>"
        "Acidentes: %{customdata[0]:,}<br>"
        "vezes a taxa global: %{customdata[1]:.2f}"
        "<extra></extra>"
    ),
    name="Taxa de letalidade",
))
fig.add_vline(
    x=TAXA_GLOBAL * 100, line_dash="dash", line_color=NEUTRO, line_width=1.5,
    annotation_text=f"taxa global {pct(TAXA_GLOBAL)}", annotation_position="top",
)

fig.update_layout(
    title=titulo(
        f"Colisão frontal ({pct(top2.iloc[1])}) e atropelamento de pedestre "
        f"({pct(top2.iloc[0])}) têm taxa de letalidade 4× a global",
        f"Barras: taxa de letalidade (% de acidentes fatais do grupo) por tipo de acidente, "
        f"ordenadas da maior para a menor; vermelho acima da taxa global, cinza abaixo.",
        f"Volume mínimo: {MINIMO_G1} acidentes por tipo — {len(g1)} tipos exibidos, "
        f"excluídos: {', '.join(excluidos) if excluidos else 'nenhum'}.",
    ),
    xaxis=dict(title="Taxa de letalidade (%)", gridcolor="#e8e8e8",
               tickformat=".1f", ticksuffix="%"),
    yaxis=dict(title="", automargin=True),
    plot_bgcolor="white", height=640, margin=dict(l=10, r=60, t=120, b=60),
    legend=dict(orientation="h", y=-0.12, x=0),
)
fig.update_xaxes(range=[0, g1["taxa_letalidade"].max() * 100 * 1.18])

assert top2.iloc[0] > 3.5 * TAXA_GLOBAL, "O topo deveria passar de 3,5x a global"
assert len(g1) == 16, f"Esperava 16 tipos com 100+ acidentes, veio {len(g1)}"

salvar_grafico(fig, "g1_taxa_por_tipo_acidente")
"""),

        # ---------------------------------------------------------------- G2
        md_txt("""
---

## Gráfico 2 — A taxa de letalidade varia ao longo dos 36 meses?

**Pergunta:** tomando um mês de cada vez, a taxa de letalidade acompanha o volume de
acidentes ou oscila ao longo dos três anos?

**Resposta:** oscila pouco e **sem tendência**. A taxa mensal fica entre **6,36%** (fev/2024)
e **8,28%** (jun/2023) — amplitude de **1,92 ponto percentual**. A média dos 12 primeiros
meses é 7,16% e a dos 12 últimos é 7,17%: o ponto de partida e o de chegada são o mesmo,
mesmo com o volume de acidentes variando de 4.751 a 6.788 por mês.
"""),
        code_txt("""
mensal = df.groupby(df["data_inversa"].dt.to_period("M")).agg(
    acidentes=("acidente_fatal", "size"),
    fatais=("acidente_fatal", "sum"),
)
mensal["taxa_letalidade"] = mensal["fatais"] / mensal["acidentes"]
mensal.index = mensal.index.astype(str)

amplitude = mensal["taxa_letalidade"].max() - mensal["taxa_letalidade"].min()
inicio = mensal["taxa_letalidade"].head(12).mean()
fim = mensal["taxa_letalidade"].tail(12).mean()

fig = go.Figure()
fig.add_bar(
    x=mensal.index, y=mensal["acidentes"], name="Acidentes no mês",
    yaxis="y2", marker_color=BARRA,
    hovertemplate="<b>%{x}</b><br>Acidentes: %{y:,}<extra></extra>",
)
fig.add_scatter(
    x=mensal.index, y=mensal["taxa_letalidade"] * 100, name="Taxa de letalidade",
    mode="lines+markers", line=dict(color=AZUL, width=2.5), marker=dict(size=5),
    customdata=[[pct(v)] for v in mensal["taxa_letalidade"]],
    hovertemplate="<b>%{x}</b><br>Taxa de letalidade: %{customdata[0]}<extra></extra>",
)
fig.add_hline(
    y=TAXA_GLOBAL * 100, line_dash="dash", line_color=NEUTRO, line_width=1.5,
    annotation_text=f"taxa global {pct(TAXA_GLOBAL)}", annotation_position="top left",
)

fig.update_layout(
    title=titulo(
        f"Em 36 meses a taxa de letalidade variou apenas "
        f"{f'{amplitude * 100:.2f}'.replace('.', ',')} p.p. "
        f"— de {pct(mensal['taxa_letalidade'].min())} a {pct(mensal['taxa_letalidade'].max())}",
        f"Barras (eixo à direita): acidentes registrados no mês. Linha (eixo à esquerda): "
        f"taxa de letalidade do mês; tracejado = taxa global de {pct(TAXA_GLOBAL)}.",
        f"Cada ponto é um mês-calendário, de jan/2023 a dez/2025. A média dos 12 primeiros "
        f"meses ({pct(inicio)}) e a dos 12 últimos ({pct(fim)}) coincidem — sem tendência.",
    ),
    xaxis=dict(title="Mês", tickangle=-60, tickfont=dict(size=9)),
    yaxis=dict(title="Taxa de letalidade (%)", gridcolor="#e8e8e8",
               tickvals=[6, 6.5, 7, 7.5, 8, 8.5],
               ticktext=["6%", "6,5%", "7%", "7,5%", "8%", "8,5%"]),
    yaxis2=dict(title="Acidentes", overlaying="y", side="right", showgrid=False),
    plot_bgcolor="white", height=560, margin=dict(l=10, r=10, t=120, b=110),
    legend=dict(orientation="h", y=-0.28, x=0),
)

assert amplitude < 0.025, "A amplitude mensal deveria ser pequena"
assert abs(inicio - fim) < 0.005, "Não deveria haver tendência entre o começo e o fim"

salvar_grafico(fig, "g2_serie_mensal")
"""),

        # ---------------------------------------------------------------- G3
        md_txt("""
---

## Gráfico 3 — Que horas do dia concentram os acidentes fatais?

**Pergunta:** dividindo o dia em blocos de 3 horas, como se distribuem o volume de acidentes
e a taxa de letalidade?

**Resposta:** a madrugada é o pior período, e o gráfico mostra que **volume e gravidade não
vão juntos**. A faixa **03h–06h** tem a taxa mais alta (**12,26%** — 2,5 vezes a mais segura,
09h–12h com 4,91%), mesmo sendo uma das faixas com menos acidentes. Em volume, quem domina é
18h–21h, com 39.758 acidentes, mas taxa de apenas 8,80%.

Este gráfico detalha, em blocos de 3 horas, o que a Q3 mostrou por `fase_dia`: as horas de
pouca luz são as mais graves.
"""),
        code_txt("""
faixa = df.groupby("faixa_horaria").agg(
    acidentes=("acidente_fatal", "size"),
    fatais=("acidente_fatal", "sum"),
)
faixa["taxa_letalidade"] = faixa["fatais"] / faixa["acidentes"]
faixa = faixa.sort_index()

pior = faixa["taxa_letalidade"].idxmax()
melhor = faixa["taxa_letalidade"].idxmin()
razao = faixa["taxa_letalidade"].max() / faixa["taxa_letalidade"].min()
participacao = faixa.loc[pior, "acidentes"] / len(df)

fig = go.Figure()
fig.add_bar(
    x=faixa.index, y=faixa["acidentes"], name="Acidentes na faixa",
    yaxis="y2", marker_color=BARRA,
    hovertemplate="<b>%{x}</b><br>Acidentes: %{y:,}<extra></extra>",
)
fig.add_scatter(
    x=faixa.index, y=faixa["taxa_letalidade"] * 100, name="Taxa de letalidade",
    mode="lines+markers", line=dict(color=AZUL, width=2.5), marker=dict(size=8),
    customdata=[[pct(v)] for v in faixa["taxa_letalidade"]],
    hovertemplate="<b>%{x}</b><br>Taxa de letalidade: %{customdata[0]}<extra></extra>",
)
fig.add_hline(
    y=TAXA_GLOBAL * 100, line_dash="dash", line_color=NEUTRO, line_width=1.5,
    annotation_text=f"taxa global {pct(TAXA_GLOBAL)}", annotation_position="top left",
)

fig.update_layout(
    title=titulo(
        f"{pior} é a faixa mais letal ({pct(faixa['taxa_letalidade'].max())}) — "
        f"{f'{razao:.1f}'.replace('.', ',')}× a mais segura "
        f"({melhor}, {pct(faixa['taxa_letalidade'].min())})",
        f"Barras (eixo à direita): acidentes na faixa horária. Linha (eixo à esquerda): "
        f"taxa de letalidade; tracejado = taxa global de {pct(TAXA_GLOBAL)}.",
        f"Blocos de 3 horas fechados no início. {pior} responde por "
        f"{pct(participacao, 1)} dos acidentes e {pct(faixa.loc[pior, 'fatais'] / df['acidente_fatal'].sum(), 1)} "
        f"dos fatais — gravidade alta com volume baixo.",
    ),
    xaxis=dict(title="Faixa horária"),
    yaxis=dict(title="Taxa de letalidade (%)", gridcolor="#e8e8e8",
               tickvals=[4, 5, 6, 7, 8, 9, 10, 11, 12, 13],
               ticktext=["4%", "5%", "6%", "7%", "8%", "9%", "10%", "11%", "12%", "13%"]),
    yaxis2=dict(title="Acidentes", overlaying="y", side="right", showgrid=False),
    plot_bgcolor="white", height=560, margin=dict(l=10, r=10, t=120, b=80),
    legend=dict(orientation="h", y=-0.2, x=0),
)

assert razao > 2, "A razão entre a pior e a melhor faixa deveria passar de 2"
assert faixa.loc[pior, "acidentes"] < faixa["acidentes"].max(), (
    "A faixa mais letal não deveria ser a de maior volume"
)

salvar_grafico(fig, "g3_faixa_horaria")
"""),

        md_txt("""
---

## Fechamento da Parte 6

| Gráfico | Pergunta que responde | Mensagem principal | Arquivo |
|---|---|---|---|
| 1 | Que tipos de acidente elevam a chance de morte? | Frontal e atropelamento de pedestre têm taxa 4× a global | `resultados/g1_taxa_por_tipo_acidente.html` |
| 2 | A taxa de letalidade varia ao longo dos 36 meses? | Oscila só 1,92 p.p. e sem tendência | `resultados/g2_serie_mensal.html` |
| 3 | Que horas do dia concentram os acidentes fatais? | 03h–06h tem a taxa mais alta (12,26%) com volume baixo | `resultados/g3_faixa_horaria.html` |

Os três arquivos ficam em `resultados/`, que **não é versionado** (`.gitignore`): o notebook
os regenera a cada execução, a partir das bases em `dados_tratados/`.

Cada gráfico é salvo em **HTML autocontido** (abre offline, sem depender de CDN). O PNG é
também gerado quando há Chrome instalado para o `kaleido`; sem ele, o notebook segue sem
erro e avisa no output.
"""),
    ]
