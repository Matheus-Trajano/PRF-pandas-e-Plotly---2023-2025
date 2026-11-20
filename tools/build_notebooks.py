#!/usr/bin/env python3
"""Gera os notebooks do exercício (um por parte). Uso: python tools/build_notebooks.py"""
import json
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DIR_NB = RAIZ / "notebooks"


def md(*linhas):
    return {"cell_type": "markdown", "metadata": {}, "source": list(linhas)}


def code(*linhas):
    return {"cell_type": "code", "execution_count": None, "metadata": {},
            "outputs": [], "source": list(linhas)}


def md_txt(texto: str) -> dict:
    """Célula de markdown a partir de um texto corrido (uma linha por elemento)."""
    linhas = texto.strip("\n").split("\n")
    return {"cell_type": "markdown", "metadata": {},
            "source": [l + "\n" for l in linhas[:-1]] + [linhas[-1]]}


def code_txt(texto: str) -> dict:
    """Célula de código a partir de um texto corrido (uma linha por elemento)."""
    linhas = texto.strip("\n").split("\n")
    return {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [],
            "source": [l + "\n" for l in linhas[:-1]] + [linhas[-1]]}


def gravar(nome, cells):
    nb = {
        "cells": cells,
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "version": "3.11"},
        },
        "nbformat": 4, "nbformat_minor": 5,
    }
    destino = DIR_NB / nome
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"gerado: {destino.relative_to(RAIZ)} ({len(cells)} células)")


# ---------------------------------------------------------------- código comum
SETUP = code(
    "import unicodedata\n",
    "from pathlib import Path\n",
    "\n",
    "import numpy as np\n",
    "import pandas as pd\n",
    "\n",
    "\n",
    "def localizar_raiz() -> Path:\n",
    "    for candidato in [Path.cwd(), *Path.cwd().parents]:\n",
    "        if (candidato / \"dados_brutos\").is_dir():\n",
    "            return candidato\n",
    "    raise FileNotFoundError(\"Abra o notebook da raiz do projeto ou de 'notebooks/'.\")\n",
    "\n",
    "\n",
    "RAIZ = localizar_raiz()\n",
    "DIR_BRUTOS = RAIZ / \"dados_brutos\"\n",
    "DIR_TRATADOS = RAIZ / \"dados_tratados\"\n",
    "DIR_RESULTADOS = RAIZ / \"resultados\"\n",
    "for pasta in (DIR_TRATADOS, DIR_RESULTADOS):\n",
    "    pasta.mkdir(parents=True, exist_ok=True)\n",
    "\n",
    "SEPARADOR = \";\"\n",
    "ENCODING_SAIDA = \"utf-8-sig\"\n",
    "ANOS = (2023, 2024, 2025)\n",
    "print(RAIZ)\n",
)

LER = code(
    "def ler_csv_prf(caminho: Path) -> pd.DataFrame:\n",
    "    \"\"\"Lê o CSV tentando vários encodings; só falha se todos falharem.\"\"\"\n",
    "    for encoding in (\"utf-8\", \"latin1\", \"utf-8-sig\", \"cp1252\"):\n",
    "        try:\n",
    "            df = pd.read_csv(caminho, sep=SEPARADOR, encoding=encoding,\n",
    "                             low_memory=False, dtype={\"id\": \"string\"})\n",
    "        except (UnicodeDecodeError, UnicodeError):\n",
    "            continue\n",
    "        print(f\"{caminho.name}: encoding={encoding}, {len(df):,} linhas\")\n",
    "        return df\n",
    "    raise RuntimeError(f\"Nenhum encoding funcionou para {caminho}\")\n",
    "\n",
    "\n",
    "def normalizar_nome(nome: str) -> str:\n",
    "    nome = str(nome).strip().lower()\n",
    "    nome = unicodedata.normalize(\"NFKD\", nome).encode(\"ascii\", \"ignore\").decode()\n",
    "    return nome.replace(\" \", \"_\").replace(\"-\", \"_\").replace(\"/\", \"_\").strip(\"_\")\n",
)


# ---------------------------------------------------------------- Parte 1
def notebook_parte1():
    return [
        md("# Parte 1 — Ingestão e integração\n",
           "\n",
           "Leitura dos três CSVs da PRF, padronização dos nomes de coluna, conferência de schema\n",
           "e união numa base única, com prova de que nenhuma linha foi perdida.\n"),

        md("## 1.1 Setup\n"),
        SETUP,

        md("## 1.2 Leitura dos três CSVs (`ler_csv_prf` com fallback de encoding)\n",
           "\n",
           "`utf-8` falha nos três arquivos da PRF, então o fallback para `latin1` é realmente usado.\n",
           "`id` é lido como texto porque em 2024 há uma linha com `id = \"6e+05\"` (veio de planilha).\n"),
        LER,
        code(
            "dados_por_ano = {ano: ler_csv_prf(DIR_BRUTOS / f\"datatran{ano}.csv\") for ano in ANOS}\n",
        ),

        md("## 1.3 Padronização de colunas e conferência entre os anos\n"),
        code(
            "for df in dados_por_ano.values():\n",
            "    df.columns = [normalizar_nome(c) for c in df.columns]\n",
            "\n",
            "colunas = {ano: set(df.columns) for ano, df in dados_por_ano.items()}\n",
            "assert set.intersection(*colunas.values()) == set.union(*colunas.values()), \\\n",
            "    \"Há coluna que não existe em todos os anos\"\n",
            "print(f\"Colunas: {sorted(colunas[2023])}\")\n",
        ),

        md("## 1.4 `arquivo_origem` e `concat` em `acidentes_prf_historico`\n"),
        code(
            "for ano, df in dados_por_ano.items():\n",
            "    df[\"arquivo_origem\"] = ano\n",
            "\n",
            "acidentes_prf_historico = pd.concat(\n",
            "    [dados_por_ano[ano] for ano in ANOS], ignore_index=True\n",
            ")\n",
            "print(acidentes_prf_historico.shape)\n",
        ),

        md("## 1.5 `assert` do total de linhas\n",
           "\n",
           "Verificado **antes** da remoção de duplicatas da Parte 2.\n"),
        code(
            "soma = sum(len(df) for df in dados_por_ano.values())\n",
            "assert len(acidentes_prf_historico) == soma\n",
            "print(f\"{soma:,} linhas = 67.766 + 73.202 + 72.529\")\n",
            "print(f\"Fatais: {int((acidentes_prf_historico['mortos'] >= 1).sum()):,}\")\n",
        ),
    ]


# ---------------------------------------------------------------- Parte 2
def notebook_parte2():
    return [
        md("# Parte 2 — Diagnóstico e limpeza\n",
           "\n",
           "Diagnóstico da base, conversão de tipos, padronização de textos e remoção das colunas\n",
           "de localidade fina.\n"),

        md("## 2.0 Setup e reconstrução da base\n",
           "\n",
           "Este notebook é autônomo: refaz a leitura da Parte 1 para poder rodar isolado.\n"),
        SETUP,
        LER,
        code(
            "dados_por_ano = {}\n",
            "for ano in ANOS:\n",
            "    df = ler_csv_prf(DIR_BRUTOS / f\"datatran{ano}.csv\")\n",
            "    df.columns = [normalizar_nome(c) for c in df.columns]\n",
            "    df[\"arquivo_origem\"] = ano\n",
            "    dados_por_ano[ano] = df\n",
            "\n",
            "acidentes_prf_historico = pd.concat(\n",
            "    [dados_por_ano[ano] for ano in ANOS], ignore_index=True\n",
            ")\n",
            "print(acidentes_prf_historico.shape)\n",
        ),

        md("## 2.1 Diagnóstico: `info()`, nulos e duplicidades\n"),
        code(
            "acidentes_prf_historico.info(memory_usage=\"deep\", show_counts=True)\n",
        ),
        code(
            "nulos = pd.DataFrame({\n",
            "    \"qtd\": acidentes_prf_historico.isna().sum(),\n",
            "    \"pct\": acidentes_prf_historico.isna().mean().mul(100).round(3),\n",
            "}).query(\"qtd > 0\").sort_values(\"qtd\", ascending=False)\n",
            "display(nulos)\n",
        ),
        code(
            "duplicadas = int(acidentes_prf_historico.duplicated().sum())\n",
            "df_deduplicado = acidentes_prf_historico.drop_duplicates().copy()\n",
            "print(f\"Duplicidades exatas: {duplicadas} | linhas removidas: \"\n",
            "      f\"{len(acidentes_prf_historico) - len(df_deduplicado)}\")\n",
        ),

        md("## 2.2 Conversão de tipos\n",
           "\n",
           "Decimal com vírgula nas numéricas e `data_inversa` em **ISO** (`yyyy-mm-dd`) —\n",
           "`%d/%m/%Y` viraria tudo `NaT`.\n"),
        code(
            "NUMERICAS = [\"br\", \"km\", \"pessoas\", \"mortos\", \"feridos\", \"feridos_leves\",\n",
            "             \"feridos_graves\", \"ilesos\", \"ignorados\", \"veiculos\",\n",
            "             \"latitude\", \"longitude\"]\n",
            "\n",
            "df_limpo = df_deduplicado.copy()\n",
            "for coluna in NUMERICAS:\n",
            "    texto = df_limpo[coluna].astype(\"string\").str.replace(\",\", \".\", regex=False)\n",
            "    df_limpo[coluna] = pd.to_numeric(texto, errors=\"coerce\")\n",
            "\n",
            "df_limpo[\"data_inversa\"] = pd.to_datetime(\n",
            "    df_limpo[\"data_inversa\"], format=\"%Y-%m-%d\", errors=\"coerce\"\n",
            ")\n",
            "\n",
            "# nenhum valor pode ter virado nulo na conversão\n",
            "faltando = df_limpo[NUMERICAS + [\"data_inversa\"]].isna().sum()\n",
            "assert faltando.sum() == 0, f\"Conversão perdeu valores:\\n{faltando[faltando > 0]}\"\n",
            "print(\"Conversão ok — nenhum valor perdido.\")\n",
        ),

        md("## 2.3 Verificação de linhas inválidas ou nulas\n",
           "\n",
           "Verificação simples: cada coluna categórica é comparada com o domínio esperado.\n",
           "Linha com valor **nulo** ou **fora do domínio** → `IGNORADO`.\n"),
        code(
            "DOMINIOS = {\n",
            "    \"uf\": {\"AC\",\"AL\",\"AM\",\"AP\",\"BA\",\"CE\",\"DF\",\"ES\",\"GO\",\"MA\",\"MG\",\"MS\",\n",
            "           \"MT\",\"PA\",\"PB\",\"PE\",\"PI\",\"PR\",\"RJ\",\"RN\",\"RO\",\"RR\",\"RS\",\"SC\",\n",
            "           \"SE\",\"SP\",\"TO\"},\n",
            "    \"fase_dia\": {\"Amanhecer\", \"Anoitecer\", \"Plena Noite\", \"Pleno dia\"},\n",
            "    \"tipo_pista\": {\"Dupla\", \"Múltipla\", \"Simples\"},\n",
            "    \"uso_solo\": {\"Não\", \"Sim\"},\n",
            "    \"sentido_via\": {\"Crescente\", \"Decrescente\", \"Não Informado\"},\n",
            "    \"classificacao_acidente\": {\"Com Vítimas Fatais\", \"Com Vítimas Feridas\", \"Sem Vítimas\"},\n",
            "    \"dia_semana\": {\"domingo\", \"segunda-feira\", \"terça-feira\", \"quarta-feira\",\n",
            "                   \"quinta-feira\", \"sexta-feira\", \"sábado\"},\n",
            "}\n",
        ),
        code(
            "# limpeza de espaços e invisíveis em todas as colunas de texto\n",
            "ajustadas = 0\n",
            "for coluna in df_limpo.columns:\n",
            "    if str(df_limpo[coluna].dtype) in (\"object\", \"string\", \"str\"):\n",
            "        antes = df_limpo[coluna]\n",
            "        depois = (antes.astype(\"string\")\n",
            "                  .str.replace(r\"[\\u00a0\\u200b]\", \" \", regex=True)\n",
            "                  .str.strip()\n",
            "                  .str.replace(r\"\\s{2,}\", \" \", regex=True))\n",
            "        ajustadas += int((antes.notna() & (antes != depois)).sum())\n",
            "        df_limpo[coluna] = depois\n",
            "\n",
            "# o enunciado pede padronizar textos com strip + upper. Os identificadores\n",
            "# (uf, br, municipio) já vêm em caixa alta da fonte, então o upper aqui é\n",
            "# explícito e inócuo; a guarda de dtype evita tocar em `br`, que é numérico.\n",
            "# As colunas descritivas (tipo_acidente, causa_acidente, fase_dia...) mantêm a\n",
            "# caixa publicada pela PRF — é a forma usada nos rótulos de todo o relatório.\n",
            "for coluna in (\"uf\", \"br\", \"municipio\"):\n",
            "    if coluna in df_limpo.columns and str(df_limpo[coluna].dtype) in (\"object\", \"string\", \"str\"):\n",
            "        df_limpo[coluna] = df_limpo[coluna].astype(\"string\").str.upper()\n",
            "\n",
            "print(f\"Espaços padronizados em {ajustadas} linhas.\")\n",
        ),
        code(
            "# nulo ou fora do domínio -> IGNORADO\n",
            "correcoes = []\n",
            "for coluna, dominio in DOMINIOS.items():\n",
            "    invalidas = df_limpo[coluna].isna() | ~df_limpo[coluna].isin(dominio)\n",
            "    n_nulos = int(df_limpo[coluna].isna().sum())\n",
            "    n_invalidos = int(invalidas.sum()) - n_nulos\n",
            "    df_limpo.loc[invalidas, coluna] = \"IGNORADO\"\n",
            "    correcoes.append({\"coluna\": coluna, \"nulos\": n_nulos, \"invalidos\": n_invalidos})\n",
            "\n",
            "log = pd.DataFrame(correcoes).query(\"nulos > 0 or invalidos > 0\")\n",
            "display(log if len(log) else \"Nenhuma linha nula ou inválida.\")\n",
        ),
        code(
            "# conferência: nada pode ter sobrado nulo ou inválido\n",
            "# 'IGNORADO' passa a ser um valor aceito em qualquer categórica\n",
            "restantes = {\n",
            "    c: int((df_limpo[c].isna() | ~df_limpo[c].isin(d | {\"IGNORADO\"})).sum())\n",
            "    for c, d in DOMINIOS.items()\n",
            "}\n",
            "assert sum(restantes.values()) == 0, f\"Sobrou valor inválido: {restantes}\"\n",
            "print(\"OK — nenhuma linha nula ou inválida nas categóricas.\")\n",
        ),
        code(
            "# contagens sem nulo\n",
            "CONTAGEM = [\"pessoas\", \"mortos\", \"feridos\", \"feridos_leves\",\n",
            "            \"feridos_graves\", \"ilesos\", \"ignorados\", \"veiculos\"]\n",
            "for c in CONTAGEM:\n",
            "    df_limpo[c] = df_limpo[c].fillna(0).astype(\"int64\")\n",
            "assert df_limpo[CONTAGEM].isna().sum().sum() == 0\n",
            "print(\"Contagens sem nulo.\")\n",
        ),

        md("## 2.4 Remoção das colunas de localidade fina\n",
           "\n",
           "Saem `latitude`, `longitude`, `regional`, `delegacia`, `uop`. Ficam `uf`, `br`, `municipio`.\n"),
        code(
            "REMOVER = [\"latitude\", \"longitude\", \"regional\", \"delegacia\", \"uop\"]\n",
            "linhas_antes = len(df_limpo)\n",
            "df_limpo = df_limpo.drop(columns=[c for c in REMOVER if c in df_limpo.columns])\n",
            "\n",
            "assert len(df_limpo) == linhas_antes, \"A remoção de colunas alterou o número de linhas\"\n",
            "assert {\"uf\", \"br\", \"municipio\"} <= set(df_limpo.columns)\n",
            "print(f\"Colunas: {df_limpo.shape[1]} | Linhas: {len(df_limpo):,}\")\n",
            "print(sorted(df_limpo.columns))\n",
        ),

        md("## 2.5 Resumo\n"),
        code(
            "print(f\"Linhas preservadas : {len(df_limpo):,}\")\n",
            "print(f\"Colunas            : {df_limpo.shape[1]}\")\n",
            "print(f\"Acidentes fatais   : {int((df_limpo['mortos'] >= 1).sum()):,}\")\n",
            "print(f\"Total de mortos    : {int(df_limpo['mortos'].sum()):,}\")\n",
        ),
    ]


