"""
Auditoria numérica independente.

Recalcula do zero, a partir da base analítica gerada pelos notebooks, todos os
números afirmados nas 12 questões, nos 3 gráficos e na síntese, e compara com o
que está escrito nos notebooks.

Uso:  python tools/auditoria_numerica.py
"""

import glob
import json
import os
import re
import sys

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

BASE = "dados_tratados/base_analitica_prf_2023_2025.csv"
df = pd.read_csv(BASE, sep=";", encoding="utf-8-sig",
                 dtype={"id": "string"}, low_memory=False)
df["data_inversa"] = pd.to_datetime(df["data_inversa"], errors="coerce")

TAXA_GLOBAL = df["acidente_fatal"].mean()
N_ACID = len(df)
N_FATAIS = int(df["acidente_fatal"].sum())
N_MORTOS = int(df["mortos"].sum())

OK, FALHAS = [], []


def check(cond, msg_ok, msg_fail):
    (OK if cond else FALHAS).append(msg_ok if cond else msg_fail)
    return cond


def perto(a, b, tol=5e-5):
    return abs(a - b) <= tol


def pct(x):
    return f"{x * 100:.4f}%"


def indicadores(grupo, minimo=0):
    g = df.groupby(grupo).agg(acidentes=("acidente_fatal", "size"),
                              fatais=("acidente_fatal", "sum"))
    g = g[g["acidentes"] >= minimo]
    g["taxa"] = g["fatais"] / g["acidentes"]
    g["lift"] = g["taxa"] / TAXA_GLOBAL
    return g


def texto_notebooks():
    t = ""
    for f in sorted(glob.glob("notebooks/*.ipynb")):
        nb = json.load(open(f, encoding="utf-8"))
        for c in nb["cells"]:
            t += "".join(c["source"]) + "\n"
    return t


T = texto_notebooks()


def no_texto(valor, casas=2):
    """O numero aparece no texto dos notebooks?"""
    br = f"{valor:.{casas}f}".replace(".", ",")
    return br in T


print("=" * 74)
print("AUDITORIA NUMERICA INDEPENDENTE")
print("=" * 74)
print(f"Base: {N_ACID:,} acidentes | {N_FATAIS:,} fatais | {N_MORTOS:,} mortos")
print(f"Taxa global: {pct(TAXA_GLOBAL)}")
print("=" * 74)

# ------------------------------------------------------------------ base
check(N_ACID == 213497, "Base com 213.497 acidentes", f"Base com {N_ACID} (esperado 213.497)")
check(N_FATAIS == 15293, "15.293 acidentes fatais", f"{N_FATAIS} fatais (esperado 15.293)")
check(N_MORTOS == 17833, "17.833 mortos", f"{N_MORTOS} mortos (esperado 17.833)")
check(perto(TAXA_GLOBAL, 0.071631), "Taxa global 7,1631%", f"Taxa global {pct(TAXA_GLOBAL)}")

# -------------------------------------------------------------------- Q1
q1 = df.groupby("ano_acidente").agg(acidentes=("acidente_fatal", "size"),
                                     fatais=("acidente_fatal", "sum"))
q1["taxa"] = q1["fatais"] / q1["acidentes"]
for ano, esperado in [(2023, 0.071688), (2024, 0.071378), (2025, 0.071833)]:
    got = q1.loc[ano, "taxa"]
    check(perto(got, esperado, 1e-5), f"Q1 {ano}: {pct(got)}", f"Q1 {ano}: {pct(got)} != {esperado}")
check(perto(q1.loc[2025, "taxa"] - q1.loc[2023, "taxa"], 0.0001455, 1e-5),
      "Q1 variacao 2023->2025 = +0,01455 p.p.",
      f"Q1 variacao = {(q1.loc[2025,'taxa']-q1.loc[2023,'taxa'])*100:.5f} p.p.")

# -------------------------------------------------------------------- Q2
q2 = df.groupby("mes_acidente").agg(acidentes=("acidente_fatal", "size"),
                                     fatais=("acidente_fatal", "sum"))
q2["taxa"] = q2["fatais"] / q2["acidentes"]
mes_max = q2["taxa"].idxmax()
mes_min = q2["taxa"].idxmin()
check(mes_max == 5 and perto(q2.loc[5, "taxa"], 0.077056, 1e-5),
      f"Q2 maior taxa: maio {pct(q2.loc[5,'taxa'])}",
      f"Q2 maior taxa: mes {mes_max} {pct(q2.loc[mes_max,'taxa'])}")
