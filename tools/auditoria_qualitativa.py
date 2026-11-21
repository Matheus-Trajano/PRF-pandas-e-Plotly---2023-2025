"""
Auditoria qualitativa: linguagem causal, tamanho das interpretacoes,
coerencia entre README e notebooks e integridade do repositorio.

Uso:  python tools/auditoria_qualitativa.py
"""

import glob
import hashlib
import json
import os
import re
import subprocess
import sys
import textwrap

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

OK, FALHAS, AVISOS = [], [], []


def check(cond, msg_ok, msg_fail):
    (OK if cond else FALHAS).append(msg_ok if cond else msg_fail)
    return cond


def warn(cond, msg):
    if not cond:
        AVISOS.append(msg)


def cells(f):
    return json.load(open(f, encoding="utf-8"))["cells"]


def src(c):
    return "".join(c["source"])


def all_text(f):
    return "\n".join(src(c) for c in cells(f))


def md_cells(f):
    return [src(c) for c in cells(f) if c["cell_type"] == "markdown"]


print("=" * 74)
print("AUDITORIA QUALITATIVA")
print("=" * 74)

# ------------------------------------------- 1. LINGUAGEM CAUSAL (PDF)
print("\n[1] Linguagem causal na Parte 5 (PDF: 'sem linguagem causal, use associado a')")
TERMOS = [r"\bpor causa d[ao]\b", r"\bdevido a\b", r"\bem raz[ãa]o d[ao]\b",
          r"\bexplicam?\b", r"\bprovoca\w*\b", r"\bfavorece\w*\b",
          r"\bresulta(?:m|ndo)? em\b", r"\brespons[áa]vel\b", r"\bcontribui\b",
          r"\batribu[íi]d[oa] a\b", r"\bcausad[oa] por\b", r"\bque eleva\b",
          r"\bquem eleva\b", r"\bfaz com que\b", r"\bpor conta d[ao]\b"]
rx = re.compile("|".join(TERMOS), re.I)
# construcoes metalinguisticas (nao sao linguagem causal): negacoes e metadiscurso
METALING = re.compile(r"(não|nao|nem|sem)\s+\w{0,12}\s*(explica|provoca|atribui)|"
                       r"não (separa|isola|permite|comprova|demonstra)", re.I)
n_cao = 0
for f in sorted(glob.glob("notebooks/0[5-8]*.ipynb")):
    b = os.path.basename(f)
    for i, t in enumerate(md_cells(f)):
        for line in t.split("\n"):
            for m in rx.finditer(line):
                if METALING.search(line):
                    continue
                n_cao += 1
                print(f"    {b} celula-md {i}: ...{line[max(0,m.start()-60):m.end()+60]}...")
check(n_cao == 0, "Nenhuma linguagem causal na Parte 5",
      f"{n_cao} ocorrencia(s) de linguagem causal na Parte 5")

# ------------------------------------------- 2. LOCUCAO "ASSOCIADO A"
print("\n[2] Locucao 'associado a' presente em cada notebook da Parte 5")
for f in sorted(glob.glob("notebooks/0[5-8]*.ipynb")):
    b = os.path.basename(f)
    t = all_text(f)
    k = sum(t.count(x) for x in ("associado a", "associada a", "associadas a", "associado à"))
    check(k > 0, f"{b}: {k} ocorrencia(s) de 'associado a'", f"{b}: SEM 'associado a'")

# concordancia: "associado a" (masc) nao pode acompanhar substantivo feminino
print("\n[2b] Concordancia da locucao 'associado a'")
FEMININOS = ["diferença", "concentração", "concentracao", "taxa", "mortalidade",
             "letalidade", "severidade", "intensidade", "frequência", "proporção",
             "ocorrência", "ocorrencia", "leitura", "distribuição"]
n_conc = 0
for f in sorted(glob.glob("notebooks/0[5-8]*.ipynb")):
    b = os.path.basename(f)
    t = all_text(f)
    # so conta quando o substantivo feminino e o sujeito direto do verbo:
    # "<feminino> está **associado a**" (dois-pontos separam clausulas e nao contam)
    for fem in FEMININOS:
        for m in re.finditer(
                rf"\b{fem}\b\s+(?:está|esta|sao|são|fica|ficam|foram|permanece|permanecem)\s+"
                rf"\*{{0,2}}associado\s+a", t, re.I):
            n_conc += 1
            print(f"    {b}: '{m.group(0)[:70]}' — deveria ser 'associada a'")
check(n_conc == 0, "Nenhum desvio de concordancia em 'associado a'",
      f"{n_conc} desvio(s) de concordancia")

