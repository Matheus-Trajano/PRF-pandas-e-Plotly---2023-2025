# ---------------------------------------------------------------- Parte 7
def notebook_parte7():
    return [
        md_txt("""
# Parte 7 — Síntese

**Três achados**, cada um com os cinco elementos que o enunciado pede:

| Elemento | O que é |
|---|---|
| **Observação** | o que os dados mostram, em número |
| **Onde aparece** | a tabela ou o gráfico que evidencia |
| **Comparação com a taxa global** | lift = taxa do grupo ÷ taxa global de 7,1631% |
| **Hipótese** | uma leitura explicativa, sem pretensão causal |
| **Limitação** | o que estes dados **não** permitem afirmar |

E, ao final, a **categoria que o filtro de volume mínimo descartou**.

Os três achados reaproveitam o que já foi calculado nas Partes 5 e 6 — mas **todo número é
recalculado aqui**, a partir da base analítica da Parte 4, para que este notebook seja
autossuficiente e os achados não dependam da memória de quem rodou a Parte 6.
"""),

        md_txt("""
## 0. Base analítica e utilitários

Lida de `dados_tratados/base_analitica_prf_2023_2025.csv` — a base já vem no repositório.
Se o arquivo não existir, rode antes o notebook da Parte 4.
"""),
        SETUP,
        CARREGA_BASE,
        funcoes_analise(),

        code_txt("""
print(f"Base: {len(df):,} acidentes | {int(df['acidente_fatal'].sum()):,} fatais "
      f"| {int(df['mortos'].sum()):,} mortos")
print(f"Taxa global de letalidade: {TAXA_GLOBAL:.4%}")
print(f"Isto é: 1 acidente fatal a cada {1 / TAXA_GLOBAL:.0f} acidentes registrados")
print(f"Mortes por acidente fatal: {df['mortos'].sum() / df['acidente_fatal'].sum():.2f}")
"""),

        # ---------------------------------------------------------------- Achado 1
        md_txt("""
---

## Achado 1 — Colisão frontal e atropelamento de pedestre concentram a letalidade

**Pergunta:** entre os tipos de acidente com volume suficiente, a alta letalidade é
difusa ou está concentrada em poucos tipos?
"""),
        code_txt("""
MIN_A1 = 100

a1 = df.groupby("tipo_acidente").agg(
    acidentes=("acidente_fatal", "size"),
    fatais=("acidente_fatal", "sum"),
)
a1["taxa_letalidade"] = a1["fatais"] / a1["acidentes"]
a1["lift"] = a1["taxa_letalidade"] / TAXA_GLOBAL
a1_visivel = a1[a1["acidentes"] >= MIN_A1].sort_values("lift", ascending=False)

display(fmt(a1_visivel.head(5))[["acidentes", "fatais", "taxa_letalidade", "lift"]])

top2 = a1_visivel.head(2)
terceiro = a1_visivel.iloc[2]
print(f"Volume mínimo aplicado: {MIN_A1} acidentes por tipo "
      f"({len(a1_visivel)} de {len(a1)} tipos exibidos)")
print()
for nome, linha in top2.iterrows():
    print(f"{nome:<28} {linha['taxa_letalidade']:.2%} | lift {linha['lift']:.2f} | "
          f"{int(linha['fatais']):,} fatais em {int(linha['acidentes']):,} acidentes")
print(f"{terceiro.name:<28} {terceiro['taxa_letalidade']:.2%} | lift {terceiro['lift']:.2f} "
      f"(3º colocado — degrau de "
      f"{top2['taxa_letalidade'].min() - terceiro['taxa_letalidade']:.2%} até o 2º)")
print()
print(f"Os dois primeiros somam {top2['acidentes'].sum() / len(df):.2%} dos acidentes "
      f"e {top2['fatais'].sum() / df['acidente_fatal'].sum():.2%} de todos os fatais")

assert top2["lift"].min() > 4
assert top2["acidentes"].sum() / len(df) < 0.12
assert top2["fatais"].sum() / df["acidente_fatal"].sum() > 0.45
"""),
        md_txt("""
**Observação.** Dois tipos se separam do resto por um degrau largo: **colisão frontal**
(29,81% de letalidade — 4.243 fatais em 14.233 acidentes) e **atropelamento de pedestre**
(28,96% — 2.711 em 9.361). O terceiro colocado, colisão lateral sentido oposto, fica em
8,73%: são mais de 20 pontos percentuais de distância entre o 2º e o 3º. Os dois tipos
juntos são **11,05% dos acidentes** e concentram **45,47% de todos os fatais**.

**Onde aparece.** **Gráfico 1** (`resultados/g1_taxa_por_tipo_acidente.html`) e as tabelas
de **Q5** (lift por tipo) e **Q6** (lift por causa) — nota: `Atropelamento de Pedestre` como
*tipo* e as causas de pedestre de Q6 (`pedestre andava na pista`, lift 5,79) contam o mesmo
fenômeno por dois recortes diferentes.

**Comparação com a taxa global.** 29,81% contra 7,1631% dá **lift 4,16**; 28,96% dá
**lift 4,04**. Nenhum outro tipo exibido passa de **1,22**.

**Hipótese.** Nos dois casos o choque é frontal e **sem espaço de escape**: na colisão
frontal os dois veículos se encaram sem para onde recuar, e no atropelamento a vítima não
tem proteção alguma — nem cinto, nem airbag, nem lataria. Energia alta somada a ausência
de proteção produz lift equivalente por dois mecanismos bastante diferentes, o que reforça
a leitura de que o fator determinante é a *severidade do impacto*, e não o tipo em si.

**Limitação.** `tipo_acidente` é a classificação registrada por quem preencheu o Boletim de
Ocorrência, e o denominador depende de notificação: acidentes sem feridos graves tendem a
não entrar, e a subnotificação é maior justamente em atropelamentos. Não há velocidade, uso
de cinto ou gravidade codificada, então a hipótese **não é testável com esta base** — o
achado é de concentração, não de causa. E 29,81% mede a participação de fatais entre os
acidentes registrados, não risco por pessoa exposta.
"""),

        # ---------------------------------------------------------------- Achado 2
        md_txt("""
---

## Achado 2 — A madrugada tem a taxa mais alta e o volume mais baixo

**Pergunta:** o horário do acidente se relaciona com a letalidade da mesma forma em que se
relaciona com o volume?
"""),
        code_txt("""
a2 = df.groupby("faixa_horaria").agg(
    acidentes=("acidente_fatal", "size"),
    fatais=("acidente_fatal", "sum"),
)
a2["taxa_letalidade"] = a2["fatais"] / a2["acidentes"]
a2["lift"] = a2["taxa_letalidade"] / TAXA_GLOBAL
a2 = a2.sort_index()

display(fmt(a2)[["acidentes", "fatais", "taxa_letalidade", "lift"]])

pior = a2["taxa_letalidade"].idxmax()
melhor = a2["taxa_letalidade"].idxmin()
razao = a2.loc[pior, "taxa_letalidade"] / a2.loc[melhor, "taxa_letalidade"]
pico_volume = a2["acidentes"].idxmax()

print(f"Pior taxa : {pior} — {a2.loc[pior, 'taxa_letalidade']:.2%} "
      f"(lift {a2.loc[pior, 'lift']:.2f}), {a2.loc[pior, 'acidentes'] / len(df):.1%} dos acidentes "
      f"e {a2.loc[pior, 'fatais'] / df['acidente_fatal'].sum():.1%} dos fatais")
print(f"Melhor taxa: {melhor} — {a2.loc[melhor, 'taxa_letalidade']:.2%} "
      f"(lift {a2.loc[melhor, 'lift']:.2f})")
print(f"Razão pior/melhor: {razao:.2f}x")
print(f"Pico de volume: {pico_volume} — {int(a2.loc[pico_volume, 'acidentes']):,} acidentes "
      f"({a2.loc[pico_volume, 'acidentes'] / len(df):.1%} da base), taxa "
      f"{a2.loc[pico_volume, 'taxa_letalidade']:.2%} (lift {a2.loc[pico_volume, 'lift']:.2f})")

fase = df.groupby("fase_dia").agg(
    acidentes=("acidente_fatal", "size"),
    fatais=("acidente_fatal", "sum"),
)
fase["taxa_letalidade"] = fase["fatais"] / fase["acidentes"]
fase["lift"] = fase["taxa_letalidade"] / TAXA_GLOBAL
print()
display(fmt(fase.sort_values("taxa_letalidade", ascending=False))[
    ["acidentes", "fatais", "taxa_letalidade", "lift"]
])
print(f"Plena Noite {fase.loc['Plena Noite', 'taxa_letalidade']:.2%} vs "
      f"Pleno dia {fase.loc['Pleno dia', 'taxa_letalidade']:.2%} — razão "
      f"{fase.loc['Plena Noite', 'taxa_letalidade'] / fase.loc['Pleno dia', 'taxa_letalidade']:.2f}x")

assert razao > 2.4
assert a2.loc[pior, "fatais"] / df["acidente_fatal"].sum() > 0.11
"""),
        md_txt("""
**Observação.** A faixa **03h–06h** tem a taxa mais alta (**12,26%**) e o volume mais
baixo: são 6,9% dos acidentes e **11,9% dos fatais**. A mais segura é 09h–12h, com 4,91% —
**razão de 2,50×** entre as duas. O contraste mais forte está no volume: o pico de
acidentes é **18h–21h** (39.758 registros, 18,6% da base) e mesmo assim a taxa é de 8,80%.
No recorte mais agregado de `fase_dia`, Plena Noite (10,09%) contra Pleno dia (5,02%) dá
**2,01×**.

**Onde aparece.** **Gráfico 3** (`resultados/g3_faixa_horaria.html`) e as tabelas de **Q3**
(`fase_dia`).

**Comparação com a taxa global.** 12,26% contra 7,1631% dá **lift 1,71**; a faixa mais
segura fica em **0,69**, abaixo da média. Pela `fase_dia`, Plena Noite dá 1,41 e Pleno dia
0,70 — a diferença de **5,07 p.p.** entre noite e dia equivale a **70,7% da própria taxa
global**.

**Hipótese.** Três componentes somam-se na madrugada: **visibilidade** ruim, **fadiga ou
sono** ao volante e **tráfego mais escasso** — que remove o "freio social" sem reduzir a
velocidade, porque a sensação de risco do dia é justamente a que falta. Em volume menor, um
excesso de velocidade tem menos tempo de ser corrigido por quem vem atrás.

**Limitação.** O `horario` da base é o do **registro** do acidente, não necessariamente o
da colisão: acidentes sem ferido grave costumam ser registrados com atraso, o que desloca
eventos de um turno para o outro. Blocos de três horas agregam dinâmicas distintas e a base
não traz **exposição** (km percorridos por faixa), então o lift compara frequências, não
risco por quilômetro. E o achado é associação: não é possível distinguir, aqui, a via
noturna iluminada da via noturna sem iluminação.
"""),

        # ---------------------------------------------------------------- Achado 3
        md_txt("""
---

## Achado 3 — O problema é de geometria de via, não de sazonalidade

**Pergunta:** a taxa de letalidade varia com o tempo (sazonalidade, tendência) ou com
características estruturais da via?
"""),
        code_txt("""
# --- (a) estabilidade no tempo
mensal = df.groupby(df["data_inversa"].dt.to_period("M")).agg(
    acidentes=("acidente_fatal", "size"),
    fatais=("acidente_fatal", "sum"),
)
mensal["taxa_letalidade"] = mensal["fatais"] / mensal["acidentes"]
mensal.index = mensal.index.astype(str)

amplitude = mensal["taxa_letalidade"].max() - mensal["taxa_letalidade"].min()
inicio = mensal["taxa_letalidade"].head(12).mean()
fim = mensal["taxa_letalidade"].tail(12).mean()

print(f"{len(mensal)} meses | mínimo {mensal['taxa_letalidade'].min():.2%} "
      f"({mensal['taxa_letalidade'].idxmin()}) | máximo {mensal['taxa_letalidade'].max():.2%} "
      f"({mensal['taxa_letalidade'].idxmax()})")
print(f"Amplitude: {amplitude * 100:.2f} p.p. | 12 primeiros {inicio:.2%} "
      f"vs 12 últimos {fim:.2%} | diferença {(fim - inicio) * 100:+.2f} p.p.")

# --- (b) o contraste estrutural: tipo de pista
a3 = df.groupby("tipo_pista").agg(
    acidentes=("acidente_fatal", "size"),
    fatais=("acidente_fatal", "sum"),
)
a3["taxa_letalidade"] = a3["fatais"] / a3["acidentes"]
a3["lift"] = a3["taxa_letalidade"] / TAXA_GLOBAL
a3 = a3.sort_values("taxa_letalidade", ascending=False)
display(fmt(a3)[["acidentes", "fatais", "taxa_letalidade", "lift"]])

razao_pista = a3.loc["Simples", "taxa_letalidade"] / a3.loc["Dupla", "taxa_letalidade"]
print(f"Simples {a3.loc['Simples', 'taxa_letalidade']:.2%} "
      f"(lift {a3.loc['Simples', 'lift']:.2f}) vs Dupla "
      f"{a3.loc['Dupla', 'taxa_letalidade']:.2%} (lift {a3.loc['Dupla', 'lift']:.2f}) "
      f"— razão {razao_pista:.2f}x")

# --- (c) o mecanismo: contramao por tipo de pista
df["contramao"] = df["causa_acidente"].str.contains("Contramão", case=False, na=False)
cm = df.groupby("tipo_pista").agg(
    acidentes=("contramao", "size"),
    contramao=("contramao", "sum"),
)
cm["pct"] = cm["contramao"] / cm["acidentes"]
cm["razao"] = cm["pct"] / cm.loc["Dupla", "pct"]
print()
print("Contramão por tipo de pista:")
for pista, linha in cm.iterrows():
    print(f"  {pista:<10} {int(linha['contramao']):>6,} de {int(linha['acidentes']):>7,} "
          f"acidentes = {linha['pct']:.2%} | {linha['razao']:.1f}x a da Dupla")

causa_cm = df[df["causa_acidente"] == "Transitar na contramão"]
taxa_cm = causa_cm["acidente_fatal"].mean()
print(f"\\n'Transitar na contramão' como causa: {len(causa_cm):,} acidentes, "
      f"taxa {taxa_cm:.2%}, lift {taxa_cm / TAXA_GLOBAL:.2f}")

# --- (d) o pior cruzamento pista x clima com volume suficiente
clima = df[df["condicao_metereologica"] != "Ignorado"]
contagem = clima.pivot_table(index="tipo_pista", columns="condicao_metereologica",
                             values="acidente_fatal", aggfunc="size", fill_value=0)
taxa = clima.pivot_table(index="tipo_pista", columns="condicao_metereologica",
                         values="acidente_fatal", aggfunc="mean")
valida = contagem >= 50
empilhado = taxa.where(valida).stack().sort_values(ascending=False)
pior_celula = empilhado.index[0]
print()
print(f"Pior célula com volume >= 50: {pior_celula[0]} + {pior_celula[1]} "
      f"→ {empilhado.iloc[0]:.2%} (lift {empilhado.iloc[0] / TAXA_GLOBAL:.2f}, "
      f"{int(contagem.loc[pior_celula]):,} acidentes)")
print(f"Mesma condição na Dupla: {taxa.loc['Dupla', pior_celula[1]]:.2%}")

assert amplitude < 0.025
assert razao_pista > 2
assert cm.loc["Simples", "razao"] > 5
"""),
        md_txt("""
**Observação.** No tempo, quase nada muda: em **36 meses** a taxa mensal fica entre
**6,36%** (fev/2024) e **8,28%** (jun/2023) — amplitude de **1,92 p.p.** — e a média dos
12 primeiros meses (7,16%) é praticamente a dos 12 últimos (7,17%). O que persiste é
estrutural: **pista Simples 9,89%** contra **Dupla 4,71%** e **Múltipla 4,14%** (2,10× a
Dupla), com **contramão em 6,00% dos acidentes** da Simples contra 0,98% na Dupla (**6,1×**).
No cruzamento pista × clima, o pior ponto com volume suficiente é **Simples + Nevoeiro**:
13,95%, contra 8,77% da mesma condição em pista Dupla.

**Onde aparece.** **Gráfico 2** (`resultados/g2_serie_mensal.html`) para a estabilidade no
tempo; as tabelas de **Q8** (`tipo_pista` × `condicao_metereologica`) e **Q11** (causa dos
acidentes críticos) para o contraste de geometria e o mecanismo.

**Comparação com a taxa global.** Simples dá **lift 1,38**; Dupla, 0,66; Múltipla, 0,58. A
causa `Transitar na contramão` isolada dá **lift 4,04** (28,95%), e a pior célula
pista × clima, **lift 1,95**. Contra a taxa global de 7,1631%, a pista Simples está 2,7 p.p.
acima e a Dupla 2,4 p.p. abaixo.

**Hipótese.** A severidade se concentra onde a **separação entre fluxos é menor**: a pista
simples concentra ultrapassagem em contramão e travessia de pedestre sem faixa, e a
contramão é justamente o mecanismo de alta letalidade da base. O nevoeiro agrava o mesmo
cenário ao encurtar a distância de reação. Já a estabilidade mensal diz algo de política
pública: um ano mais chuvoso ou mais de férias não move o resultado — o que move a taxa é
o desenho da via, não o calendário.

**Limitação.** `tipo_pista` é um **proxy** do desenho da via e se confunde com a identidade
da rodovia: as vias de pista simples concentram-se em BRs de menor velocidade, mais
distantes e com mais travessias. A diferença observada pode ser geometria *ou* mistura de
rotas — a base não traz velocidade, RTT nem geometria, então os dois mecanismos não são
separáveis aqui. E 36 meses é uma série curta para sustentar a afirmação de estabilidade
estrutural; a taxa mensal ainda é sensível ao mix de registro de cada mês.
"""),

        # ---------------------------------------------------------------- Descarte
        md_txt("""
---

## O que o filtro de volume mínimo descartou

Todo filtro de volume da Parte 5 e da Parte 6 tem um custo: categorias reais ficam de fora
das tabelas. A categoria mais expressiva é **`Participar de racha`** — 52 acidentes, 13
fatais, **25,00% de letalidade (lift 3,49)**. Com menos de 100 registros ela não passa do
corte da **Q6**; sem o filtro, ocuparia a **6ª posição** por lift, logo atrás do corte do
top 5 (lift 3,60).
"""),
        code_txt("""
# --- Q6: causas com menos de 100 acidentes
q6 = df.groupby("causa_acidente").agg(
    acidentes=("acidente_fatal", "size"),
    fatais=("acidente_fatal", "sum"),
)
q6["taxa_letalidade"] = q6["fatais"] / q6["acidentes"]
q6["lift"] = q6["taxa_letalidade"] / TAXA_GLOBAL
ranking_completo = q6.sort_values("lift", ascending=False)
visiveis = q6[q6["acidentes"] >= 100].sort_values("lift", ascending=False)

print(f"Causas no vocabulário: {len(q6)} | exibidas com >= 100: {len(visiveis)} "
      f"| descartadas: {len(q6) - len(visiveis)}")
print()
print("Causas descartadas pelo filtro de volume, ordenadas por lift:")
excluidas = q6[q6["acidentes"] < 100].sort_values("lift", ascending=False)
for nome, linha in list(excluidas.head(5).iterrows()):
    posicao = list(ranking_completo.index).index(nome) + 1
    print(f"  {nome[:52]:<52} {int(linha['acidentes']):>5} ac | {linha['taxa_letalidade']:>7.2%} "
          f"| lift {linha['lift']:.2f} | {posicao}º lugar no ranking completo")

racha = "Participar de racha"
print()
print(f"'{racha}': {int(q6.loc[racha, 'acidentes'])} acidentes, "
      f"{int(q6.loc[racha, 'fatais'])} fatais, taxa {q6.loc[racha, 'taxa_letalidade']:.2%}, "
      f"lift {q6.loc[racha, 'lift']:.2f}")
print(f"  posição no ranking completo : {list(ranking_completo.index).index(racha) + 1} "
      f"de {len(ranking_completo)}")
print(f"  corte do top 5 (>= 100 ac)   : lift {visiveis.head(5)['lift'].iloc[-1]:.2f}")
print(f"  passaria no filtro?          : "
      f"{'SIM' if q6.loc[racha, 'acidentes'] >= 100 else 'NÃO'}")

# --- outros filtros e o que cada um deixou de fora
tracados = df["tracado_via"].str.split(";").explode().str.strip()
volume_tracado = tracados.value_counts()
noite = df[df["fase_dia"] == "Plena Noite"]
q9 = noite.groupby("br").agg(acidentes=("acidente_fatal", "size"), mortos=("mortos", "sum"))
pe = df[(df["uf"] == "PE") & (df["ano_acidente"].isin([2024, 2025]))]
q12 = pe.groupby("municipio").agg(acidentes=("acidente_fatal", "size"), mortos=("mortos", "sum"))

print()
print("Outros descartes por filtro de volume:")
print(f"  Q5 / G1 (>= 100 ac por tipo de acidente): "
      f"{', '.join(a1[a1['acidentes'] < 100].index)}")
print(f"  Q7 (>= 501 ac por traçado): "
      f"{', '.join(volume_tracado[volume_tracado < 501].index)}")
print(f"  Q9 (>= 50 ac noturnos por BR): {int((q9['acidentes'] < 50).sum())} de {len(q9)} BRs")
print(f"  Q12 (>= 50 ac fatais no município de PE): "
      f"{int((q12['acidentes'] < 50).sum())} de {len(q12)} municípios")
print(f"  Q8 (>= 50 ac por célula pista × clima): {int((contagem < 50).values.sum())} células")

print()
print("O caso mais extremo: BR-308 em plena noite")
br308 = q9.loc[308]
print(f"  {int(br308['acidentes'])} acidentes noturnos | {int(br308['mortos'])} mortos | "
      f"{br308['mortos'] / br308['acidentes']:.0%} de mortos por acidente")
print("  (abaixo do corte de 50 acidentes noturnos da Q9)")

assert q6.loc[racha, "acidentes"] < 100
assert q6.loc[racha, "lift"] > 3
"""),
        md_txt("""
**O custo do filtro, explicitado.** A Q6 mostra 75 causas no vocabulário e exibe 57: as
**18 restantes** saem do corte de 100 acidentes. Entre elas, `Participar de racha` seria a
**6ª por lift** — a posição imediatamente anterior ao top 5. É um caso em que o filtro,
justamente por exigir volume, esconde um padrão de alta gravidade: 25,00% de letalidade
contra 7,16% da base. O mesmo padrão se repete nos outros filtros: `Sinistro pessoal de
trânsito` (20 acidentes, 15,00%, lift 2,09) seria o **3º colocado** entre os tipos de
acidente se o corte de 100 não existisse; `Túnel` (125 acidentes) sai da Q7, que exige
mais de 500; **36 das 119 BRs** saem da Q9; **64 dos 90 municípios** de PE saem da Q12; e
seis células de pista × clima — as de Granizo e Neve, com 0 a 3 registros cada — ficam
fora da Q8.

**Por que o filtro existe e o que ele custa.** Com 52 registros, a taxa de `Participar de
racha` tem intervalo de confiança largo e um único evento a move; com 20 registros, o
`Sinistro pessoal de trânsito` tem taxa de 15,00% que pode ser 10% ou 20%. Publicar esses
números como se fossem tendências seria impreciso — por isso o corte. O ponto da síntese
não é dispensar o filtro, é **declará-lo**: as tabelas acima mostram o que ficou de fora,
com o volume que justifica a exclusão, para que a ausência possa ser lida como informação
e não como esquecimento.
"""),

        # ---------------------------------------------------------------- Resumo + grafico
        md_txt("""
---

## Quadro-resumo dos três achados

Os três achados, lado a lado, com a comparação com a taxa global (lift) e a referência de
onde cada um aparece.
"""),
        code_txt("""
resumo = pd.DataFrame([
    {
        "Achado": "1. Tipo de acidente",
        "Mensagem": f"Colisão frontal ({a1_visivel['taxa_letalidade'].iloc[0]:.2%}) e "
                    f"atropelamento de pedestre ({a1_visivel['taxa_letalidade'].iloc[1]:.2%})",
        "Lift": f"{a1_visivel['lift'].iloc[0]:.2f} / {a1_visivel['lift'].iloc[1]:.2f}",
        "Onde": "Gráfico 1 + Q5, Q6",
    },
    {
        "Achado": "2. Horário",
        "Mensagem": f"03h-06h tem a taxa mais alta ({a2.loc['03h-06h', 'taxa_letalidade']:.2%}) "
                    f"com o menor volume; 2,50x a mais segura",
        "Lift": f"{a2.loc['03h-06h', 'lift']:.2f} / {a2.loc['09h-12h', 'lift']:.2f}",
        "Onde": "Gráfico 3 + Q3",
    },
    {
        "Achado": "3. Geometria da via",
        "Mensagem": f"Pista Simples {a3.loc['Simples', 'taxa_letalidade']:.2%} contra "
                    f"{a3.loc['Dupla', 'taxa_letalidade']:.2%} na Dupla; 36 meses sem tendencia",
        "Lift": f"{a3.loc['Simples', 'lift']:.2f} / {a3.loc['Dupla', 'lift']:.2f}",
        "Onde": "Gráfico 2 + Q8, Q11",
    },
])
display(resumo)
"""),

        code_txt("""
import plotly.graph_objects as go

NEUTRO = "#2c3e50"
ABAIXO = "#7f8c8d"
DESTAQUE = "#1f4e79"


def pct(valor, casas=2):
    # percentual no padrão brasileiro
    return f"{valor * 100:.{casas}f}%".replace(".", ",")


contramao = df[df["causa_acidente"] == "Transitar na contramão"]["acidente_fatal"].mean()

grupos = [
    ("Colisão frontal", a1_visivel.loc["Colisão frontal", "lift"],
     a1_visivel.loc["Colisão frontal", "taxa_letalidade"]),
    ("Atropelamento de pedestre", a1_visivel.loc["Atropelamento de Pedestre", "lift"],
     a1_visivel.loc["Atropelamento de Pedestre", "taxa_letalidade"]),
    ("Contramão (causa)", contramao / TAXA_GLOBAL, contramao),
    ("Faixa 03h-06h", a2.loc["03h-06h", "lift"], a2.loc["03h-06h", "taxa_letalidade"]),
    ("Pista Simples", a3.loc["Simples", "lift"], a3.loc["Simples", "taxa_letalidade"]),
    ("Pista Dupla", a3.loc["Dupla", "lift"], a3.loc["Dupla", "taxa_letalidade"]),
    ("Faixa 09h-12h", a2.loc["09h-12h", "lift"], a2.loc["09h-12h", "taxa_letalidade"]),
]
nomes = [g[0] for g in grupos]
lifts = [g[1] for g in grupos]
taxas = [g[2] for g in grupos]

fig = go.Figure(go.Bar(
    x=lifts,
    y=nomes,
    orientation="h",
    marker_color=[DESTAQUE if l > 1 else ABAIXO for l in lifts],
    text=[pct(t) for t in taxas],
    textposition="outside",
    customdata=[[pct(t)] for t in taxas],
    hovertemplate="<b>%{y}</b><br>Taxa: %{customdata[0]}<br>Lift: %{x:.2f}<extra></extra>",
    name="Lift vs taxa global",
))
fig.add_vline(
    x=1.0, line_dash="dash", line_color=NEUTRO, line_width=1.5,
    annotation_text="taxa global (lift = 1,00)", annotation_position="top",
)

fig.update_layout(
    title=dict(
        text="<b>Os três achados apontam para o mesmo lado: os grupos de risco ficam "
             "1,4x a 4,2x acima da taxa global</b>"
             "<br><sup>Barras: lift = taxa de letalidade do grupo ÷ taxa global de 7,16%; "
             "acima de 1,00 em azul, abaixo em cinza."
             "<br>Grupos: Achado 1 (tipo de acidente), Achado 2 (faixa horária) e "
             "Achado 3 (tipo de pista); contramão e faixa 09h-12h como contraponto.</sup>",
        x=0.01, xanchor="left", y=0.99, yanchor="top",
        font=dict(size=16, color="#1a1a1a"),
    ),
    xaxis=dict(title="Lift (taxa do grupo ÷ taxa global)", gridcolor="#e8e8e8"),
    yaxis=dict(title="", automargin=True),
    plot_bgcolor="white", height=520, margin=dict(l=10, r=90, t=120, b=60),
    legend=dict(orientation="h", y=-0.12, x=0),
)
fig.update_xaxes(range=[0, max(lifts) * 1.25])

assert min(lifts) < 1 < max(lifts)
print("resultados/: g4_sintese_achados.html")
fig.write_html(DIR_RESULTADOS / "g4_sintese_achados.html", include_plotlyjs=True)
fig.show()
"""),

        md_txt("""
---

## Fecho da Parte 7

| Achado | Observação | Onde | vs taxa global | Hipótese | Limitação |
|---|---|---|---|---|---|
| **1** | Colisão frontal 29,81% e atropelamento 28,96%: 11,05% dos acidentes, 45,47% dos fatais | Gráfico 1 + Q5/Q6 | lift 4,16 e 4,04 | choque frontal sem escape; vítima sem proteção | classificação do BO, subnotificação, sem velocidade |
| **2** | 03h–06h: 6,9% dos acidentes e 11,9% dos fatais; 2,50× a faixa mais segura | Gráfico 3 + Q3 | lift 1,71 (mais segura: 0,69) | visibilidade, fadiga e tráfego escasso | horário de registro, sem exposição por km, associação |
| **3** | Pista Simples 9,89% contra Dupla 4,71%; contramão 6,1× mais frequente; 36 meses sem tendência | Gráfico 2 + Q8/Q11 | lift 1,38 (Dupla: 0,66) | separação de fluxos e contramão | `tipo_pista` é proxy, confundido com a BR; 36 meses é curto |
| **Descarte** | `Participar de racha` — 52 acidentes, 25,00%, lift 3,49 — seria 6º por lift | Q6 | lift 3,49 | racha tem o perfil de alta gravidade que o corte esconde | com 52 registros, um evento move a taxa |

O **gráfico de síntese** (`resultados/g4_sintese_achados.html`) junta os três achados em uma
escala só — o lift de cada grupo contra a linha da taxa global — com dois contraponto
(`Contramão`, lift 4,04; `Faixa 09h-12h`, lift 0,69) para mostrar que a separação entre
acima e abaixo da média é o que os três achados têm em comum.

Nenhum dos três achados é uma explicação causal: todos são leituras de **concentração**,
com a hipótese e a limitação explicitadas. É o máximo que uma base de acidentes
registrados, sem velocidade, sem geometria e sem exposição, permite afirmar.
"""),
    ]