check(perto(q2.loc[2, "taxa"], 0.065741, 1e-5), f"Q2 menor taxa: fevereiro {pct(q2.loc[2,'taxa'])}",
      f"Q2 fevereiro {pct(q2.loc[2,'taxa'])}")
amp = (q2["taxa"].max() - q2["taxa"].min()) * 100
check(perto(amp, 1.13165, 1e-4), f"Q2 amplitude {amp:.5f} p.p.", f"Q2 amplitude {amp:.5f} p.p.")

# -------------------------------------------------------------------- Q3
q3 = df.groupby("fase_dia").agg(acidentes=("acidente_fatal", "size"),
                                 fatais=("acidente_fatal", "sum"))
q3["taxa"] = q3["fatais"] / q3["acidentes"]
check(perto(q3.loc["Plena Noite", "taxa"], 0.100879, 1e-5),
      f"Q3 Plena Noite {pct(q3.loc['Plena Noite','taxa'])}",
      f"Q3 Plena Noite {pct(q3.loc['Plena Noite','taxa'])}")
check(perto(q3.loc["Pleno dia", "taxa"], 0.050207, 1e-5),
      f"Q3 Pleno dia {pct(q3.loc['Pleno dia','taxa'])}",
      f"Q3 Pleno dia {pct(q3.loc['Pleno dia','taxa'])}")
check(perto(q3.loc["Amanhecer", "taxa"], 0.113614, 1e-5),
      f"Q3 Amanhecer {pct(q3.loc['Amanhecer','taxa'])}",
      f"Q3 Amanhecer {pct(q3.loc['Amanhecer','taxa'])}")
check(perto(q3.loc["Anoitecer", "taxa"], 0.066907, 1e-5),
      f"Q3 Anoitecer {pct(q3.loc['Anoitecer','taxa'])}",
      f"Q3 Anoitecer {pct(q3.loc['Anoitecer','taxa'])}")
check(int(q3.loc["Plena Noite", "acidentes"]) == 73603, "Q3 Plena Noite = 73.603 acidentes",
      f"Q3 Plena Noite = {int(q3.loc['Plena Noite','acidentes'])}")
check(int(q3.loc["Pleno dia", "acidentes"]) == 118012, "Q3 Pleno dia = 118.012 acidentes",
      f"Q3 Pleno dia = {int(q3.loc['Pleno dia','acidentes'])}")
vol_menos = 1 - q3.loc["Plena Noite", "acidentes"] / q3.loc["Pleno dia", "acidentes"]
check(perto(vol_menos, 0.376, 1e-3), f"Q3 Plena Noite tem {vol_menos*100:.1f}% menos acidentes",
      f"Q3 volume diff = {vol_menos*100:.2f}%")

# -------------------------------------------------------------------- Q4
q4 = df.groupby("fim_de_semana").agg(acidentes=("acidente_fatal", "size"),
                                     fatais=("acidente_fatal", "sum"))
q4["taxa"] = q4["fatais"] / q4["acidentes"]
rr = q4.loc[1, "taxa"] / q4.loc[0, "taxa"]
check(perto(q4.loc[1, "taxa"], 0.084288, 1e-5), f"Q4 fim de semana {pct(q4.loc[1,'taxa'])}",
      f"Q4 fim de semana {pct(q4.loc[1,'taxa'])}")
check(perto(q4.loc[0, "taxa"], 0.065614, 1e-5), f"Q4 dias uteis {pct(q4.loc[0,'taxa'])}",
      f"Q4 dias uteis {pct(q4.loc[0,'taxa'])}")
check(perto(rr, 1.2846, 1e-3), f"Q4 RR = {rr:.4f}", f"Q4 RR = {rr:.4f}")

# -------------------------------------------------------------------- Q5
q5 = indicadores("tipo_acidente", 100)
check(len(q5) == 16, f"Q5 {len(q5)} tipos com n>=100", f"Q5 {len(q5)} tipos (esperado 16)")
check(perto(q5.loc["Colisão frontal", "taxa"], 0.298110, 1e-5),
      f"Q5 frontal {pct(q5.loc['Colisão frontal','taxa'])}",
      f"Q5 frontal {pct(q5.loc['Colisão frontal','taxa'])}")