# ------------------------------------------- 3. TAMANHO DAS INTERPRETACOES
print("\n[3] Tamanho das interpretacoes (PDF: 'escreva 2 ou 3 linhas de interpretacao')")
n_interp = 0
for f in sorted(glob.glob("notebooks/0[5-8]*.ipynb")):
    b = os.path.basename(f)
    for t in md_cells(f):
        if "**Interpretação.**" not in t:
            continue
        n_interp += 1
        corpo = t.split("**Interpretação.**", 1)[1]
        prosa = "\n".join(l for l in corpo.split("\n")
                          if not l.strip().startswith(("|", ">")))
        linhas = len(textwrap.wrap(" ".join(prosa.split()), width=90))
        frases = len([s for s in prosa.replace("\n", " ").split(".") if s.strip()])
        ok = linhas <= 5
        check(ok, f"{b}: interpretacao com {linhas} linha(s) visualizadas",
              f"{b}: interpretacao com {linhas} linha(s) — acima de 5")
        print(f"    {b:30} {linhas} linha(s), {frases} frase(s)")
check(n_interp == 12, f"{n_interp}/12 questoes com interpretacao",
      f"Apenas {n_interp}/12 questoes com interpretacao")

# ------------------------------------------- 4. VOLUME MINIMO E TAXA GLOBAL
print("\n[4] Volume minimo e comparacao com a taxa global, por questao")
for f in sorted(glob.glob("notebooks/0[5-8]*.ipynb")):
    b = os.path.basename(f)
    t = all_text(f)
    for q in re.findall(r"##\s*(Q\d+)", t):
        bloco = t.split(f"## {q}", 1)[1]
        bloco = bloco.split("## Q", 1)[0]
        tem_min = re.search(r"[Mm]ínimo|Volume mínimo|mínimo|minimo", bloco) is not None
        # a comparacao com a global pode ser explicita ("global"), pelo valor
        # da taxa global (7,16%) ou pelo lift (taxa do grupo / taxa global)
        tem_global = re.search(r"global|7,16|lift", bloco, re.I) is not None
        check(tem_min, f"{q} declara volume minimo", f"{q} NAO declara volume minimo")
        check(tem_global, f"{q} compara com a taxa global", f"{q} NAO compara com a taxa global")

# ------------------------------------------- 5. ENUNCIADO ANTES DE CADA QUESTAO
print("\n[5] Pergunta escrita em celula de texto antes de cada questao (PDF, avaliacao)")
for f in sorted(glob.glob("notebooks/0[5-8]*.ipynb")):
    b = os.path.basename(f)
    for t in md_cells(f):
        m = re.match(r"##\s*(Q\d+)\b", t.strip())
        if not m:
            continue
        corpo = t.split("\n", 1)[1] if "\n" in t else ""
        tem_interrogacao = "?" in corpo
        check(tem_interrogacao, f"{m.group(1)} tem pergunta enunciada",
              f"{m.group(1)} SEM pergunta enunciada (sem '?')")

# ------------------------------------------- 6. COERENCIA README x NOTEBOOKS
print("\n[6] Coerencia entre README e notebooks")
readme = open("README.md", encoding="utf-8").read()
txt_nb = "\n".join(all_text(f) for f in sorted(glob.glob("notebooks/*.ipynb")))
for rot, val in [("taxa global", "7,16"), ("Q1 2023", "7,17"), ("Q5 frontal", "29,81"),
                 ("Q5 atropelamento", "28,96"), ("Q3 noite", "10,09"), ("Q3 dia", "5,02"),
                 ("Q4 RR", "1,285"), ("Q10 fim de ano", "7,40"), ("Q12 Recife", "45"),
                 ("Q11 criticos", "437"), ("Q11 MG", "303")]:
    check(val in readme, f"README cita {rot} = {val}", f"README NAO cita {rot} = {val}")
    check(val in txt_nb, f"Notebooks citam {rot} = {val}", f"Notebooks NAO citam {rot} = {val}")

# todo percentual citado no README precisa existir tambem nos notebooks
# (o README nao precisa repetir cada numero, mas nao pode contradizer)
nums = set(re.findall(r"\d+,\d+(?=\s?%)", readme))
nums |= set(re.findall(r"lift \*?\*?(\d+,\d+)", readme))
contradicoes = []
for n in sorted(nums):
    # o notebook pode escrever o numero com ou sem formatacao (% em negrito, etc.)
    if n not in txt_nb and n + "%" not in txt_nb:
        contradicoes.append(n)
check(not contradicoes, f"Todos os {len(nums)} numeros do README batem com os notebooks",
      f"README com numeros nao encontrados nos notebooks: {contradicoes}")

