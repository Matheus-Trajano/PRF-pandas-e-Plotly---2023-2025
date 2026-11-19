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


if __name__ == "__main__":
    gravar("01_parte1_ingestao.ipynb", notebook_parte1())
    gravar("02_parte2_limpeza.ipynb", notebook_parte2())
    gravar("03_parte3_variaveis.ipynb", notebook_parte3())