check(perto(q5.loc["Colisão frontal", "lift"], 4.1617, 1e-3),
      f"Q5 frontal lift {q5.loc['Colisão frontal','lift']:.4f}",
      f"Q5 frontal lift {q5.loc['Colisão frontal','lift']:.4f}")
check(perto(q5.loc["Atropelamento de Pedestre", "taxa"], 0.289606, 1e-5),
      f"Q5 atropelamento {pct(q5.loc['Atropelamento de Pedestre','taxa'])}",
      f"Q5 atropelamento {pct(q5.loc['Atropelamento de Pedestre','taxa'])}")
check(perto(q5.loc["Atropelamento de Pedestre", "lift"], 4.0430, 1e-3),
      f"Q5 atropelamento lift {q5.loc['Atropelamento de Pedestre','lift']:.4f}",
      f"Q5 atropelamento lift {q5.loc['Atropelamento de Pedestre','lift']:.4f}")
ac2 = q5.loc["Colisão frontal", "acidentes"] + q5.loc["Atropelamento de Pedestre", "acidentes"]
ft2 = q5.loc["Colisão frontal", "fatais"] + q5.loc["Atropelamento de Pedestre", "fatais"]
check(int(ft2) == 6954, f"Q5 juntos: {int(ft2)} fatais", f"Q5 juntos: {int(ft2)} fatais")
check(int(ac2) == 23594, f"Q5 juntos: {int(ac2)} acidentes", f"Q5 juntos: {int(ac2)} acidentes")
check("Sinistro pessoal de trânsito" not in q5.index, "Q5 exclui Sinistro pessoal (n<100)",
      "Q5 inclui Sinistro pessoal")

# -------------------------------------------------------------------- Q6
q6 = indicadores("causa_acidente", 100)
check(perto(q6.loc["Suicídio (presumido)", "taxa"], 0.509132, 1e-5),
      f"Q6 suicidio {pct(q6.loc['Suicídio (presumido)','taxa'])}",
      f"Q6 suicidio {pct(q6.loc['Suicídio (presumido)','taxa'])}")
check(perto(q6.loc["Suicídio (presumido)", "lift"], 7.1077, 1e-3),
      f"Q6 suicidio lift {q6.loc['Suicídio (presumido)','lift']:.4f}",
      f"Q6 suicidio lift {q6.loc['Suicídio (presumido)','lift']:.4f}")
check(perto(q6.loc["Ultrapassagem Indevida", "taxa"], 0.165914, 1e-5),
      f"Q6 ultrapassagem {pct(q6.loc['Ultrapassagem Indevida','taxa'])}",
      f"Q6 ultrapassagem {pct(q6.loc['Ultrapassagem Indevida','taxa'])}")
alcool_ped = [c for c in q6.index if "álcool" in c.lower() and "pedestre" in c.lower()]
check(len(alcool_ped) == 2, "Q6 duas categorias de alcool do pedestre",
      f"Q6 categorias alcool-pedestre: {alcool_ped}")
for c in alcool_ped:
    print(f"     Q6 {c}: n={int(q6.loc[c,'acidentes'])}, "
          f"taxa={q6.loc[c,'taxa']*100:.4f}%, lift={q6.loc[c,'lift']:.2f}")
rank_ped = q6["lift"].rank(ascending=False, method="min").loc[alcool_ped]
check(int(rank_ped.min()) == 8, f"Q6 alcool-pedestre mais letal em {int(rank_ped.min())}o lugar",
      f"Q6 alcool-pedestre em {int(rank_ped.min())}o lugar")
check(int(rank_ped.max()) == 16, f"Q6 outra categoria em {int(rank_ped.max())}o lugar",
      f"Q6 outra categoria em {int(rank_ped.max())}o lugar")
cond = df[df["causa_acidente"] == "Ingestão de álcool pelo condutor"]
cond_t = cond["acidente_fatal"].mean()
check(perto(cond_t, 0.045336, 1e-5), f"Q6 alcool do condutor {pct(cond_t)}",
      f"Q6 alcool do condutor {pct(cond_t)}")
check(perto(cond_t / TAXA_GLOBAL, 0.63, 1e-2),
      f"Q6 lift alcool condutor {cond_t/TAXA_GLOBAL:.2f}",
      f"Q6 lift alcool condutor {cond_t/TAXA_GLOBAL:.2f}")
