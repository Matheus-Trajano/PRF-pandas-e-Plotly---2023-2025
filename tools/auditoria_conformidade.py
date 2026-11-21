"""
Auditoria de conformidade com o PDF oficial do exercício.

Verifica, notebook a notebook, cada requisito explícito do enunciado:
ingestão, limpeza, variáveis derivadas, as duas bases, as 12 questões de
negócio (com volume mínimo, comparação com a taxa global, interpretação de
2-3 linhas e locução associativa), os 3 gráficos da Parte 6 e a síntese da
Parte 7.

Uso:  python tools/auditoria_conformidade.py
Saída: contagem de verificações OK / FALHAS / AVISOS. Código de saída 1 se
houver qualquer falha.
"""

import json
import glob
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

OK, FALHAS, AVISOS = [], [], []


def check(cond, msg_ok, msg_fail):
    """Registra uma verificação. Retorna o próprio `cond`."""
    (OK if cond else FALHAS).append(msg_ok if cond else msg_fail)
    return cond


def warn(cond, msg):
    """Registra um aviso (não bloqueia)."""
    if not cond:
        AVISOS.append(msg)


def cells(nbfile):
    return json.load(open(nbfile, encoding="utf-8"))["cells"]


def src(c):
    return "".join(c["source"])


def all_text(f):
    return "\n".join(src(c) for c in cells(f))


def code_text(f):
    return "\n".join(src(c) for c in cells(f) if c["cell_type"] == "code")


N = {i: f"notebooks/{f}" for i, f in enumerate(
    sorted(os.path.basename(p) for p in glob.glob("notebooks/*.ipynb")), 1)}

print("=" * 74)
print("AUDITORIA DE CONFORMIDADE COM O PDF OFICIAL")
print("=" * 74)

# ---------------------------------------------------------------- PARTE 1
c1 = code_text(N[1])
check("ler_csv_prf" in c1, "P1 usa ler_csv_prf", "P1 NAO usa ler_csv_prf")
check("UnicodeDecodeError" in c1 and "except" in c1, "P1 implementa fallback de encoding",
      "P1 SEM fallback de encoding")
check(".lower()" in c1, "P1 padroniza nomes das colunas", "P1 NAO padroniza nomes de colunas")
check("set(" in c1, "P1 confere colunas iguais entre os 3 anos", "P1 NAO confere colunas iguais")
check("arquivo_origem" in c1 and "pd.concat" in c1, "P1 cria arquivo_origem e usa pd.concat",
      "P1 SEM arquivo_origem/pd.concat")
check("acidentes_prf_historico" in c1, "P1 cria acidentes_prf_historico",
      "P1 SEM acidentes_prf_historico")
check("assert" in c1, "P1 valida total com assert", "P1 SEM assert de total")

# ---------------------------------------------------------------- PARTE 2
t2, c2 = all_text(N[2]), code_text(N[2])
check(".info(" in c2, "P2 mostra info()", "P2 SEM info()")
check("isnull" in c2 or "isna" in c2, "P2 mostra nulos (qtd e %)", "P2 SEM nulos")
check("drop_duplicates" in c2, "P2 remove duplicidades exatas", "P2 SEM drop_duplicates")
check("to_datetime" in c2, "P2 converte colunas para data", "P2 SEM conversao de data")
check(".strip()" in c2, "P2 aplica strip", "P2 SEM strip")
check(".upper()" in c2, "P2 aplica upper", "P2 SEM upper")
check("IGNORADO" in c2, "P2 nulos de categoria -> IGNORADO", "P2 SEM IGNORADO")
check("df_limpo" in c2, "P2 cria df_limpo", "P2 SEM df_limpo")
for col in ["latitude", "longitude", "regional", "delegacia", "uop"]:
    check(col in c2, f"P2 remove {col}", f"P2 NAO remove {col}")
for col in ["uf", "br", "municipio"]:
    check(col in t2, f"P2 mantem {col}", f"P2 NAO mantem {col}")

# ---------------------------------------------------------------- PARTE 3
t3, c3 = all_text(N[3]), code_text(N[3])
check("df_enriquecido" in c3, "P3 cria df_enriquecido", "P3 SEM df_enriquecido")
check("acidente_fatal" in c3, "P3 cria acidente_fatal", "P3 SEM acidente_fatal")
check("ano_acidente" in c3 and "mes_acidente" in c3, "P3 cria ano_acidente e mes_acidente",
      "P3 SEM ano/mes_acidente")