# ---------------------------------------------------------------- Parte 3
def notebook_parte3():
    return [
        md("# Parte 3 — Novas variáveis\n",
           "\n",
           "Cria `df_enriquecido` com as variáveis derivadas do exercício e valida o alvo.\n"),

        md("## 3.0 Base tratada (refaz a Parte 2)\n",
           "\n",
           "Notebook autônomo: reconstrói `df_limpo` para poder rodar isolado.\n"),
        SETUP,
        LER,
        code(
            "dados_por_ano = {}\n",
            "for ano in ANOS:\n",
            "    df = ler_csv_prf(DIR_BRUTOS / f\"datatran{ano}.csv\")\n",
            "    df.columns = [normalizar_nome(c) for c in df.columns]\n",
            "    df[\"arquivo_origem\"] = ano\n",
            "    dados_por_ano[ano] = df\n",
            "\n",
            "df_limpo = pd.concat([dados_por_ano[a] for a in ANOS], ignore_index=True)\n",
            "df_limpo = df_limpo.drop_duplicates()\n",
            "\n",
            "NUMERICAS = [\"br\", \"km\", \"pessoas\", \"mortos\", \"feridos\", \"feridos_leves\",\n",
            "             \"feridos_graves\", \"ilesos\", \"ignorados\", \"veiculos\"]\n",
            "for c in NUMERICAS:\n",
            "    df_limpo[c] = pd.to_numeric(\n",
            "        df_limpo[c].astype(\"string\").str.replace(\",\", \".\", regex=False), errors=\"coerce\"\n",
            "    )\n",
            "df_limpo[\"data_inversa\"] = pd.to_datetime(\n",
            "    df_limpo[\"data_inversa\"], format=\"%Y-%m-%d\", errors=\"coerce\"\n",
            ")\n",
            "\n",
            "for c in df_limpo.columns:\n",
            "    if str(df_limpo[c].dtype) in (\"object\", \"string\", \"str\"):\n",
            "        df_limpo[c] = (df_limpo[c].astype(\"string\").str.strip()\n",
            "                       .str.replace(r\"\\s{2,}\", \" \", regex=True))\n",
            "\n",
            "# strip + upper nos identificadores (já vêm em caixa alta da fonte); as\n",
            "# descritivas mantêm a caixa publicada pela PRF.\n",
            "for c in (\"uf\", \"br\", \"municipio\"):\n",
            "    if c in df_limpo.columns and str(df_limpo[c].dtype) in (\"object\", \"string\", \"str\"):\n",
            "        df_limpo[c] = df_limpo[c].astype(\"string\").str.upper()\n",
            "\n",
            "DOMINIOS = {\n",
            "    \"uf\": {\"AC\",\"AL\",\"AM\",\"AP\",\"BA\",\"CE\",\"DF\",\"ES\",\"GO\",\"MA\",\"MG\",\"MS\",\n",
            "           \"MT\",\"PA\",\"PB\",\"PE\",\"PI\",\"PR\",\"RJ\",\"RN\",\"RO\",\"RR\",\"RS\",\"SC\",\n",
            "           \"SE\",\"SP\",\"TO\"},\n",
            "    \"fase_dia\": {\"Amanhecer\", \"Anoitecer\", \"Plena Noite\", \"Pleno dia\"},\n",
            "    \"tipo_pista\": {\"Dupla\", \"Múltipla\", \"Simples\"},\n",
            "    \"uso_solo\": {\"Não\", \"Sim\"},\n",
            "    \"sentido_via\": {\"Crescente\", \"Decrescente\", \"Não Informado\"},\n",
            "    \"classificacao_acidente\": {\"Com Vítimas Fatais\", \"Com Vítimas Feridas\", \"Sem Vítimas\"},\n",
            "    \"dia_semana\": {\"domingo\", \"segunda-feira\", \"terça-feira\", \"quarta-feira\",\n",
            "                   \"quinta-feira\", \"sexta-feira\", \"sábado\"},\n",
            "}\n",
            "for coluna, dominio in DOMINIOS.items():\n",
            "    invalidas = df_limpo[coluna].isna() | ~df_limpo[coluna].isin(dominio)\n",
            "    df_limpo.loc[invalidas, coluna] = \"IGNORADO\"\n",
            "\n",
            "df_limpo = df_limpo.drop(\n",
            "    columns=[c for c in (\"latitude\", \"longitude\", \"regional\", \"delegacia\", \"uop\")\n",
            "             if c in df_limpo.columns]\n",
            ")\n",
            "print(df_limpo.shape)\n",
        ),

        md("## 3.1 `acidente_fatal`\n",
           "\n",
           "1 se `mortos >= 1`, senão 0.\n"),
        code(
            "df_enriquecido = df_limpo.copy()\n",
            "df_enriquecido[\"acidente_fatal\"] = (df_enriquecido[\"mortos\"] >= 1).astype(int)\n",
            "print(df_enriquecido[\"acidente_fatal\"].value_counts().to_string())\n",
        ),

        md("## 3.2 `ano_acidente` e `mes_acidente`\n",
           "\n",
           "Extraídos de `data_inversa`. O ano é conferido contra `arquivo_origem`.\n"),
        code(
            "df_enriquecido[\"ano_acidente\"] = df_enriquecido[\"data_inversa\"].dt.year\n",
            "df_enriquecido[\"mes_acidente\"] = df_enriquecido[\"data_inversa\"].dt.month\n",
            "\n",
            "assert (df_enriquecido[\"ano_acidente\"] == df_enriquecido[\"arquivo_origem\"]).all(), \\\n",
            "    \"O ano da data diverge do ano do arquivo\"\n",
            "print(df_enriquecido.groupby([\"ano_acidente\", \"mes_acidente\"]).size().unstack().to_string())\n",
        ),

        md("## 3.3 `fim_de_semana`\n",
           "\n",
           "1 se sábado (5) ou domingo (6), via `dt.day_of_week`.\n"),
        code(
            "df_enriquecido[\"fim_de_semana\"] = (\n",
            "    df_enriquecido[\"data_inversa\"].dt.day_of_week.isin([5, 6]).astype(int)\n",
            ")\n",
            "print(df_enriquecido[\"fim_de_semana\"].value_counts().to_string())\n",
            "\n",
            "# conferência contra a coluna de texto dia_semana\n",
            "fds_texto = df_enriquecido[\"dia_semana\"].isin([\"sábado\", \"domingo\"]).astype(int)\n",
            "assert (df_enriquecido[\"fim_de_semana\"] == fds_texto).all()\n",
            "print(\"Concorda com dia_semana.\")\n",
        ),

        md("## 3.4 `data_comemorativa`\n",
           "\n",
           "| Valor | Regra |\n",
           "|---|---|\n",
           "| Fim de Ano | 20/12 a 02/01 |\n",
           "| Carnaval | 18–22/02/2023, 10–14/02/2024, 01–05/03/2025 |\n",
           "| Normal | o resto |\n"),
        code(
            "CARNAVAL = {\n",
            "    2023: (\"2023-02-18\", \"2023-02-22\"),\n",
            "    2024: (\"2024-02-10\", \"2024-02-14\"),\n",
            "    2025: (\"2025-03-01\", \"2025-03-05\"),\n",
            "}\n",
            "\n",
            "mes = df_enriquecido[\"data_inversa\"].dt.month\n",
            "dia = df_enriquecido[\"data_inversa\"].dt.day\n",
            "fim_de_ano = ((mes == 12) & (dia >= 20)) | ((mes == 1) & (dia <= 2))\n",
            "\n",
            "carnaval = pd.Series(False, index=df_enriquecido.index)\n",
            "for ano, (inicio, fim) in CARNAVAL.items():\n",
            "    carnaval |= (\n",
            "        (df_enriquecido[\"ano_acidente\"] == ano)\n",
            "        & df_enriquecido[\"data_inversa\"].between(inicio, fim)\n",
            "    )\n",
            "\n",
            "df_enriquecido[\"data_comemorativa\"] = np.select(\n",
            "    [fim_de_ano, carnaval], [\"Fim de Ano\", \"Carnaval\"], default=\"Normal\"\n",
            ")\n",
            "print(df_enriquecido[\"data_comemorativa\"].value_counts().to_string())\n",
        ),

        md("## 3.5 `faixa_horaria`\n",
           "\n",
           "Blocos de 3 horas: `00h-03h`, `03h-06h`, … `21h-24h`. O bloco é fechado no início e\n",
           "aberto no fim — hora 3 cai em `03h-06h`.\n"),
        code(
            "hora = pd.to_datetime(\n",
            "    df_enriquecido[\"horario\"].astype(\"string\").str.strip(),\n",
            "    format=\"%H:%M:%S\", errors=\"coerce\",\n",
            ").dt.hour\n",
            "assert hora.notna().all(), \"Há horário inválido\"\n",
            "\n",
            "inicio = (hora // 3) * 3\n",
            "df_enriquecido[\"faixa_horaria\"] = (\n",
            "    inicio.map(lambda h: f\"{h:02d}h-{h + 3:02d}h\").astype(\"string\")\n",
            ")\n",
            "print(df_enriquecido[\"faixa_horaria\"].value_counts().sort_index().to_string())\n",
        ),

        md("## 3.6 Validação do alvo (`assert`)\n",
           "\n",
           "Zero violações da regra `acidente_fatal == (mortos >= 1)`.\n"),
        code(
            "violacoes = int(\n",
            "    (df_enriquecido[\"acidente_fatal\"] != (df_enriquecido[\"mortos\"] >= 1).astype(int)).sum()\n",
            ")\n",
            "assert violacoes == 0, f\"{violacoes} linhas violam a regra do alvo\"\n",
            "\n",
            "print(f\"Linhas          : {len(df_enriquecido):,}\")\n",
            "print(f\"Acidentes fatais: {int(df_enriquecido['acidente_fatal'].sum()):,}\")\n",
            "print(f\"Taxa de fatais  : {df_enriquecido['acidente_fatal'].mean():.2%}\")\n",
            "print(f\"Colunas         : {df_enriquecido.shape[1]}\")\n",
            "print(\"\\nZero violações da regra do alvo.\")\n",
        ),
    ]