# frases antigas que nao podem mais existir
proibidas = ["com metade do volume", "não se distingue de dia normal",
             "é a única fase sobrerrepresentada", "quase um terço", "Panelás",
             "apenas Amanhecer", "rampas favorecem", "Quem eleva a taxa"]
for p in proibidas:
    check(p not in txt_nb, f"Frase antiga removida: {p!r}", f"Frase antiga AINDA PRESENTE: {p!r}")
    check(p not in readme, f"README sem frase antiga: {p!r}", f"README com frase antiga: {p!r}")

# ------------------------------------------- 7. INTEGRIDADE DO REPOSITORIO
print("\n[7] Integridade do repositorio")
status = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True).stdout
tracked = [l for l in status.split("\n") if l and not l.startswith("??")]
ESPERADOS = ("README.md", "notebooks/", "tools/", ".gitignore",
             "dados_brutos/", "dados_tratados/", "resultados/")
inesperados = [l for l in tracked if not any(e in l for e in ESPERADOS)]
check(not inesperados, "Nenhum arquivo inesperado modificado",
      f"Modificados inesperadamente: {inesperados}")

# o repositorio e autocontido: dados, bases e resultados versionados
esperados = ["dados_brutos/datatran2023.csv", "dados_brutos/datatran2024.csv",
             "dados_brutos/datatran2025.csv",
             "dados_tratados/base_analitica_prf_2023_2025.csv",
             "dados_tratados/base_modelavel_prf_2023_2025.csv",
             "resultados/g1_taxa_por_tipo_acidente.html",
             "resultados/g2_serie_mensal.html",
             "resultados/g3_faixa_horaria.html",
             "resultados/g4_sintese_achados.html"]
r = subprocess.run(["git", "ls-files", "dados_brutos", "dados_tratados", "resultados"],
                   capture_output=True, text=True)
versionados = {l for l in r.stdout.split("\n") if l and not l.endswith(".gitkeep")}
faltando = [d for d in esperados if d not in versionados]
check(not faltando, "Dados, bases e resultados versionados no repositorio",
      f"Nao versionados (o repo deve ser autocontido): {faltando}")
# e nenhum deles pode estar ignorado pelo .gitignore
for d in esperados:
    r = subprocess.run(["git", "check-ignore", "-q", d], capture_output=True)
    check(r.returncode != 0, f"{d} nao esta no .gitignore", f"{d} esta no .gitignore")
# integridade dos CSVs originais: MD5 igual ao publicado pela PRF
MD5_OFICIAL = {
    "dados_brutos/datatran2023.csv": "0a7c200814c6bef67f05c86adc73a882",
    "dados_brutos/datatran2024.csv": "b55ee95f37b24dc2489ce201e1b11ae6",
    "dados_brutos/datatran2025.csv": "49b9b890080023274870a68d326a9e54",
}
for arquivo, md5_esperado in MD5_OFICIAL.items():
    md5 = hashlib.md5(open(arquivo, "rb").read()).hexdigest()
    check(md5 == md5_esperado, f"{arquivo} com MD5 oficial ({md5})",
          f"{arquivo} MD5 {md5} != oficial {md5_esperado}")

# o gerador reproduz o codigo dos notebooks (outputs nao contam)
def assinatura():
    out = {}
    for f in sorted(glob.glob("notebooks/*.ipynb")):
        nb = json.load(open(f, encoding="utf-8"))
        # o `source` pode ser serializado como lista de linhas ou string unica;
        # normaliza para comparar o conteudo renderizado, nao a serializacao
        out[os.path.basename(f)] = [
            (c["cell_type"], "".join(c.get("source", []))) for c in nb["cells"]]
    return out

antes = assinatura()
# backup dos arquivos: o gerador emite notebooks SEM outputs, e a convencao do
# repositorio e versionar com outputs — entao o original precisa ser restaurado
originais = {f: open(f, "rb").read() for f in sorted(glob.glob("notebooks/*.ipynb"))}
r = subprocess.run([sys.executable, "tools/build_notebooks.py"], capture_output=True, text=True)
check(r.returncode == 0, "Gerador roda sem erro", f"Gerador falhou: {r.stderr[-300:]}")
depois = assinatura()
diferencas = [k for k in antes if antes[k] != depois.get(k)]
check(not diferencas, "Gerador reproduz identico o conteudo dos notebooks",
      f"Gerador alterou: {diferencas}")
for f, dados in originais.items():
    with open(f, "wb") as fh:
        fh.write(dados)
print("    (notebooks restaurados com os outputs)")

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