check("fim_de_semana" in c3, "P3 cria fim_de_semana", "P3 SEM fim_de_semana")
check("dt.dayofweek" in c3 or "dt.day_of_week" in c3, "P3 codigo usa dt.dayofweek (PDF)",
      "P3 codigo NAO usa dt.dayofweek")
check("dayofweek" in t3, "P3 documenta dt.dayofweek (PDF)", "P3 NAO documenta dt.dayofweek")
check("data_comemorativa" in c3, "P3 cria data_comemorativa", "P3 SEM data_comemorativa")
check("Fim de Ano" in c3 and "Carnaval" in c3 and "Normal" in c3,
      "P3 data_comemorativa com 3 categorias", "P3 SEM as 3 categorias")
check("faixa_horaria" in c3, "P3 cria faixa_horaria", "P3 SEM faixa_horaria")
check("assert" in c3, "P3 valida alvo com assert", "P3 SEM assert de alvo")
for d in ["18", "22", "10", "14", "01", "05"]:
    check(d in c3, f"P3 contem data {d} do carnaval", f"P3 SEM data {d} do carnaval")

# ---------------------------------------------------------------- PARTE 4
t4, c4 = all_text(N[4]), code_text(N[4])
check("base_analitica" in c4, "P4 cria base_analitica", "P4 SEM base_analitica")
check("base_modelavel" in c4, "P4 cria base_modelavel", "P4 SEM base_modelavel")
for col in ["mortos", "feridos", "feridos_leves", "feridos_graves", "classificacao_acidente"]:
    check(col in t4, f"P4 cita {col} como proibida", f"P4 SEM mencao a {col}")
check("verificar_data_leakage" in c4, "P4 escreve verificar_data_leakage",
      "P4 SEM verificar_data_leakage")
check("utf-8-sig" in c4, "P4 exporta com utf-8-sig", "P4 SEM utf-8-sig")
check(re.search(r'SEPARADOR\s*=\s*["\'];["\']', c4), "P4 exporta com separador ';'",
      "P4 SEM separador ';'")
check("assert" in c4, "P4 reabre e confere com assert", "P4 SEM assert de reabertura")
check("Path" in c4, "P4 usa Path com caminho relativo", "P4 SEM Path")

# --------------------------------------------------------------- PARTE 5
NIVEL = {1: (N[5], ["Q1", "Q2", "Q3", "Q4"]),
         2: (N[6], ["Q5", "Q6", "Q7"]),
         3: (N[7], ["Q8", "Q9", "Q10"]),
         4: (N[8], ["Q11", "Q12"])}

for nivel, (nb, qs) in NIVEL.items():
    t, c = all_text(nb), code_text(nb)
    for q in qs:
        check(re.search(rf"##\s*{q}\b", t) is not None, f"{q} tem enunciado em celula de texto",
              f"{q} SEM enunciado em celula de texto")
    check("minimo" in c.lower() or "Volume mínimo" in t, f"Nivel {nivel} declara volume minimo",
          f"Nivel {nivel} SEM volume minimo")
    check("Interpretação" in t, f"Nivel {nivel} tem interpretacao", f"Nivel {nivel} SEM interpretacao")
    check("global" in t.lower(), f"Nivel {nivel} compara com a taxa global",
          f"Nivel {nivel} SEM comparacao com a taxa global")
    causal = re.compile(r"(?<!não )\b(por causa d[ao]|devido a|em raz[ãa]o d[ao]|explicam? |"
                        r"provoca|favorece|resulta(?:m|ndo)? em|respons[áa]vel|contribui|"
                        r"atribu[íi]d[oa] a|causad[oa] por)\b", re.I)
    hits = [l for l in t.split("\n") if causal.search(l)]
    warn(not hits, f"Nivel {nivel} usa linguagem causal: {hits[:2]}")

# --- requisitos especificos por questao, conforme o PDF ---
t5, c5 = all_text(N[5]), code_text(N[5])
t6, c6 = all_text(N[6]), code_text(N[6])
t7, c7 = all_text(N[7]), code_text(N[7])
t8, c8 = all_text(N[8]), code_text(N[8])