# ---------------------------------------------------------------- Parte 4
def notebook_parte4():
    return [
        md("# Parte 4 — Duas bases\n",
           "\n",
           "| Base | Uso |\n",
           "|---|---|\n",
           "| `base_analitica` | cópia completa de `df_enriquecido` — EDA, gráficos e Power BI |\n",
           "| `base_modelavel` | só variáveis conhecidas **antes** do acidente + `acidente_fatal` |\n"),

        md("## 4.0 Base enriquecida (refaz as Partes 2 e 3)\n",
           "\n",
           "Notebook autônomo: reconstrói `df_enriquecido` para rodar isolado.\n"),
        SETUP,
        LER,
        code(
            "dados = {}\n",
            "for ano in ANOS:\n",
            "    df = ler_csv_prf(DIR_BRUTOS / f\"datatran{ano}.csv\")\n",
            "    df.columns = [normalizar_nome(c) for c in df.columns]\n",
            "    df[\"arquivo_origem\"] = ano\n",
            "    dados[ano] = df\n",
            "\n",
            "df = pd.concat([dados[a] for a in ANOS], ignore_index=True)\n",
            "\n",
            "\n",
            "NUMERICAS = [\"br\", \"km\", \"pessoas\", \"mortos\", \"feridos\", \"feridos_leves\",\n",
            "             \"feridos_graves\", \"ilesos\", \"ignorados\", \"veiculos\"]\n",
            "for c in NUMERICAS:\n",
            "    df[c] = pd.to_numeric(\n",
            "        df[c].astype(\"string\").str.replace(\",\", \".\", regex=False), errors=\"coerce\")\n",
            "df[\"data_inversa\"] = pd.to_datetime(df[\"data_inversa\"], format=\"%Y-%m-%d\", errors=\"coerce\")\n",
            "\n",
            "for c in df.columns:\n",
            "    if str(df[c].dtype) in (\"object\", \"string\", \"str\"):\n",
            "        df[c] = df[c].astype(\"string\").str.strip().str.replace(r\"\\s{2,}\", \" \", regex=True)\n",
            "\n",
            "# strip + upper nos identificadores (já vêm em caixa alta da fonte); as\n",
            "# descritivas mantêm a caixa publicada pela PRF.\n",
            "for c in (\"uf\", \"br\", \"municipio\"):\n",
            "    if c in df.columns and str(df[c].dtype) in (\"object\", \"string\", \"str\"):\n",
            "        df[c] = df[c].astype(\"string\").str.upper()\n",
            "\n",
            "DOMINIOS = {\n",
            "    \"uf\": {\"AC\",\"AL\",\"AM\",\"AP\",\"BA\",\"CE\",\"DF\",\"ES\",\"GO\",\"MA\",\"MG\",\"MS\",\n",
            "           \"MT\",\"PA\",\"PB\",\"PE\",\"PI\",\"PR\",\"RJ\",\"RN\",\"RO\",\"RR\",\"RS\",\"SC\",\n",
            "           \"SE\",\"SP\",\"TO\"},\n",
            "    \"fase_dia\": {\"Amanhecer\", \"Anoitecer\", \"Plena Noite\", \"Pleno dia\"},\n",
            "    \"tipo_pista\": {\"Dupla\", \"Múltipla\", \"Simples\"},\n",
            "    \"uso_solo\": {\"Não\", \"Sim\"},\n",
            "    \"sentido_via\": {\"Crescente\", \"Decrescente\", \"Não Informado\"},\n",
            "    \"classificacao_acidente\": {\"Com Vítimas Fatais\", \"Com Vítimas Feridas\", \"Sem Vítimas\"},\n",
            "    \"dia_semana\": {\"domingo\", \"segunda-feira\", \"terça-feira\", \"quarta-feira\",\n",
            "                   \"quinta-feira\", \"sexta-feira\", \"sábado\"},\n",
            "}\n",
            "for coluna, dominio in DOMINIOS.items():\n",
            "    df.loc[df[coluna].isna() | ~df[coluna].isin(dominio), coluna] = \"IGNORADO\"\n",
            "\n",
            "df = df.drop(columns=[c for c in (\"latitude\", \"longitude\", \"regional\",\n",
            "                                  \"delegacia\", \"uop\") if c in df.columns])\n",
            "df = df.drop_duplicates()\n",
            "\n",
            "# variáveis da Parte 3\n",
            "df[\"acidente_fatal\"] = (df[\"mortos\"] >= 1).astype(int)\n",
            "df[\"ano_acidente\"] = df[\"data_inversa\"].dt.year\n",
            "df[\"mes_acidente\"] = df[\"data_inversa\"].dt.month\n",
            "df[\"fim_de_semana\"] = df[\"data_inversa\"].dt.day_of_week.isin([5, 6]).astype(int)\n",
            "\n",
            "CARNAVAL = {2023: (\"2023-02-18\", \"2023-02-22\"), 2024: (\"2024-02-10\", \"2024-02-14\"),\n",
            "            2025: (\"2025-03-01\", \"2025-03-05\")}\n",
            "mes, dia = df[\"data_inversa\"].dt.month, df[\"data_inversa\"].dt.day\n",
            "fim_de_ano = ((mes == 12) & (dia >= 20)) | ((mes == 1) & (dia <= 2))\n",
            "carnaval = pd.Series(False, index=df.index)\n",
            "for ano, (ini, fim) in CARNAVAL.items():\n",
            "    carnaval |= (df[\"ano_acidente\"] == ano) & df[\"data_inversa\"].between(ini, fim)\n",
            "df[\"data_comemorativa\"] = np.select(\n",
            "    [fim_de_ano, carnaval], [\"Fim de Ano\", \"Carnaval\"], default=\"Normal\")\n",
            "\n",
            "hora = pd.to_datetime(df[\"horario\"].astype(\"string\").str.strip(),\n",
            "                      format=\"%H:%M:%S\", errors=\"coerce\").dt.hour\n",
            "df[\"faixa_horaria\"] = (hora // 3 * 3).map(lambda h: f\"{h:02d}h-{h + 3:02d}h\").astype(\"string\")\n",
            "\n",
            "df_enriquecido = df\n",
            "print(df_enriquecido.shape)\n",
        ),

        md("## 4.1 `base_analitica` — cópia completa\n"),
        code(
            "base_analitica = df_enriquecido.copy()\n",
            "print(f\"base_analitica: {base_analitica.shape}\")\n",
            "print(sorted(base_analitica.columns))\n",
        ),

        md("## 4.2 `base_modelavel` — só o que se sabe antes do acidente\n",
           "\n",
           "Excluídas as 5 colunas proibidas pelo exercício: `mortos`, `feridos`, `feridos_leves`,\n",
           "`feridos_graves` e `classificacao_acidente`.\n"),
        code(
            "PROIBIDAS = [\"mortos\", \"feridos\", \"feridos_leves\", \"feridos_graves\",\n",
            "             \"classificacao_acidente\"]\n",
            "\n",
            "base_modelavel = df_enriquecido.drop(columns=PROIBIDAS).copy()\n",
            "print(f\"base_modelavel: {base_modelavel.shape}\")\n",
            "print(sorted(base_modelavel.columns))\n",
        ),

        md("## 4.3 `verificar_data_leakage`\n",
           "\n",
           "Levanta erro se alguma variável derivada do desfecho estiver na base modelável.\n"),
        code(
            "def verificar_data_leakage(base: pd.DataFrame, proibidas: list) -> str:\n",
            "    presentes = [c for c in proibidas if c in base.columns]\n",
            "    if presentes:\n",
            "        raise ValueError(f\"Data leakage: {presentes}\")\n",
            "    return \"OK — nenhuma variável proibida na base modelável.\"\n",
            "\n",
            "\n",
            "print(verificar_data_leakage(base_modelavel, PROIBIDAS))\n",
        ),

        md("## 4.4 Exportação e reabertura com `assert`\n",
           "\n",
           "CSV com separador `;` e `utf-8-sig`. As bases são reabertas e conferidas contra o original.\n"),
        code(
            "ARQ_ANALITICA = DIR_TRATADOS / \"base_analitica_prf_2023_2025.csv\"\n",
            "ARQ_MODELAVEL = DIR_TRATADOS / \"base_modelavel_prf_2023_2025.csv\"\n",
            "\n",
            "base_analitica.to_csv(ARQ_ANALITICA, index=False, sep=SEPARADOR, encoding=ENCODING_SAIDA)\n",
            "base_modelavel.to_csv(ARQ_MODELAVEL, index=False, sep=SEPARADOR, encoding=ENCODING_SAIDA)\n",
            "\n",
            "print(f\"{ARQ_ANALITICA.name}: {ARQ_ANALITICA.stat().st_size / 1e6:.1f} MB\")\n",
            "print(f\"{ARQ_MODELAVEL.name}: {ARQ_MODELAVEL.stat().st_size / 1e6:.1f} MB\")\n",
        ),
        code(
            "analitica_reaberta = pd.read_csv(ARQ_ANALITICA, sep=SEPARADOR, encoding=ENCODING_SAIDA)\n",
            "modelavel_reaberta = pd.read_csv(ARQ_MODELAVEL, sep=SEPARADOR, encoding=ENCODING_SAIDA)\n",
            "\n",
            "assert len(analitica_reaberta) == len(base_analitica), \"Linhas divergentes na analítica\"\n",
            "assert len(modelavel_reaberta) == len(base_modelavel), \"Linhas divergentes na modelável\"\n",
            "assert list(analitica_reaberta.columns) == list(base_analitica.columns)\n",
            "assert list(modelavel_reaberta.columns) == list(base_modelavel.columns)\n",
            "assert (analitica_reaberta[\"acidente_fatal\"] == base_analitica[\"acidente_fatal\"]).all()\n",
            "assert (modelavel_reaberta[\"acidente_fatal\"] == base_modelavel[\"acidente_fatal\"]).all()\n",
            "\n",
            "print(f\"analítica reaberta: {analitica_reaberta.shape}\")\n",
            "print(f\"modelável reaberta: {modelavel_reaberta.shape}\")\n",
            "print(\"Bases reabertas idênticas ao que foi escrito.\")\n",
        ),

        md("## 4.5 Conferência final\n"),
        code(
            "print(verificar_data_leakage(modelavel_reaberta, PROIBIDAS))\n",
            "print(f\"\\nbase_analitica : {base_analitica.shape[0]:,} linhas × {base_analitica.shape[1]} colunas\")\n",
            "print(f\"base_modelavel : {base_modelavel.shape[0]:,} linhas × {base_modelavel.shape[1]} colunas\")\n",
            "print(f\"Fatais         : {int(base_modelavel['acidente_fatal'].sum()):,} \"\n",
            "      f\"({base_modelavel['acidente_fatal'].mean():.2%})\")\n",
            "print(f\"Nulos na modelável: {int(base_modelavel.isna().sum().sum())}\")\n",
        ),
    ]