check("Participar de racha" not in q6.index, "Q6 exclui 'Participar de racha' (n<100)",
      "Q6 inclui 'Participar de racha'")

# -------------------------------------------------------------------- Q7
multi = df["tracado_via"].astype(str).str.contains(";", regex=False).sum()
check(multi > 0, f"Q7 multi-valor detectado ({multi} registros)", "Q7 sem multi-valor")
linhas = df.assign(t=df["tracado_via"].astype(str).str.split(";"))
expl = linhas.explode("t")
q7 = expl.groupby("t").agg(acidentes=("acidente_fatal", "size"),
                            fatais=("acidente_fatal", "sum"))
q7 = q7[q7["acidentes"] > 500]
q7["taxa"] = q7["fatais"] / q7["acidentes"]
for tr, esp in [("Reta", 0.073477), ("Curva", 0.081879), ("Ponte", 0.107455),
                ("Declive", 0.098505), ("Aclive", 0.086527), ("Rotatória", 0.020555),
                ("Retorno Regulamentado", 0.033017)]:
    check(perto(q7.loc[tr, "taxa"], esp, 1e-4), f"Q7 {tr} {pct(q7.loc[tr,'taxa'])}",
          f"Q7 {tr} {pct(q7.loc[tr,'taxa'])} != {esp}")

# -------------------------------------------------------------------- Q8
p8 = df[df["condicao_metereologica"] != "Ignorado"]
check(len(p8) == N_ACID - (df["condicao_metereologica"] == "Ignorado").sum(),
      "Q8 exclui 'Ignorado' da margem clima",
      "Q8 nao exclui 'Ignorado'")
cel = p8.groupby(["tipo_pista", "condicao_metereologica"]).agg(
    n=("acidente_fatal", "size"), f=("acidente_fatal", "sum"))
cel = cel[cel["n"] >= 50]
cel["taxa"] = cel["f"] / cel["n"]
pior = cel["taxa"].idxmax()
check(pior == ("Simples", "Nevoeiro/Neblina"), f"Q8 pior celula: {pior}",
      f"Q8 pior celula: {pior}")
check(perto(cel.loc[pior, "taxa"], 0.139535, 1e-4),
      f"Q8 pior taxa {pct(cel.loc[pior,'taxa'])}", f"Q8 pior taxa {pct(cel.loc[pior,'taxa'])}")
check(int(cel.loc[pior, "n"]) == 1075, f"Q8 pior celula n={int(cel.loc[pior,'n'])}",
      f"Q8 pior celula n={int(cel.loc[pior,'n'])}")
for tp, esp in [("Simples", 0.098279), ("Dupla", 0.046896), ("Múltipla", 0.041318)]:
    g = p8[p8["tipo_pista"] == tp]
    taxa = g["acidente_fatal"].mean()
    check(perto(taxa, esp, 1e-4), f"Q8 {tp} {pct(taxa)}", f"Q8 {tp} {pct(taxa)} != {esp}")
# Simples vs Dupla em 7/7 comparaveis
conds = sorted(set(p8.loc[p8["tipo_pista"] == "Simples", "condicao_metereologica"]) &
                set(p8.loc[p8["tipo_pista"] == "Dupla", "condicao_metereologica"]))
ganha = 0
comparaveis = 0
for c in conds:
    s = p8[(p8["tipo_pista"] == "Simples") & (p8["condicao_metereologica"] == c)]
    d = p8[(p8["tipo_pista"] == "Dupla") & (p8["condicao_metereologica"] == c)]
    if len(s) >= 50 and len(d) >= 50:
        comparaveis += 1
        if s["acidente_fatal"].mean() > d["acidente_fatal"].mean():
            ganha += 1
check(ganha == comparaveis == 7, f"Q8 Simples > Dupla em {ganha}/{comparaveis}",
      f"Q8 Simples > Dupla em {ganha}/{comparaveis}")

# -------------------------------------------------------------------- Q9
noite = df[df["fase_dia"] == "Plena Noite"]
brs = noite.groupby("br").agg(n=("acidente_fatal", "size"),
                                mortos=("mortos", "sum"),
                                fatais=("acidente_fatal", "sum"))