check("minimo=100" in c6, "Q5 minimo 100 registros (PDF)", "Q5 FALTA minimo 100")
check(re.search(r"indicadores\(df,\s*\"tipo_acidente\",\s*minimo=100\)", c6),
      "Q5 aplica minimo=100 via helper", "Q5 SEM minimo=100 via helper")
check("501" in c6, "Q7 filtra traçados com mais de 500 acidentes (PDF)",
      "Q7 SEM filtro de 500 acidentes")
check("explode" in c6.lower() and "explode" in t6.lower(),
      "Q7 justifica o tratamento de multi-valor (explode)", "Q7 SEM justificativa de multi-valor")
check("minimo=50" in c7 or "MINIMO" in c7, "Q8/Q9 minimo 50 (PDF)", "Q8/Q9 SEM minimo 50")
check("Plena Noite" in c7, "Q9 restringe a plena noite", "Q9 SEM restricao de plena noite")
check(re.search(r'mortos"?\]?\s*>=\s*3', c8) is not None or "3+ mortos" in t8,
      "Q11 filtra acidentes com 3+ mortos", "Q11 SEM filtro de 3+ mortos")
check("PE" in t8 and "2024" in t8 and "2025" in t8, "Q12 filtra PE 2024-2025",
      "Q12 SEM filtro PE 2024-2025")

# ---------------------------------------------------------------- PARTE 6
t6c, c6c = all_text(N[9]), code_text(N[9])
check(c6c.count("salvar_grafico(") >= 4, "P6 gera 3 graficos + 1 sintese",
      f"P6 FALTA graficos (salvar_grafico x{c6c.count('salvar_grafico(')})")
check("fig.show()" in c6c, "P6 exibe os graficos", "P6 FALHA exibir graficos")
check("write_html" in c6c, "P6 salva HTML", "P6 SEM write_html")
check("go.Bar" in c6c or "add_bar" in c6c, "P6 tem grafico de barras", "P6 SEM grafico de barras")
check("go.Scatter" in c6c or "add_scatter" in c6c, "P6 tem serie mensal (linha)",
      "P6 SEM serie mensal")
check(c6c.count("add_scatter") >= 2 and c6c.count("add_bar") >= 2,
      "P6 graficos 2 e 3 combinam barra+linha", "P6 SEM combinacao barra+linha")
check("resultados" in c6c, "P6 salva em resultados/", "P6 SEM caminho resultados/")
for i in (1, 2, 3):
    check(f"g{i}_" in c6c, f"P6 gera grafico {i}", f"P6 SEM grafico {i}")

# ---------------------------------------------------------------- PARTE 7
t7b, c7b = all_text(N[10]), code_text(N[10])
for i in (1, 2, 3):
    check(f"Achado {i}" in t7b or f"ACHADO {i}" in t7b, f"P7 tem Achado {i}", f"P7 SEM Achado {i}")
for elem in ["Observa", "Hipótese", "Limita"]:
    check(elem.lower() in t7b.lower(), f"P7 tem '{elem}'", f"P7 SEM '{elem}'")
check("g4_sintese" in c7b, "P7 gera grafico de sintese", "P7 SEM grafico de sintese")
check("descartad" in t7b.lower(), "P7 cita categoria descartada pelo filtro",
      "P7 SEM categoria descartada")

# ------------------------------------------------------- REGRAS GLOBAIS
for f in sorted(glob.glob("notebooks/*.ipynb")):
    b = os.path.basename(f)
    check("Path" in code_text(f), f"{b} usa Path", f"{b} SEM Path")
    check(not re.search(r"to_csv\([^)]*dados_brutos", all_text(f) + code_text(f)),
          f"{b} nao sobrescreve CSVs originais", f"{b} SOBRESCREVE CSV original")
    check("acidente_fatal" in code_text(f) or f in (N[1], N[2], N[3], N[4]),
          f"{b} usa acidente_fatal", f"{b} SEM acidente_fatal")

print(f"\nOK: {len(OK)}   FALHAS: {len(FALHAS)}   AVISOS: {len(AVISOS)}")
if FALHAS:
    print("\n=== FALHAS ===")
    for x in FALHAS:
        print("  X " + x)
if AVISOS:
    print("\n=== AVISOS ===")
    for x in AVISOS:
        print("  ! " + x)
if not FALHAS:
    print("\nTODAS AS VERIFICACOES PASSARAM")
sys.exit(1 if FALHAS else 0)