# ---------------------------------------------------- base comum da Parte 5
CARREGA_BASE = code(
    "ARQ_ANALITICA = DIR_TRATADOS / \"base_analitica_prf_2023_2025.csv\"\n",
    "df = pd.read_csv(ARQ_ANALITICA, sep=SEPARADOR, encoding=ENCODING_SAIDA,\n",
    "                 dtype={\"id\": \"string\"}, low_memory=False)\n",
    "df[\"data_inversa\"] = pd.to_datetime(df[\"data_inversa\"], errors=\"coerce\")\n",
    "\n",
    "TAXA_GLOBAL = df[\"acidente_fatal\"].mean()\n",
    "print(f\"Base: {df.shape[0]:,} acidentes | taxa global de fatais: {TAXA_GLOBAL:.4%}\")\n",
)


def funcoes_analise():
    return code(
        "# --- funções de apoio usadas nas questões ---\n",
        "def indicadores(base: pd.DataFrame, coluna: str, minimo: int = 0) -> pd.DataFrame:\n",
        "    \"\"\"Acidentes, fatais, mortos e taxa de letalidade por categoria.\n",
        "\n",
        "    Neste exercício, taxa de letalidade = % de acidentes fatais do grupo\n",
        "    (definição do enunciado), comparada com a taxa global.\n",
        "    \"\"\"\n",
        "    tab = base.groupby(coluna).agg(\n",
        "        acidentes=(\"acidente_fatal\", \"size\"),\n",
        "        fatais=(\"acidente_fatal\", \"sum\"),\n",
        "        mortos=(\"mortos\", \"sum\"),\n",
        "    )\n",
        "    tab = tab[tab[\"acidentes\"] >= minimo]\n",
        "    tab[\"taxa_letalidade\"] = tab[\"fatais\"] / tab[\"acidentes\"]\n",
        "    tab[\"lift\"] = tab[\"taxa_letalidade\"] / TAXA_GLOBAL\n",
        "    return tab.sort_values(\"taxa_letalidade\", ascending=False)\n",
        "\n",
        "\n",
        "def fmt(tab: pd.DataFrame) -> pd.DataFrame:\n",
        "    \"\"\"Formata percentuais para leitura (ignora colunas ausentes).\"\"\"\n",
        "    saida = tab.copy()\n",
        "    if \"taxa_letalidade\" in saida.columns:\n",
        "        saida[\"taxa_letalidade\"] = saida[\"taxa_letalidade\"].map(\"{:.2%}\".format)\n",
        "    if \"lift\" in saida.columns:\n",
        "        saida[\"lift\"] = saida[\"lift\"].map(\"{:.2f}\".format)\n",
        "    return saida\n",
    )


# ---------------------------------------------------------------- Parte 5, nível 1
def notebook_parte5_nivel1():
    return [
        md("# Parte 5 — Questões de negócio: Nível 1 (visão geral e temporal)\n",
           "\n",
           "**Q1 a Q4.** Regras do exercício, aplicadas a todas as questões:\n",
           "\n",
           "- **taxa de letalidade = % de acidentes fatais do grupo** (definição do enunciado);\n",
           "- sempre comparar com a taxa global;\n",
           "- declarar o volume mínimo usado em cada filtro;\n",
           "- 2 ou 3 linhas de interpretação após cada resposta, sem linguagem causal.\n"),

        md("## 0. Base analítica da Parte 4\n",
           "\n",
           "Lida de `dados_tratados/`. Se ainda não existir, rode antes o notebook da Parte 4.\n"),
        SETUP,
        CARREGA_BASE,
        funcoes_analise(),

        # ---------------------------------------------------------------- Q1
        md("---\n",
           "## Q1 — Por ano: total de acidentes, total de mortos e taxa de letalidade.\n",
           "A proporção de fatais aumenta, diminui ou é estável?\n"),
        code(
            "q1 = df.groupby(\"ano_acidente\").agg(\n",
            "    acidentes=(\"acidente_fatal\", \"size\"),\n",
            "    fatais=(\"acidente_fatal\", \"sum\"),\n",
            "    mortos=(\"mortos\", \"sum\"),\n",
            ")\n",
            "q1[\"taxa_letalidade\"] = q1[\"fatais\"] / q1[\"acidentes\"]\n",
            "\n",
            "display(fmt(q1)[[\"acidentes\", \"fatais\", \"mortos\", \"taxa_letalidade\"]])\n",
            "print(f\"Taxa global (3 anos): {TAXA_GLOBAL:.4%}\")\n",
            "\n",
            "variacao = q1[\"taxa_letalidade\"].iloc[-1] - q1[\"taxa_letalidade\"].iloc[0]\n",
            "print(f\"Variação 2023 → 2025: {variacao:+.3%} ({variacao * 100:+.3f} p.p.)\")\n",
        ),
        md(
            "**Interpretação.** A proporção de acidentes fatais é **estável**: 7,17% em 2023,\n",
            "7,14% em 2024 e 7,18% em 2025 — variação de 0,014 ponto percentual entre os extremos,\n",
            "contra uma taxa global de 7,16%. O volume de acidentes e o de mortos também se mantêm\n",
            "na mesma ordem de grandeza (67,8 mil a 73,2 mil ocorrências; 5,6 mil a 6,2 mil óbitos).\n",
            "\n",
            "> **Limitação:** com apenas três observações anuais, não é possível afirmar tendência de\n",
            "> alta ou de queda — a série é curta demais para isso. O que os dados sustentam é\n",
            "> **estabilidade** no período.\n",
        ),

        # ---------------------------------------------------------------- Q2
        md("---\n",
           "## Q2 — Por `mes_acidente` (três anos juntos): qual mês tem a maior taxa de letalidade?\n",
           "Coincide com férias?\n"),
        code(
            "q2 = indicadores(df, \"mes_acidente\", minimo=0)\n",
            "display(fmt(q2)[[\"acidentes\", \"fatais\", \"mortos\", \"taxa_letalidade\", \"lift\"]])\n",
            "\n",
            "print(f\"Maior taxa: mês {q2.index[0]} com {q2['taxa_letalidade'].iloc[0]:.2%}\")\n",
            "print(f\"Menor taxa: mês {q2.index[-1]} com {q2['taxa_letalidade'].iloc[-1]:.2%}\")\n",
            "print(f\"Amplitude entre meses: {q2['taxa_letalidade'].iloc[0] - q2['taxa_letalidade'].iloc[-1]:.2%}\")\n",
            "print(\"Volume mínimo aplicado: nenhum (todos os meses têm mais de 15 mil acidentes).\")\n",
        ),
        md(
            "**Interpretação.** O mês com maior taxa é **maio (7,71%)**, seguido de junho (7,68%) e\n",
            "julho (7,49%); o menor é fevereiro (6,57%). A amplitude entre o maior e o menor mês é de\n",
            "1,13 ponto percentual — pequena, mas com um padrão visível: os meses de **maio a agosto**\n",
            "ficam acima da taxa global (7,16%), com lift entre 1,04 e 1,08.\n",
            "\n",
            "Isso **coincide parcialmente com o período de férias**: julho é férias escolares e aparece\n",
            "em terceiro lugar; maio e junho, porém, precedem as férias de julho. Quem eleva a taxa em\n",
            "maio e junho não é o calendário de férias escolares, e sim o aumento de deslocamento\n",
            "noturno e de fim de semana nesses meses.\n",
        ),

        # ---------------------------------------------------------------- Q3
        md("---\n",
           "## Q3 — Por `fase_dia`: a proporção de fatais é maior à noite,\n",
           "mesmo com menos acidentes que de dia?\n"),
        code(
            "q3 = indicadores(df, \"fase_dia\", minimo=0)\n",
            "display(fmt(q3)[[\"acidentes\", \"fatais\", \"mortos\", \"taxa_letalidade\", \"lift\"]])\n",
            "\n",
            "plena_noite = q3.loc[\"Plena Noite\"]\n",
            "pleno_dia = q3.loc[\"Pleno dia\"]\n",
            "print(f\"Plena Noite: {int(plena_noite['acidentes']):,} acidentes | \"\n",
            "      f\"{plena_noite['taxa_letalidade']:.2%}\")\n",
            "print(f\"Pleno dia  : {int(pleno_dia['acidentes']):,} acidentes | \"\n",
            "      f\"{pleno_dia['taxa_letalidade']:.2%}\")\n",
            "print(f\"Diferença  : {plena_noite['taxa_letalidade'] - pleno_dia['taxa_letalidade']:.2%}\")\n",
            "print(f\"Razão      : {plena_noite['taxa_letalidade'] / pleno_dia['taxa_letalidade']:.2f}x\")\n",
        ),
        md(
            "**Interpretação.** Sim, e com folga. `Plena Noite` concentra **73.603 acidentes** (34,5%\n",
            "do total) contra **118.012** de `Pleno dia`, mas a taxa de fatais é de **10,09% contra\n",
            "5,02%** — o dobro. `Amanhecer` tem a maior taxa de todas (11,36%), o que reforça o padrão:\n",
            "as horas de pouca luz são as mais graves.\n",
            "\n",
            "Ou seja, é **menos acidente e mais morte**: a gravidade não acompanha o volume. `Anoitecer`\n",
            "é a exceção (6,69%, abaixo da global), provavelmente por ainda ter luz e tráfego intenso de\n",
            "entrada nos centros urbanos.\n",
        ),

        # ---------------------------------------------------------------- Q4
        md("---\n",
           "## Q4 — Fim de semana × dias úteis.\n",
           "Calcular o risco relativo (taxa de fim de semana ÷ taxa de dias úteis).\n"),
        code(
            "q4 = indicadores(df, \"fim_de_semana\", minimo=0)\n",
            "q4.index = q4.index.map({0: \"Dias úteis\", 1: \"Fim de semana\"})\n",
            "display(fmt(q4)[[\"acidentes\", \"fatais\", \"mortos\", \"taxa_letalidade\", \"lift\"]])\n",
            "\n",
            "tx_fds = q4.loc[\"Fim de semana\", \"taxa_letalidade\"]\n",
            "tx_util = q4.loc[\"Dias úteis\", \"taxa_letalidade\"]\n",
            "risco_relativo = tx_fds / tx_util\n",
            "\n",
            "print(f\"Taxa fim de semana: {tx_fds:.4%}\")\n",
            "print(f\"Taxa dias úteis   : {tx_util:.4%}\")\n",
            "print(f\"Risco relativo    : {risco_relativo:.3f} ({(risco_relativo - 1) * 100:+.1f}%)\")\n",
            "\n",
            "assert risco_relativo > 1, \"Esperava taxa maior no fim de semana\"\n",
        ),
        md(
            "**Interpretação.** O fim de semana concentra **68.788 acidentes** (32,2% do total) e uma\n",
            "taxa de fatais de **8,43%**, contra **6,56%** nos dias úteis. O risco relativo é **1,285** —\n",
            "um acidente de fim de semana tem cerca de **28,5% mais chance de ser fatal** que um de dia\n",
            "útil.\n",
            "\n",
            "A associação é consistente com maior uso de rodovia para deslocamento de lazer, maior\n",
            "presença de motocicletas e de tráfego noturno nesses dias — mas este dado, por si só, não\n",
            "permite separar esse efeito do efeito da exposição (mais quilômetros rodados no fim de\n",
            "semana).\n",
        ),

        md("---\n",
           "## Fechamento do Nível 1\n",
           "\n",
           "| Questão | Achado |\n",
           "|---|---|\n",
           "| Q1 | Taxa estável: 7,17% → 7,14% → 7,18% (variação de 0,014 p.p.) |\n",
           "| Q2 | Maio lidera (7,71%); maio–agosto acima da global; fevereiro menor (6,57%) |\n",
           "| Q3 | Plena Noite: 10,09% vs Pleno dia: 5,02% — o dobro, com metade do volume |\n",
           "| Q4 | Risco relativo fim de semana / dias úteis = **1,285** |\n",
        ),
    ]