brs = brs[brs["n"] >= 50]
brs["taxa"] = brs["fatais"] / brs["n"]
top_m = brs.sort_values("mortos", ascending=False).head(10)
top_t = brs.sort_values("taxa", ascending=False).head(10)
inter = set(top_m.index) & set(top_t.index)
check(inter == {316}, f"Q9 interseccao dos rankings = {inter}",
      f"Q9 interseccao dos rankings = {inter}")
check(int(brs.loc[316, "n"]) == 1524, f"Q9 BR-316 n={int(brs.loc[316,'n'])}",
      f"Q9 BR-316 n={int(brs.loc[316,'n'])}")
check(int(brs.loc[316, "mortos"]) == 342, f"Q9 BR-316 mortos={int(brs.loc[316,'mortos'])}",
      f"Q9 BR-316 mortos={int(brs.loc[316,'mortos'])}")
check(perto(brs.loc[316, "taxa"], 0.204724, 1e-4),
      f"Q9 BR-316 taxa {pct(brs.loc[316,'taxa'])}",
      f"Q9 BR-316 taxa {pct(brs.loc[316,'taxa'])}")
check(len(brs) == 83, f"Q9 {len(brs)} BRs passam do filtro de 50",
      f"Q9 {len(brs)} BRs passam do filtro de 50")
check(int(noite["br"].nunique()) == 119, f"Q9 {noite['br'].nunique()} BRs presentes na noite",
      f"Q9 {noite['br'].nunique()} BRs presentes na noite")
check(int(noite["br"].nunique()) - len(brs) == 36,
      "Q9 36 das 119 BRs da noite saem pelo filtro de volume",
      f"Q9 exclui {int(noite['br'].nunique()) - len(brs)} BRs")
pct_mortes = top_m["mortos"].sum() / noite["mortos"].sum()
check(perto(pct_mortes, 0.523609, 1e-4), f"Q9 top10 = {pct_mortes*100:.2f}% das mortes noturnas",
      f"Q9 top10 = {pct_mortes*100:.2f}%")

# ------------------------------------------------------------------- Q10
q10 = df.groupby("data_comemorativa").agg(acidentes=("acidente_fatal", "size"),
                                          mortos=("mortos", "sum"),
                                          fatais=("acidente_fatal", "sum"))
q10["taxa"] = q10["fatais"] / q10["acidentes"]
dias = df.groupby("data_comemorativa")["data_inversa"].agg(lambda s: s.dt.date.nunique())
q10["ac_dia"] = q10["acidentes"] / dias
q10["mortos_dia"] = q10["mortos"] / dias
for cat, esp_taxa in [("Fim de Ano", 0.074016), ("Carnaval", 0.066275), ("Normal", 0.071603)]:
    check(perto(q10.loc[cat, "taxa"], esp_taxa, 1e-5), f"Q10 {cat} taxa {pct(q10.loc[cat,'taxa'])}",
          f"Q10 {cat} taxa {pct(q10.loc[cat,'taxa'])} != {esp_taxa}")
ac_fim = q10.loc["Fim de Ano", "ac_dia"] / q10.loc["Normal", "ac_dia"] - 1
ac_car = q10.loc["Carnaval", "ac_dia"] / q10.loc["Normal", "ac_dia"] - 1
mo_fim = q10.loc["Fim de Ano", "mortos_dia"] / q10.loc["Normal", "mortos_dia"] - 1
mo_car = q10.loc["Carnaval", "mortos_dia"] / q10.loc["Normal", "mortos_dia"] - 1
check(perto(ac_fim, 0.086830, 1e-4), f"Q10 Fim de Ano ac/dia {ac_fim*100:+.2f}%",
      f"Q10 Fim de Ano ac/dia {ac_fim*100:+.2f}%")
check(perto(mo_fim, 0.251722, 1e-4), f"Q10 Fim de Ano mortos/dia {mo_fim*100:+.2f}%",
      f"Q10 Fim de Ano mortos/dia {mo_fim*100:+.2f}%")
check(perto(ac_car, -0.005311, 1e-4), f"Q10 Carnaval ac/dia {ac_car*100:+.2f}%",
      f"Q10 Carnaval ac/dia {ac_car*100:+.2f}%")
check(perto(mo_car, -0.153724, 1e-4), f"Q10 Carnaval mortos/dia {mo_car*100:+.2f}%",
      f"Q10 Carnaval mortos/dia {mo_car*100:+.2f}%")