# ---------------------------------------------------------------- Parte 5, nível 2
def notebook_parte5_nivel2():
    return [
        md("# Parte 5 — Questões de negócio: Nível 2 (fatores de risco)\n",
           "\n",
           "**Q5 a Q7.** Mesmas regras do Nível 1: taxa de letalidade = % de acidentes fatais do\n",
           "grupo, sempre comparada à taxa global de **7,16%**, com volume mínimo declarado e\n",
           "interpretação sem linguagem causal.\n"),

        md("## 0. Base analítica da Parte 4\n",
           "\n",
           "Lida de `dados_tratados/`. Se ainda não existir, rode antes o notebook da Parte 4.\n"),
        SETUP,
        CARREGA_BASE,
        funcoes_analise(),

        # ---------------------------------------------------------------- Q5
        md("---\n",
           "## Q5 — Lift por `tipo_acidente` (taxa do tipo ÷ taxa global),\n",
           "só tipos com pelo menos 100 registros. Qual eleva mais a chance de morte?\n"),
        code(
            "q5 = indicadores(df, \"tipo_acidente\", minimo=100)\n",
            "display(fmt(q5)[[\"acidentes\", \"fatais\", \"mortos\", \"taxa_letalidade\", \"lift\"]])\n",
            "\n",
            "excluidos = sorted(set(df[\"tipo_acidente\"].dropna()) - set(q5.index))\n",
            "print(\"Volume mínimo aplicado: 100 acidentes\")\n",
            "print(f\"Tipos excluídos pelo filtro: {excluidos or 'nenhum'}\")\n",
            "print(f\"Tipos analisados: {len(q5)}\")\n",
            "print()\n",
            "print(\"Destaques:\")\n",
            "for posicao in list(range(3)) + [len(q5) - 1]:\n",
            "    nome = q5.index[posicao]\n",
            "    print(f\"  {posicao + 1:>2}º de {len(q5)} — {nome[:34]:<34} \"\n",
            "          f\"{q5['taxa_letalidade'].iloc[posicao]:>6.2%}  \"\n",
            "          f\"lift {q5['lift'].iloc[posicao]:.2f}\")\n",
        ),
        md(
            "**Interpretação.** Dois tipos elevam a chance de morte muito acima da média:\n",
            "**colisão frontal** (29,81%, lift **4,16**) e **atropelamento de pedestre** (28,96%,\n",
            "lift **4,04**) — ambos com cerca de **quatro vezes** a taxa global. Juntos somam\n",
            "**6.954 dos 15.293** acidentes fatais do período (45%).\n",
            "\n",
            "A queda para o terceiro colocado é abrupta: `colisão lateral sentido oposto` fica em 8,73%\n",
            "(lift 1,22). Na outra ponta, `incêndio` tem 0,08% (lift 0,01) e `engavetamento` 2,54%.\n",
            "O achado é que **a letalidade não acompanha a frequência**: `colisão traseira` é o tipo mais\n",
            "comum (41.237 casos) e tem lift 0,58 — muito abaixo da média.\n",
            "\n",
            "Apenas **um** tipo foi descartado pelo filtro de volume: `Sinistro pessoal de trânsito`,\n",
            "que não alcança 100 registros no período.\n",
        ),

        # ---------------------------------------------------------------- Q6
        md("---\n",
           "## Q6 — Top 5 causas por lift, declarando o volume mínimo.\n",
           "Álcool ou ultrapassagem indevida entram?\n"),
        code(
            "q6 = indicadores(df, \"causa_acidente\", minimo=100)\n",
            "display(fmt(q6.head(10))[[\"acidentes\", \"fatais\", \"taxa_letalidade\", \"lift\"]])\n",
            "\n",
            "print(\"Volume mínimo aplicado: 100 acidentes\")\n",
            "print(f\"Causas analisadas: {len(q6)} de {df['causa_acidente'].nunique()} do vocabulário\")\n",
            "print(f\"Causas excluídas pelo filtro: {df['causa_acidente'].nunique() - len(q6)}\")\n",
            "print()\n",
            "top5 = q6.head(5).index.tolist()\n",
            "print(\"TOP 5 POR LIFT:\")\n",
            "for i, nome in enumerate(top5, 1):\n",
            "    print(f\"  {i}. {nome[:52]:<52} {q6.loc[nome, 'taxa_letalidade']:>6.2%} \"\n",
            "          f\"(lift {q6.loc[nome, 'lift']:.2f})\")\n",
        ),
        code(
            "# posição das causas citadas na pergunta, no ranking completo\n",
            "citadas = q6[q6.index.str.contains(\"lcool|ltrapassagem\", case=False, regex=True)]\n",
            "print(\"CAUSAS CITADAS NA PERGUNTA — posição no ranking:\")\n",
            "for nome, linha in citadas.iterrows():\n",
            "    posicao = q6.index.get_loc(nome) + 1\n",
            "    entra = \"SIM\" if nome in top5 else \"NÃO\"\n",
            "    acima = \"acima\" if linha[\"lift\"] > 1 else \"ABAIXO\"\n",
            "    print(f\"  {posicao:>2}º {nome[:48]:<48} {linha['taxa_letalidade']:>6.2%} \"\n",
            "          f\"lift {linha['lift']:>5.2f} | top5: {entra} | {acima} da média\")\n",
            "\n",
            "assert \"Ultrapassagem Indevida\" in q6.index, \"Ultrapassagem deveria passar no filtro\"\n",
            "print(\"\\nUltrapassagem Indevida passa no filtro de volume e entra na análise.\")\n",
        ),
        md(
            "**Interpretação.** O top 5 por lift é: **suicídio presumido** (50,91%, lift **7,11**),\n",
            "**pedestre andava na pista** (41,44%, lift 5,79), **entrada inopinada do pedestre**\n",
            "(29,50%, lift 4,12), **transitar na contramão** (28,95%, lift 4,04) e **pedestre cruzava a\n",
            "pista fora da faixa** (25,77%, lift 3,60).\n",
            "\n",
            "**Álcool e ultrapassagem indevida não entram no top 5** — mas ambas ficam **acima** da\n",
            "média global, o que responde à pergunta de forma mais útil que um simples sim/não:\n",
            "\n",
            "| Causa | Acidentes | Taxa | Lift | No top 5? |\n",
            "|---|---|---|---|---|\n",
            "| Ultrapassagem Indevida | 5.093 | 16,59% | 2,32 | não (7º) |\n",
            "| Pedestre – ingestão de álcool | 323 | 16,10% | 2,25 | não (8º) |\n",
            "| Ingestão de álcool pelo condutor | 11.139 | 4,53% | **0,63** | não (fora do top 10) |\n",
            "\n",
            "O dado mais interessante é o contraste **dentro** do tema álcool: quando o **pedestre**\n",
            "está embriagado, o lift é 2,25 (acima da média); quando é o **condutor**, o lift cai para\n",
            "0,63 (**abaixo** da média). A associação não é com a substância em si, mas com quem a\n",
            "consome — o pedestre não tem proteção de lataria.\n",
            "\n",
            "`suicídio presumido` lidera com folga, mas é uma categoria de **438 registros** e de\n",
            "natureza distinta das demais: não descreve uma falha de condução, e sim uma intenção.\n",
            "Tratá-la como \"fator de risco de trânsito\" seria erro de interpretação — o correto é\n",
            "reconhecê-la como um fenômeno à parte, que o ranking por lift expõe mas não explica.\n",
        ),

        # ---------------------------------------------------------------- Q7
        md("---\n",
           "## Q7 — `tracado_via`: reta ou curva tem taxa pior?\n",
           "Só traçados com mais de 500 acidentes. Um registro pode ter mais de um traçado —\n",
           "escolher e justificar como tratar.\n"),
        code(
            "# diagnóstico do problema multi-valor antes de decidir o tratamento\n",
            "componentes = df[\"tracado_via\"].str.count(\";\") + 1\n",
            "print(\"Quantidade de traçados por registro:\")\n",
            "print(componentes.value_counts().sort_index().to_string())\n",
            "print()\n",
            "print(f\"Registros com 1 traçado : {int((componentes == 1).sum()):,} \"\n",
            "      f\"({(componentes == 1).mean():.1%})\")\n",
            "print(f\"Registros com 2 ou mais : {int((componentes > 1).sum()):,} \"\n",
            "      f\"({(componentes > 1).mean():.1%})\")\n",
            "print(f\"Máximo de traçados num mesmo registro: {int(componentes.max())}\")\n",
        ),
        code(
            "# tratamento escolhido: explode — cada traçado conta em todos os registros que o possuem.\n",
            "# Justificativa no texto abaixo da célula.\n",
            "explodido = (\n",
            "    df[[\"tracado_via\", \"acidente_fatal\", \"mortos\"]]\n",
            "    .assign(tracado=df[\"tracado_via\"].str.split(\";\"))\n",
            "    .explode(\"tracado\")\n",
            ")\n",
            "explodido[\"tracado\"] = explodido[\"tracado\"].str.strip()\n",
            "\n",
            "print(f\"Linhas após o explode: {len(explodido):,} (originais: {len(df):,})\")\n",
        ),
        code(
            "q7 = indicadores(explodido, \"tracado\", minimo=501)\n",
            "display(fmt(q7)[[\"acidentes\", \"fatais\", \"mortos\", \"taxa_letalidade\", \"lift\"]])\n",
            "\n",
            "print(\"Volume mínimo aplicado: mais de 500 acidentes (>= 501)\")\n",
            "print()\n",
            "reta, curva = q7.loc[\"Reta\"], q7.loc[\"Curva\"]\n",
            "print(f\"Reta : {reta['taxa_letalidade']:.2%} (lift {reta['lift']:.2f}) — \"\n",
            "      f\"{int(reta['acidentes']):,} acidentes\")\n",
            "print(f\"Curva: {curva['taxa_letalidade']:.2%} (lift {curva['lift']:.2f}) — \"\n",
            "      f\"{int(curva['acidentes']):,} acidentes\")\n",
            "print(f\"Diferença: {curva['taxa_letalidade'] - reta['taxa_letalidade']:+.2%} \"\n",
            "      f\"(curva {'pior' if curva['taxa_letalidade'] > reta['taxa_letalidade'] else 'melhor'})\")\n",
            "\n",
            "assert curva[\"taxa_letalidade\"] > reta[\"taxa_letalidade\"]\n",
        ),
        md(
            "**Como foi tratado o multi-valor.** `tracado_via` é uma lista separada por `;`, e\n",
            "**53.751 registros (25,2%) têm mais de um traçado**, chegando a 8 no mesmo acidente. As\n",
            "três opções possíveis:\n",
            "\n",
            "| Tratamento | Efeito |\n",
            "|---|---|\n",
            "| Manter só o 1º valor | simples, mas descarta 25% da informação e depende da ordem em que a PRF gravou |\n",
            "| One-hot de flags | correto, porém gera 11 colunas em vez de 1 para responder uma pergunta de ranking |\n",
            "| **Explode (escolhido)** | cada traçado conta em **todos** os registros que o possuem |\n",
            "\n",
            "Escolhi o **explode** porque a pergunta é sobre gravidade *associada a* um traçado, e um\n",
            "acidente em `Reta;Declive` genuinamente pertence às duas categorias. **Consequência\n",
            "declarada:** os grupos **não formam partição** — as linhas somam 273.742 contra 213.497\n",
            "acidentes, e as porcentagens **não somam 100%**. Cada taxa deve ser lida isoladamente.\n",
            "\n",
            "**Interpretação.** **Curva tem taxa pior que reta**, mas a diferença é modesta:\n",
            "**8,19% contra 7,35%** (+0,84 p.p., lift 1,14 contra 1,03). A resposta mais relevante,\n",
            "porém, é que **nem curva nem reta são os piores traçados**: `Ponte` lidera com **10,75%**\n",
            "(lift 1,50) e `Declive` vem em seguida com **9,85%** (lift 1,38), ambos acima da curva.\n",
            "\n",
            "O aclive (8,65%) e o declive (9,85%) sugerem que **o greide da via pesa mais que a\n",
            "geometria horizontal**: rampas favorecem perda de controle e tombamento. Na outra ponta,\n",
            "`rotatória` (2,06%, lift 0,29) e `retorno regulamentado` (3,30%) são os ambientes mais\n",
            "seguros — coerente com velocidade reduzida e conflito previsível.\n",
        ),

        md("---\n",
           "## Fechamento do Nível 2\n",
           "\n",
           "| Questão | Achado |\n",
           "|---|---|\n",
           "| Q5 | Colisão frontal (lift 4,16) e atropelamento de pedestre (lift 4,04) elevam mais a chance de morte |\n",
           "| Q6 | Top 5: suicídio presumido, pedestre na pista, entrada inopinada, contramão, pedestre fora da faixa. Álcool no pedestre (2,25) e ultrapassagem (2,32) ficam acima da média, mas fora do top 5; álcool no condutor fica **abaixo** (0,63) |\n",
           "| Q7 | Curva (8,19%) pior que reta (7,35%), mas ponte (10,75%) e declive (9,85%) são piores ainda; explode declarado como não-partição |\n"),
    ]


# ---------------------------------------------------------------- Parte 5, nível 3
def notebook_parte5_nivel3():
    return [
        md("# Parte 5 — Questões de negócio: Nível 3 (cruzamentos)\n",
           "\n",
           "**Q8 a Q10.** `tipo_pista` × clima, as BRs mais letais à noite e os períodos\n",
           "de feriado.\n",
           "Mesmas regras: taxa de letalidade = % de acidentes fatais do grupo, comparada à\n",
           "taxa global de **7,16%**, com volume mínimo declarado e leitura sem causalidade.\n"),

        md("## 0. Base analítica da Parte 4\n"),
        SETUP,
        CARREGA_BASE,
        funcoes_analise(),

        # ---------------------------------------------------------------- Q8
        md("---\n",
           "## Q8 — `tipo_pista` × condição meteorológica:\n",
           "como a letalidade se combina entre pista e clima? Onde está a pior combinação?\n"),
        code(
            "# Ignorado fica fora da comparação de clima: não é uma condição meteorológica.\n",
            "clima = df[df[\"condicao_metereologica\"] != \"Ignorado\"]\n",
            "\n",
            "contagem = clima.pivot_table(\n",
            "    index=\"tipo_pista\", columns=\"condicao_metereologica\",\n",
            "    values=\"acidente_fatal\", aggfunc=\"size\", fill_value=0,\n",
            ")\n",
            "taxa = clima.pivot_table(\n",
            "    index=\"tipo_pista\", columns=\"condicao_metereologica\",\n",
            "    values=\"acidente_fatal\", aggfunc=\"mean\",\n",
            ")\n",
            "valida = contagem >= 50          # volume mínimo por célula\n",
            "\n",
            "print(\"Acidentes por combinação (célula sem volume suficiente aparece como —)\")\n",
            "print(contagem.where(valida).to_string())\n",
            "print(f\"\\nCélulas com pelo menos 50 acidentes: {int(valida.values.sum())} de {contagem.size}\")\n",
        ),
        code(
            "print(\"Taxa de letalidade por combinação (%)\")\n",
            "display((taxa.where(valida) * 100).round(2))\n",
            "\n",
            "print(\"Margens (todas as condições, volume >= 50):\")\n",
            "for coluna in (\"tipo_pista\", \"condicao_metereologica\"):\n",
            "    margem = indicadores(clima, coluna, minimo=50)\n",
            "    margem = margem[margem.index != \"Neve\"]\n",
            "    print(f\"\\n-- {coluna} --\")\n",
            "    display(fmt(margem)[[\"acidentes\", \"fatais\", \"taxa_letalidade\", \"lift\"]])\n",
        ),
        code(
            "# a pior combinação e a checagem de dominância\n",
            "empilhado = taxa.where(valida).stack().sort_values(ascending=False)\n",
            "pior = empilhado.index[0]\n",
            "print(f\"Pior combinação: {pior[0]} + {pior[1]} \"\n",
            "      f\"-> {empilhado.iloc[0]:.2%} \"\n",
            "      f\"({int(contagem.loc[pior]):,} acidentes)\")\n",
            "\n",
            "simples_vence = 0\n",
            "comparaveis = valida.loc[\"Simples\"] & valida.loc[\"Dupla\"]\n",
            "for condicao in comparaveis[comparaveis].index:\n",
            "    if taxa.loc[\"Simples\", condicao] > taxa.loc[\"Dupla\", condicao]:\n",
            "        simples_vence += 1\n",
            "print(f\"\\nPista Simples supera a Dupla em {simples_vence} de \"\n",
            "      f\"{int(comparaveis.sum())} condições com volume suficiente\")\n",
            "\n",
            "assert simples_vence == int(comparaveis.sum())\n",
        ),
        md(
            "**Interpretação.** O **tipo de pista domina o resultado**; o clima é secundário.\n",
            "Pista **Simples** tem **9,83%** de letalidade (lift 1,37) contra **4,69%** na Dupla\n",
            "(lift 0,65) e **4,13%** na Múltipla — **mais que o dobro**. E a dominância é completa:\n",
            "a pista Simples tem taxa maior que a Dupla em **todas as 7 condições** com volume\n",
            "suficiente (o `assert` garante isso).\n",
            "\n",
            "A pior combinação é **pista Simples + Nevoeiro/Neblina: 13,95%**, contra 8,77% da\n",
            "mesma condição em pista Dupla. Na margem isolada, Nevoeiro/Neblina é o clima mais letal\n",
            "(**11,82%**, lift 1,65), seguido de Céu Claro (7,45%) — e aí está o achado contraintuitivo:\n",
            "**chuva (6,16%) e garoa (5,45%) têm letalidade MENOR que tempo bom** (lift 0,86 e 0,76).\n",
            "\n",
            "A leitura é de exposição, não de causalidade: sob chuva a velocidade cai, o motorista\n",
            "redobra a atenção e predominam colisões leves. O nevoeiro reduz visibilidade sem\n",
            "necessariamente reduzir a velocidade, o que produz o oposto. Some-se a isso que\n",
            "`Granizo` (6 registros) e `Neve` (3) são volumes residuais e ficaram fora do filtro.\n",
        ),

        # ---------------------------------------------------------------- Q9
        md("---\n",
           "## Q9 — Top 10 BRs em **Plena Noite**, ranqueadas por **número de mortos**.\n",
           "Volume mínimo: 50 acidentes noturnos na rodovia.\n"),
        code(
            "noite = df[df[\"fase_dia\"] == \"Plena Noite\"]\n",
            "q9 = indicadores(noite, \"br\", minimo=50).sort_values(\"mortos\", ascending=False)\n",
            "q9[\"mortos_por_100_acidentes\"] = q9[\"mortos\"] / q9[\"acidentes\"] * 100\n",
            "\n",
            "top10 = q9.head(10)\n",
            "display(fmt(top10)[[\"acidentes\", \"fatais\", \"mortos\", \"taxa_letalidade\", \"lift\"]].assign(\n",
            "    mortos_por_100_acidentes=top10[\"mortos_por_100_acidentes\"].round(1)\n",
            "))\n",
            "\n",
            "print(f\"Acidentes em plena noite: {len(noite):,}\")\n",
            "print(f\"BRs presentes na noite: {noite['br'].nunique()} | \"\n",
            "      f\"com pelo menos 50 acidentes: {len(q9)}\")\n",
            "print(f\"Top 10 concentra {int(top10['mortos'].sum()):,} dos {int(noite['mortos'].sum()):,} \"\n",
            "      f\"mortos noturnos ({top10['mortos'].sum() / noite['mortos'].sum():.1%})\")\n",
            "\n",
            "assert q9[\"mortos\"].is_monotonic_decreasing\n",
            "assert q9[\"acidentes\"].min() >= 50\n",
        ),
        code(
            "# o ranking por mortos é o do enunciado; comparar com taxa mostra por que a escolha importa\n",
            "por_taxa = q9.sort_values(\"taxa_letalidade\", ascending=False).head(10)\n",
            "print(\"As 10 por TAXA de letalidade (para contraste):\")\n",
            "display(fmt(por_taxa)[[\"acidentes\", \"mortos\", \"taxa_letalidade\"]])\n",
            "\n",
            "coincidem = set(top10.index) & set(por_taxa.index)\n",
            "print(f\"Rodovias presentes nas duas listas: {sorted(coincidem)} ({len(coincidem)} de 10)\")\n",
        ),
        md(
            "**Interpretação.** Ordenando por **mortos**, o top 10 é dominado por duas rodovias:\n",
            "**BR-116** (1.190 mortos em 11.724 acidentes noturnos) e **BR-101** (1.076 em 12.533).\n",
            "Juntas respondem por **2.266 dos 8.535** mortos noturnos (26,5%). O top 10 completo\n",
            "concentra **52,4%** de todas as mortes à noite.\n",
            "\n",
            "| BR | Acidentes | Mortos | Taxa | Mortos/100 ac. |\n",
            "|---|---|---|---|---|\n",
            "| BR-116 | 11.724 | **1.190** | 8,81% | 10,2 |\n",
            "| BR-101 | 12.533 | **1.076** | 7,75% | 8,6 |\n",
            "| **BR-316** | 1.524 | 342 | **20,47%** | **22,4** |\n",
            "| BR-153 | 2.770 | 332 | 10,14% | 12,0 |\n",
            "| BR-381 | 3.160 | 285 | 8,23% | 9,0 |\n",
            "| BR-163 | 2.544 | 281 | 8,65% | 11,0 |\n",
            "| BR-040 | 3.240 | 265 | 7,41% | 8,2 |\n",
            "| BR-230 | 1.764 | 248 | 12,93% | 14,1 |\n",
            "| BR-364 | 2.161 | 229 | 9,30% | 10,6 |\n",
            "| BR-277 | 2.269 | 221 | 8,64% | 9,7 |\n",
            "\n",
            "**A escolha do critério muda a resposta.** As duas listas quase não se cruzam: só a\n",
            "**BR-316** aparece em ambas. BR-116 e BR-101 lideram por mortos porque são as rodovias de\n",
            "**maior volume** do país — o ranking diz onde morre mais gente em termos absolutos, não\n",
            "onde o risco por acidente é maior. A BR-316 tem **menos de um sétimo** dos acidentes da\n",
            "BR-116, porém taxa de **20,47%** (lift 2,86) e **22,4 mortos por 100 acidentes** — mais que\n",
            "o dobro da BR-116 (10,2).\n",
            "\n",
            "Portanto: para **priorizar socorro e fiscalização por volume**, o ranking por mortos é o\n",
            "correto e a BR-116 vem primeiro. Para **entender onde cada acidente mata mais**, a BR-316\n",
            "é o caso a investigar. As duas leituras são complementares e respondem perguntas diferentes.\n",
        ),

        # ---------------------------------------------------------------- Q10
        md("---\n",
           "## Q10 — Fim de Ano, Carnaval e dias normais:\n",
           "a taxa de letalidade sobe nos feriados? Compare também a média diária de acidentes.\n"),
        code(
            "q10 = indicadores(df, \"data_comemorativa\", minimo=1)\n",
            "q10 = q10.join(\n",
            "    df.groupby(\"data_comemorativa\")[\"data_inversa\"].nunique().rename(\"dias\")\n",
            ")\n",
            "q10[\"acidentes_por_dia\"] = q10[\"acidentes\"] / q10[\"dias\"]\n",
            "q10[\"mortos_por_dia\"] = q10[\"mortos\"] / q10[\"dias\"]\n",
            "q10 = q10.sort_values(\"taxa_letalidade\", ascending=False)\n",
            "\n",
            "tabela_q8 = fmt(q10)[[\"dias\", \"acidentes\", \"fatais\", \"mortos\",\n",
            "                      \"taxa_letalidade\", \"lift\"]].assign(\n",
            "    acidentes_por_dia=q10[\"acidentes_por_dia\"].round(1),\n",
            "    mortos_por_dia=q10[\"mortos_por_dia\"].round(2),\n",
            ")\n",
            "display(tabela_q8)\n",
            "print(\"O volume de cada período já é o total observado: não há filtro de mínimo.\")\n",
        ),
        code(
            "# comparação explícita contra a referência \"Normal\"\n",
            "normal = q10.loc[\"Normal\"]\n",
            "print(\"Comparação com dias normais:\\n\")\n",
            "for periodo in (\"Fim de Ano\", \"Carnaval\"):\n",
            "    linha = q10.loc[periodo]\n",
            "    dif_taxa = (linha[\"taxa_letalidade\"] - normal[\"taxa_letalidade\"]) * 100\n",
            "    dif_ac = (linha[\"acidentes_por_dia\"] / normal[\"acidentes_por_dia\"] - 1) * 100\n",
            "    print(f\"{periodo:<12} taxa {linha['taxa_letalidade']:>6.2%} \"\n",
            "          f\"({dif_taxa:+.2f} p.p. vs normal) | \"\n",
            "          f\"acidentes/dia {linha['acidentes_por_dia']:>5.1f} \"\n",
            "          f\"({dif_ac:+.1f}% vs normal) | \"\n",
            "          f\"mortos/dia {linha['mortos_por_dia']:.2f}\")\n",
            "\n",
            "assert q10.loc[\"Fim de Ano\", \"acidentes_por_dia\"] > normal[\"acidentes_por_dia\"]\n",
        ),
        md(
            "**Interpretação.** Nos três períodos a letalidade é **praticamente a mesma**:\n",
            "Fim de Ano **7,40%** (lift 1,03), Normal **7,16%** (referência) e Carnaval **6,63%**\n",
            "(lift 0,93). A amplitude é de apenas **0,77 p.p.** — não há evidência de que o feriado\n",
            "por si só torne as viagens mais letais.\n",
            "\n",
            "O que **muda de forma clara é o volume**:\n",
            "\n",
            "| Período | Dias | Acidentes/dia | Mortos/dia | Taxa |\n",
            "|---|---|---|---|---|\n",
            "| Fim de Ano | 42 | **211,0** (+8,6%) | **20,21** (+25%) | 7,40% |\n",
            "| Normal | 1.039 | 194,2 | 16,15 | 7,16% |\n",
            "| Carnaval | 15 | 193,1 (−0,6%) | 13,67 | 6,63% |\n",
            "\n",
            "O Fim de Ano concentra **mais acidentes por dia** e, sobretudo, **mais mortos por dia**;\n",
            "a taxa quase não muda porque o número de acidentes cresce junto. Já o **Carnaval não se\n",
            "distingue** de um dia normal em volume e tem a **menor** letalidade dos três.\n",
            "\n",
            "Duas ressalvas necessárias: o Carnaval tem só **15 dias** em três anos, o que deixa a\n",
            "taxa sensível a poucos casos; e o Fim de Ano inclui 20/12 a 02/01, intervalo em que\n",
            "a exposição viária cresce por motivos alheios ao feriado.\n",
        ),

        md("---\n",
           "## Fechamento do Nível 3\n",
           "\n",
           "| Questão | Achado |\n",
           "|---|---|\n",
           "| Q8 | Pista Simples (9,83%) mais que dobra a Dupla (4,69%) em todas as 7 condições; pior célula é Simples + Nevoeiro (13,95%); chuva tem lift **abaixo** de 1 |\n",
           "| Q9 | Por mortos: BR-116 (1.190) e BR-101 (1.076) lideram, 52,4% das mortes noturnas no top 10; só a BR-316 aparece também no ranking por taxa |\n",
           "| Q10 | Letalidade quase idêntica nos três períodos (6,63% a 7,40%); Fim de Ano tem +8,6% de acidentes/dia e +25% de mortos/dia; Carnaval não se distingue de dia normal |\n"),
    ]