# ------------------------------------------------------------------- Q11
crit = df[df["mortos"] >= 3]
check(len(crit) == 437, f"Q11 {len(crit)} acidentes criticos", f"Q11 {len(crit)} criticos")
check(perto(len(crit) / N_ACID, 0.00205, 1e-4),
      f"Q11 {len(crit)/N_ACID*100:.3f}% da base", f"Q11 {len(crit)/N_ACID*100:.3f}% da base")
check(perto(crit["mortos"].sum() / N_MORTOS, 0.093591, 1e-4),
      f"Q11 {crit['mortos'].sum()/N_MORTOS*100:.2f}% das mortes",
      f"Q11 {crit['mortos'].sum()/N_MORTOS*100:.2f}% das mortes")
check(perto(crit["acidente_fatal"].sum() / N_FATAIS, 0.028575, 1e-4),
      f"Q11 {crit['acidente_fatal'].sum()/N_FATAIS*100:.2f}% dos fatais",
      f"Q11 {crit['acidente_fatal'].sum()/N_FATAIS*100:.2f}% dos fatais")
uf = crit.groupby("uf").agg(n=("acidente_fatal", "size"), mortos=("mortos", "sum"))
check(uf["mortos"].idxmax() == "MG", f"Q11 UF lidera por mortos: {uf['mortos'].idxmax()}",
      f"Q11 UF lidera: {uf['mortos'].idxmax()}")
check(int(uf.loc["MG", "n"]) == 75, f"Q11 MG n={int(uf.loc['MG','n'])}",
      f"Q11 MG n={int(uf.loc['MG','n'])}")
check(int(uf.loc["MG", "mortos"]) == 303, f"Q11 MG mortos={int(uf.loc['MG','mortos'])}",
      f"Q11 MG mortos={int(uf.loc['MG','mortos'])}")
fatais = df[df["acidente_fatal"] == 1]
def composicao(coluna):
    a = crit.groupby(coluna).size().rename("criticos")
    b = fatais.groupby(coluna).size().rename("fatais")
    c = pd.concat([a, b], axis=1).fillna(0)
    c["pct_criticos"] = c["criticos"] / c["criticos"].sum() * 100
    c["pct_fatais"] = c["fatais"] / c["fatais"].sum() * 100
    c["razao"] = c["pct_criticos"] / c["pct_fatais"]
    return c
fase_c = composicao("fase_dia")
sobre = fase_c[fase_c["razao"] > 1].sort_values("razao", ascending=False)
check(len(sobre) == 2, f"Q11 {len(sobre)} fases sobrerrepresentadas: {list(sobre.index)}",
      f"Q11 fases sobrerrepresentadas: {list(sobre.index)}")
check(perto(sobre.loc["Amanhecer", "razao"], 1.4719, 1e-3),
      f"Q11 Amanhecer razao {sobre.loc['Amanhecer','razao']:.4f}",
      f"Q11 Amanhecer razao {sobre.loc['Amanhecer','razao']:.4f}")
check(perto(sobre.loc["Pleno dia", "razao"], 1.1281, 1e-3),
      f"Q11 Pleno dia razao {sobre.loc['Pleno dia','razao']:.4f}",
      f"Q11 Pleno dia razao {sobre.loc['Pleno dia','razao']:.4f}")
tipo_c = composicao("tipo_acidente")
check(perto(tipo_c.loc["Colisão frontal", "pct_criticos"], 62.929100, 1e-4),
      f"Q11 frontal {tipo_c.loc['Colisão frontal','pct_criticos']:.2f}% dos criticos",
      f"Q11 frontal {tipo_c.loc['Colisão frontal','pct_criticos']:.2f}%")
check(perto(tipo_c.loc["Colisão frontal", "razao"], 2.27, 2e-2),
      f"Q11 frontal razao {tipo_c.loc['Colisão frontal','razao']:.2f}",
      f"Q11 frontal razao {tipo_c.loc['Colisão frontal','razao']:.2f}")
pista_c = composicao("tipo_pista")
check(perto(pista_c.loc["Simples", "pct_criticos"], 88.558400, 1e-4),
      f"Q11 Simples {pista_c.loc['Simples','pct_criticos']:.2f}%",
      f"Q11 Simples {pista_c.loc['Simples','pct_criticos']:.2f}%")
causa_c = composicao("causa_acidente")
check(perto(causa_c.loc["Transitar na contramão", "pct_criticos"], 27.002300, 1e-4),
      f"Q11 contramao {causa_c.loc['Transitar na contramão','pct_criticos']:.2f}%",
      f"Q11 contramao {causa_c.loc['Transitar na contramão','pct_criticos']:.2f}%")
check(perto(causa_c.loc["Ultrapassagem Indevida", "pct_criticos"], 15.103000, 1e-4),
      f"Q11 ultrapassagem {causa_c.loc['Ultrapassagem Indevida','pct_criticos']:.2f}%",
      f"Q11 ultrapassagem {causa_c.loc['Ultrapassagem Indevida','pct_criticos']:.2f}%")

# ------------------------------------------------------------------- Q12
pe = df[(df["uf"] == "PE") & (df["ano_acidente"].isin([2024, 2025]))]
mun = pe.groupby("municipio").agg(n=("acidente_fatal", "size"),
                                   fatais=("acidente_fatal", "sum"),
                                   mortos=("mortos", "sum"))
mun_f = mun[mun["n"] >= 50].sort_values(["fatais", "mortos", "n"], ascending=False)
top5 = mun_f.head(5)
check(list(top5.index) == ["RECIFE", "GARANHUNS", "JABOATAO DOS GUARARAPES", "CARUARU", "PETROLINA"],
      f"Q12 top5: {list(top5.index)}", f"Q12 top5: {list(top5.index)}")
check(list(top5["fatais"]) == [45, 24, 24, 24, 23],
      f"Q12 fatais: {list(top5['fatais'])}", f"Q12 fatais: {list(top5['fatais'])}")
check(int(pe["acidente_fatal"].sum()) == 590, f"Q12 PE fatais={int(pe['acidente_fatal'].sum())}",
      f"Q12 PE fatais={int(pe['acidente_fatal'].sum())}")
check(int(pe["mortos"].sum()) == 649, f"Q12 PE mortos={int(pe['mortos'].sum())}",
      f"Q12 PE mortos={int(pe['mortos'].sum())}")
check(len(pe) == 6245, f"Q12 PE acidentes={len(pe)}", f"Q12 PE acidentes={len(pe)}")

# ------------------------------------------------------------- graficos
mensal = df.groupby(df["data_inversa"].dt.to_period("M")).agg(n=("acidente_fatal", "size"),
                                                              f=("acidente_fatal", "sum"))
mensal["taxa"] = mensal["f"] / mensal["n"]
check(len(mensal) == 36, f"G2 {len(mensal)} meses", f"G2 {len(mensal)} meses")
check(perto(mensal["taxa"].max(), 0.082825, 1e-4), f"G2 max {pct(mensal['taxa'].max())}",
      f"G2 max {pct(mensal['taxa'].max())}")
check(perto(mensal["taxa"].min(), 0.063636, 1e-4), f"G2 min {pct(mensal['taxa'].min())}",
      f"G2 min {pct(mensal['taxa'].min())}")
amp2 = (mensal["taxa"].max() - mensal["taxa"].min()) * 100
check(perto(amp2, 1.9188, 1e-3), f"G2 amplitude {amp2:.4f} p.p.", f"G2 amplitude {amp2:.4f} p.p.")
check(perto(mensal["taxa"].head(12).mean(), 0.071561, 1e-5),
      f"G2 media 12 primeiros {pct(mensal['taxa'].head(12).mean())}",
      f"G2 media 12 primeiros {pct(mensal['taxa'].head(12).mean())}")
check(perto(mensal["taxa"].tail(12).mean(), 0.071744, 1e-5),
      f"G2 media 12 ultimos {pct(mensal['taxa'].tail(12).mean())}",
      f"G2 media 12 ultimos {pct(mensal['taxa'].tail(12).mean())}")

faixa = df.groupby("faixa_horaria").agg(n=("acidente_fatal", "size"),
                                         f=("acidente_fatal", "sum"))
faixa["taxa"] = faixa["f"] / faixa["n"]
check(perto(faixa.loc["03h-06h", "taxa"], 0.122634, 1e-4),
      f"G3 03h-06h {pct(faixa.loc['03h-06h','taxa'])}",
      f"G3 03h-06h {pct(faixa.loc['03h-06h','taxa'])}")