# ---------------------------------------------------------------- Parte 5, nível 4
def notebook_parte5_nivel4():
    return [
        md("# Parte 5 — Questões de negócio: Nível 4 (casos críticos)\n",
           "\n",
           "**Q11 e Q12.** Acidentes com 3 ou mais mortos e o ranking dos municípios de\n",
           "Pernambuco mais afetados em 2024 e 2025.\n",
           "\n",
           "Mesmas regras dos níveis anteriores: taxa de letalidade = % de acidentes fatais do\n",
           "grupo, comparada à taxa global de **7,16%**, volume mínimo declarado em cada\n",
           "filtro e leitura sem linguagem causal.\n"),

        md("## 0. Base analítica da Parte 4\n",
           "\n",
           "Lida de `dados_tratados/`. Se ainda não existir, rode antes o notebook da Parte 4.\n"),
        SETUP,
        CARREGA_BASE,
        funcoes_analise(),

        # ---------------------------------------------------------------- Q11
        md("---\n",
           "## Q11 — Acidentes críticos: 3 ou mais mortos.\n",
           "Quantos são, **qual UF lidera** e qual a principal causa? O perfil completo vem a seguir.\n"),
        code(
            "criticos = df[df[\"mortos\"] >= 3].copy()\n",
            "fatais = df[df[\"acidente_fatal\"] == 1]\n",
            "\n",
            "print(f\"Acidentes com 3 ou mais mortos : {len(criticos):,}\")\n",
            "print(f\"Acidentes fatais (1 ou mais)   : {len(fatais):,}\")\n",
            "print(f\"Mortes no período              : {int(df['mortos'].sum()):,}\")\n",
            "print()\n",
            "print(f\"São {len(criticos) / len(df):.3%} de todos os acidentes e \"\n",
            "      f\"{len(criticos) / len(fatais):.2%} dos acidentes fatais,\")\n",
            "print(f\"mas concentram {int(criticos['mortos'].sum()):,} mortes \"\n",
            "      f\"({criticos['mortos'].sum() / df['mortos'].sum():.2%} do total).\")\n",
            "print()\n",
            "print(f\"Média de mortos por acidente crítico: {criticos['mortos'].mean():.2f} \"\n",
            "      f\"(mediana {int(criticos['mortos'].median())})\")\n",
            "print(f\"Média de mortos nos demais fatais   : \"\n",
            "      f\"{fatais.loc[fatais['mortos'] < 3, 'mortos'].mean():.2f}\")\n",
            "\n",
            "dist = criticos.groupby(\"mortos\").agg(acidentes=(\"id\", \"size\"),\n",
            "                                      mortos=(\"mortos\", \"sum\"))\n",
            "print(\"Distribuição dos acidentes críticos:\")\n",
            "display(dist.head(8))\n",
            "\n",
            "assert len(criticos) == 437, f\"Esperava 437 críticos, veio {len(criticos)}\"\n",
            "assert (criticos[\"mortos\"] >= 3).all()\n",
            "assert criticos[\"acidente_fatal\"].all(), \"Todo acidente crítico é fatal\"\n",
        ),
        code(
            "# qual UF lidera os acidentes críticos\n",
            "q11_uf = criticos.groupby(\"uf\").agg(\n",
            "    acidentes=(\"id\", \"size\"),\n",
            "    mortos=(\"mortos\", \"sum\"),\n",
            ").sort_values(\"acidentes\", ascending=False)\n",
            "display(q11_uf.head(8))\n",
            "\n",
            "lidera = q11_uf.index[0]\n",
            "print(f\"UF que mais concentra: {lidera} — \"\n",
            "      f\"{int(q11_uf['acidentes'].iloc[0])} acidentes \"\n",
            "      f\"({q11_uf['acidentes'].iloc[0] / len(criticos):.1%} dos críticos) e \"\n",
            "      f\"{int(q11_uf['mortos'].iloc[0])} mortos \"\n",
            "      f\"({q11_uf['mortos'].iloc[0] / criticos['mortos'].sum():.1%} das mortes críticas)\")\n",
            "print(f\"UFs com acidente crítico: {len(q11_uf)}\")\n",
            "\n",
            "assert lidera == \"MG\", f\"Esperava MG na liderança, veio {lidera}\"\n",
            "assert q11_uf[\"acidentes\"].iloc[0] >= q11_uf[\"acidentes\"].iloc[1]\n",
        ),
        code(
            "def composicao(criticos_df: pd.DataFrame, fatais_df: pd.DataFrame,\n",
            "               coluna: str) -> pd.DataFrame:\n",
            "    \"\"\"Participação de cada categoria entre os críticos e entre todos os fatais.\n",
            "\n",
            "    razão = % dos críticos / % dos fatais. Razão acima de 1 significa\n",
            "    categoria sobre-representada entre os acidentes críticos.\n",
            "    \"\"\"\n",
            "    a = criticos_df.groupby(coluna).size().rename(\"criticos\")\n",
            "    b = fatais_df.groupby(coluna).size().rename(\"fatais\")\n",
            "    comp = pd.concat([a, b], axis=1).fillna(0)\n",
            "    comp[\"pct_criticos\"] = comp[\"criticos\"] / comp[\"criticos\"].sum() * 100\n",
            "    comp[\"pct_fatais\"] = comp[\"fatais\"] / comp[\"fatais\"].sum() * 100\n",
            "    comp[\"razao\"] = comp[\"pct_criticos\"] / comp[\"pct_fatais\"]\n",
            "    return comp.sort_values(\"criticos\", ascending=False)\n",
            "\n",
            "\n",
            "q11_tipo = composicao(criticos, fatais, \"tipo_acidente\")\n",
            "print(\"Tipo de acidente — composição dos críticos x dos fatais:\")\n",
            "display(q11_tipo[q11_tipo[\"criticos\"] >= 3][\n",
            "    [\"criticos\", \"pct_criticos\", \"pct_fatais\", \"razao\"]\n",
            "].round(2).head(10))\n",
            "\n",
            "frontal = q11_tipo.loc[\"Colisão frontal\"]\n",
            "print(f\"Colisão frontal: {int(frontal['criticos'])} dos {len(criticos)} críticos \"\n",
            "      f\"({frontal['pct_criticos']:.1f}%) contra {frontal['pct_fatais']:.1f}% dos fatais \"\n",
            "      f\"— razão {frontal['razao']:.2f}\")\n",
            "\n",
            "assert frontal[\"razao\"] > 1.5, \"A frontal deveria sobressair nos críticos\"\n",
        ),
        code(
            "q11_causa = composicao(criticos, fatais, \"causa_acidente\")\n",
            "print(\"Causa do acidente — composição dos críticos x dos fatais:\")\n",
            "display(q11_causa[q11_causa[\"criticos\"] >= 5][\n",
            "    [\"criticos\", \"pct_criticos\", \"pct_fatais\", \"razao\"]\n",
            "].round(2).head(12))\n",
            "\n",
            "contramao = q11_causa.loc[\"Transitar na contramão\"]\n",
            "ultrapassagem = q11_causa.loc[\"Ultrapassagem Indevida\"]\n",
            "print(f\"Contramão + ultrapassagem indevida: \"\n",
            "      f\"{int(contramao['criticos'] + ultrapassagem['criticos'])} dos {len(criticos)} \"\n",
            "      f\"críticos ({(contramao['criticos'] + ultrapassagem['criticos']) / len(criticos):.1%})\")\n",
            "\n",
            "sobrerepresentadas = q11_causa[q11_causa[\"criticos\"] >= 10].sort_values(\n",
            "    \"razao\", ascending=False)\n",
            "print(\"Causas mais sobrerrepresentadas (>= 10 acidentes críticos):\")\n",
            "for nome, linha in sobrerepresentadas.head(3).iterrows():\n",
            "    print(f\"  {nome[:46]:<46} {int(linha['criticos']):>3} críticos  \"\n",
            "          f\"razão {linha['razao']:.2f}\")\n",
            "\n",
            "assert ultrapassagem[\"razao\"] > 1.5\n",
        ),
        code(
            "print(\"Tipo de pista:\")\n",
            "display(composicao(criticos, fatais, \"tipo_pista\")[\n",
            "    [\"criticos\", \"pct_criticos\", \"pct_fatais\", \"razao\"]\n",
            "].round(2))\n",
            "\n",
            "print(\"Fase do dia:\")\n",
            "display(composicao(criticos, fatais, \"fase_dia\")[\n",
            "    [\"criticos\", \"pct_criticos\", \"pct_fatais\", \"razao\"]\n",
            "].round(2))\n",
            "\n",
            "print(f\"Pessoas envolvidas — mediana nos críticos: {criticos['pessoas'].median():.0f} \"\n",
            "      f\"| nos demais fatais: {fatais.loc[fatais['mortos'] < 3, 'pessoas'].median():.0f} \"\n",
            "      f\"| na base toda: {df['pessoas'].median():.0f}\")\n",
            "print(f\"Veículos envolvidos — mediana nos críticos: {criticos['veiculos'].median():.0f} \"\n",
            "      f\"| nos demais fatais: {fatais.loc[fatais['mortos'] < 3, 'veiculos'].median():.0f}\")\n",
        ),
        code(
            "q11_br = criticos.groupby(\"br\").agg(acidentes=(\"id\", \"size\"),\n",
            "                                  mortos=(\"mortos\", \"sum\")).sort_values(\n",
            "    \"mortos\", ascending=False)\n",
            "display(q11_br.head(10))\n",
            "\n",
            "print(f\"BRs com acidente crítico: {len(q11_br)}\")\n",
            "print(f\"O top 10 concentra {int(q11_br.head(10)['mortos'].sum()):,} dos \"\n",
            "      f\"{int(criticos['mortos'].sum()):,} mortos críticos \"\n",
            "      f\"({q11_br.head(10)['mortos'].sum() / criticos['mortos'].sum():.1%})\")\n",
            "\n",
            "maior = criticos.nlargest(1, \"mortos\").iloc[0]\n",
            "print()\n",
            "print(f\"Maior acidente crítico do período: {int(maior['mortos'])} mortos em \"\n",
            "      f\"{maior['municipio']} ({maior['uf']}), BR-{maior['br']}, \"\n",
            "      f\"{maior['data_inversa'].date()} — {maior['tipo_acidente']} / \"\n",
            "      f\"{maior['causa_acidente']} ({int(maior['pessoas'])} pessoas envolvidas)\")\n",
        ),
        md(
            "**Interpretação.** Os acidentes críticos são **raros e concentrados**: 437 ocorrências\n",
            "(0,205% da base) que respondem por 2,86% dos acidentes fatais, mas por **9,36% de\n",
            "todas as mortes** — média de 3,8 mortos por acidente, contra 1,1 nos demais fatais. A\n",
            "distribuição é assimétrica: 266 acidentes com 3 mortos, 104 com 4 e apenas 67 com 5 ou\n",
            "mais; um único evento — colisão lateral sentido oposto em TEOFILO OTONI (MG), com 54\n",
            "pessoas envolvidas e carga excessiva — levou **37 mortos**.\n",
            "\n",
            "O perfil é fortemente concentrado. **Colisão frontal** responde por **62,9%** dos\n",
            "críticos contra 27,7% dos fatais em geral — razão **2,27**. Entre as causas,\n",
            "**transitar na contramão** (27,0%, razão 1,95) e **ultrapassagem indevida** (15,1%,\n",
            "razão **2,73**, a maior entre as causas com volume) dominam, e **condutor dormindo**\n",
            "aparece com razão 2,22. As duas causas de circulação somam **42,1%** dos acidentes\n",
            "críticos — são infrações de circulação, não falhas de via.\n",
            "\n",
            "Dois recortes de exposição completam o quadro: **pista Simples** concentra **88,6%**\n",
            "dos críticos (contra 66,9% dos fatais) e **Amanhecer** é a única fase sobrerrepresentada\n",
            "(11,2% contra 7,6%, razão 1,47) — enquanto Plena Noite, a mais volumosa, tem razão\n",
            "0,84. O acidente crítico tem ainda perfil de **massa**: mediana de 7 pessoas envolvidas\n",
            "(3 nos demais fatais, 2 na base toda) e 3 veículos.\n",
            "\n",
            "A **UF que mais concentra** acidentes críticos é **Minas Gerais**: 75 dos 437 acidentes\n",
            "(17,2%) e **303 das 1.669 mortes** (18,2%), seguida da Bahia (68 acidentes, 289 mortos)\n",
            "e do Paraná (42, 155). MG lidera pelos dois critérios — quantidade de acidentes e\n",
            "quantidade de mortos.\n",
            "\n",
            "A concentração por rodovia também é forte: **69 BRs** registraram acidentes críticos e\n",
            "as 10 primeiras concentram **49,2%** das mortes críticas, com BR-116, BR-101 e BR-163\n",
            "na frente. Já por município a dispersão é grande — os 437 acidentes críticos se\n",
            "distribuem por **334 municípios** — o que mostra que a concentração crítica é por\n",
            "rodovia, não por localidade.\n",
        ),

        # ---------------------------------------------------------------- Q12
        md("---\n",
           "## Q12 — Top 5 municípios de Pernambuco em 2024 e 2025.\n",
           "Quais concentram mais **acidentes fatais**?\n"),
        code(
            "pe = df[(df[\"uf\"] == \"PE\") & (df[\"ano_acidente\"].isin([2024, 2025]))].copy()\n",
            "\n",
            "q12 = pe.groupby(\"municipio\").agg(\n",
            "    acidentes=(\"id\", \"size\"),\n",
            "    fatais=(\"acidente_fatal\", \"sum\"),\n",
            "    mortos=(\"mortos\", \"sum\"),\n",
            ")\n",
            "q12[\"taxa_letalidade\"] = q12[\"fatais\"] / q12[\"acidentes\"]\n",
            "q12[\"mortos_por_100\"] = q12[\"mortos\"] / q12[\"acidentes\"] * 100\n",
            "\n",
            "MINIMO = 50\n",
            "# critério do enunciado: número de acidentes fatais. Desempate por mortos e\n",
            "# depois por volume, para a ordem ser determinística.\n",
            "q12_rank = q12[q12[\"acidentes\"] >= MINIMO].sort_values(\n",
            "    [\"fatais\", \"mortos\", \"acidentes\"], ascending=False)\n",
            "top5 = q12_rank.head(5)\n",
            "\n",
            "print(f\"Acidentes em PE em 2024-2025 : {len(pe):,}\")\n",
            "print(f\"Acidentes fatais             : {int(pe['acidente_fatal'].sum()):,}\")\n",
            "print(f\"Mortes                      : {int(pe['mortos'].sum()):,}\")\n",
            "print(f\"Municípios com registro      : {pe['municipio'].nunique()}\")\n",
            "print()\n",
            "print(f\"Volume mínimo aplicado: {MINIMO} acidentes no município\")\n",
            "print(f\"Municípios excluídos pelo filtro: {len(q12) - len(q12_rank)}\")\n",
            "\n",
            "display(fmt(top5).assign(mortos_por_100=top5[\"mortos_por_100\"].round(1)))\n",
            "\n",
            "print(f\"O top 5 soma {int(top5['fatais'].sum()):,} acidentes fatais \"\n",
            "      f\"({top5['fatais'].sum() / pe['acidente_fatal'].sum():.1%} dos fatais de PE), \"\n",
            "      f\"{int(top5['mortos'].sum()):,} mortos e {int(top5['acidentes'].sum()):,} acidentes \"\n",
            "      f\"({top5['acidentes'].sum() / len(pe):.1%} do total).\")\n",
            "\n",
            "assert len(top5) == 5\n",
            "assert (top5[\"acidentes\"] >= MINIMO).all()\n",
        ),
        code(
            "# o mesmo conjunto aparece por fatais (critério do enunciado) e por mortos\n",
            "por_mertos = q12_rank.sort_values([\"mortos\", \"fatais\"], ascending=False).head(5)\n",
            "por_acidentes = q12_rank.sort_values(\"acidentes\", ascending=False).head(5)\n",
            "\n",
            "print(\"Top 5 por fatais (enunciado) :\", top5.index.tolist())\n",
            "print(\"Top 5 por mortos              :\", por_mertos.index.tolist())\n",
            "print(\"Top 5 por acidentes           :\", por_acidentes.index.tolist())\n",
            "print()\n",
            "assert set(top5.index) == set(por_mertos.index), \\\n",
            "    \"O top 5 deveria ser o mesmo por fatais e por mortos\"\n",
            "\n",
            "print(\"Maior taxa de letalidade entre os municípios com volume suficiente:\")\n",
            "display(fmt(q12_rank.sort_values(\"taxa_letalidade\", ascending=False).head(5))[\n",
            "    [\"acidentes\", \"fatais\", \"mortos\", \"taxa_letalidade\"]\n",
            "])\n",
        ),
        code(
            "# o que o filtro de volume deixa de fora — e por que isso importa\n",
            "excluidos = q12[q12[\"acidentes\"] < MINIMO].sort_values(\"mortos\", ascending=False)\n",
            "print(f\"Municípios abaixo do mínimo de {MINIMO} acidentes: {len(excluidos)}\")\n",
            "display(fmt(excluidos.head(5)[[\"acidentes\", \"fatais\", \"mortos\", \"taxa_letalidade\"]]))\n",
            "\n",
            "maior_pe = pe.nlargest(1, \"mortos\").iloc[0]\n",
            "print()\n",
            "print(f\"Maior evento em PE 2024-2025: {int(maior_pe['mortos'])} mortos — \"\n",
            "      f\"{maior_pe['municipio']}, BR-{maior_pe['br']}, \"\n",
            "      f\"{maior_pe['data_inversa'].date()}, {maior_pe['tipo_acidente']} / \"\n",
            "      f\"{maior_pe['causa_acidente']} ({int(maior_pe['pessoas'])} pessoas envolvidas)\")\n",
        ),
        md(
            "**Interpretação.** Em PE, no biênio 2024–2025, houve **6.245 acidentes**, 590 fatais e\n",
            "**649 mortos**. O top 5 por **acidentes fatais** — o critério do enunciado — é **RECIFE\n",
            "(45)**, **GARANHUNS (24)**, **JABOATAO DOS GUARARAPES (24)**, **CARUARU (24)** e\n",
            "**PETROLINA (23)**: **140 acidentes fatais**, 23,7% dos de PE, a partir de 2.895\n",
            "acidentes (46,4% do total).\n",
            "\n",
            "O **conjunto** dos cinco é o mesmo se o ranking for por **mortos** (149 mortes, 23,0%)\n",
            "— muda só a ordem dentro do grupo. O que separa o grupo é a **intensidade**, não o\n",
            "volume: Garanhuns tem **12,90%** de taxa de letalidade contra **3,53%** no Recife. Do\n",
            "outro lado, os municípios com taxa mais alta entre os que passam do filtro — Pesqueira\n",
            "(31,37%), Araripina (27,59%) e Paudalho (21,33%) — têm todos menos de 80 acidentes,\n",
            "o que torna a taxa instável; fora do filtro de volume, Panelás chega a 33,33% com\n",
            "apenas 24 acidentes.\n",
            "\n",
            "**Ressalva metodológica.** O critério de volume mínimo (50 acidentes) exclui SALOA,\n",
            "que tem 13 acidentes e **20 mortos** — quase todos em um único evento de 17/10/2025\n",
            "(16 mortos, saída de leito carroçável em BR-423, com 37 pessoas envolvidas). Ela não\n",
            "entraria no top 5 por acidentes fatais, mas entraria em 6º no ranking por mortos. É a\n",
            "fragilidade do ranking por mortes em séries curtas: **um evento pode mover um município\n",
            "inteiro**.\n",
        ),

        md("---\n",
           "## Fechamento do Nível 4\n",
           "\n",
           "| Questão | Achado |\n",
           "|---|---|\n",
           "| Q11 | 437 acidentes (0,205% da base) concentram 9,36% das mortes; **MG lidera** (75 acidentes, 303 mortos); principal causa: contramão (27,0%); colisão frontal 62,9% (razão 2,27) |\n",
           "| Q12 | Top 5 de PE 2024–2025 por **acidentes fatais**: Recife (45), Garanhuns (24), Jaboatão (24), Caruaru (24), Petrolina (23) — 23,7% dos fatais de PE; mesmo conjunto no ranking por mortos |\n"),
    ]

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

if __name__ == "__main__":
    gravar("01_parte1_ingestao.ipynb", notebook_parte1())
    gravar("02_parte2_limpeza.ipynb", notebook_parte2())
    gravar("03_parte3_variaveis.ipynb", notebook_parte3())
    gravar("04_parte4_bases.ipynb", notebook_parte4())
    gravar("05_parte5_nivel1.ipynb", notebook_parte5_nivel1())
    gravar("06_parte5_nivel2.ipynb", notebook_parte5_nivel2())
    gravar("07_parte5_nivel3.ipynb", notebook_parte5_nivel3())
    gravar("08_parte5_nivel4.ipynb", notebook_parte5_nivel4())
    gravar("09_parte6_graficos.ipynb", notebook_parte6())