check(perto(faixa.loc["09h-12h", "taxa"], 0.049112, 1e-4),
      f"G3 09h-12h {pct(faixa.loc['09h-12h','taxa'])}",
      f"G3 09h-12h {pct(faixa.loc['09h-12h','taxa'])}")
razao3 = faixa.loc["03h-06h", "taxa"] / faixa.loc["09h-12h", "taxa"]
check(perto(razao3, 2.4970, 1e-3), f"G3 razao {razao3:.4f}", f"G3 razao {razao3:.4f}")
check(perto(faixa.loc["03h-06h", "n"] / N_ACID, 0.069284, 1e-4),
      f"G3 03h-06h = {faixa.loc['03h-06h','n']/N_ACID*100:.2f}% dos acidentes",
      f"G3 03h-06h = {faixa.loc['03h-06h','n']/N_ACID*100:.2f}%")
check(int(faixa["n"].idxmax() == faixa["n"].idxmax()) and
      faixa["n"].idxmax() == "18h-21h", f"G3 pico de volume em {faixa['n'].idxmax()}",
      f"G3 pico de volume em {faixa['n'].idxmax()}")
check(int(faixa.loc["18h-21h", "n"]) == 39758, f"G3 18h-21h n={int(faixa.loc['18h-21h','n'])}",
      f"G3 18h-21h n={int(faixa.loc['18h-21h','n'])}")

# ----------------------------------------------------------- Parte 7
p7s = df.groupby("tipo_pista").agg(n=("acidente_fatal", "size"), f=("acidente_fatal", "sum"))
p7s["taxa"] = p7s["f"] / p7s["n"]
check(perto(p7s.loc["Simples", "taxa"], 0.098867, 1e-5),
      f"P7 Simples {pct(p7s.loc['Simples','taxa'])}", f"P7 Simples {pct(p7s.loc['Simples','taxa'])}")
check(perto(p7s.loc["Dupla", "taxa"], 0.047122, 1e-5),
      f"P7 Dupla {pct(p7s.loc['Dupla','taxa'])}", f"P7 Dupla {pct(p7s.loc['Dupla','taxa'])}")
check(perto(p7s.loc["Múltipla", "taxa"], 0.041359, 1e-5),
      f"P7 Multipla {pct(p7s.loc['Múltipla','taxa'])}",
      f"P7 Multipla {pct(p7s.loc['Múltipla','taxa'])}")
raz_p7 = p7s.loc["Simples", "taxa"] / p7s.loc["Dupla", "taxa"]
check(perto(raz_p7, 2.0981, 1e-3), f"P7 razao Simples/Dupla {raz_p7:.4f}",
      f"P7 razao Simples/Dupla {raz_p7:.4f}")
raz_noite = q3.loc["Plena Noite", "taxa"] / q3.loc["Pleno dia", "taxa"]
check(perto(raz_noite, 2.0093, 1e-3), f"P7 razao noite/dia {raz_noite:.4f}",
      f"P7 razao noite/dia {raz_noite:.4f}")
dif_pp = (q3.loc["Plena Noite", "taxa"] - q3.loc["Pleno dia", "taxa"]) * 100
check(perto(dif_pp / (TAXA_GLOBAL * 100), 0.7074, 1e-3),
      f"P7 diferenca = {dif_pp/(TAXA_GLOBAL*100)*100:.2f}% da taxa global",
      f"P7 diferenca = {dif_pp/(TAXA_GLOBAL*100)*100:.2f}%")

# ---------------------------------------- numeros citados nos notebooks
for rot, val in [("taxa global", 7.16), ("frontal", 29.81), ("atropelamento", 28.96),
                  ("Plena Noite", 10.09), ("Pleno dia", 5.02), ("RR fim de semana", 1.285)]:
    check(no_texto(val, 2), f"Texto dos notebooks cita {rot} {val}",
          f"Texto dos notebooks NAO cita {rot} {val}")

print()
print(f"OK: {len(OK)}   FALHAS: {len(FALHAS)}")
if FALHAS:
    print("\n=== DIVERGENCIAS ===")
    for x in FALHAS:
        print("  X " + x)
else:
    print("\nTODOS OS NUMEROS CONFIRMADOS NA BASE")
sys.exit(1 if FALHAS else 0)
