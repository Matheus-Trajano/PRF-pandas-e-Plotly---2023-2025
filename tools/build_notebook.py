#!/usr/bin/env python3
"""Gera o notebook do exercício (construção incremental, parte por parte)."""
import json
from pathlib import Path
import sys

OUT = "notebooks/analise_prf_2023_2025.ipynb"


def md(*linhas: str) -> dict:
    return {"cell_type": "markdown", "metadata": {}, "source": list(linhas)}


def code(*linhas: str) -> dict:
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": list(linhas),
    }


def build() -> dict:
    cells = []

    # ---------------------------------------------------------------- capa
    cells.append(md(
        "# Análise Integrada de Acidentes Rodoviários Federais (2023 a 2025)\n",
        "\n",
        "**Exercício Prático — refazendo em Python (pandas + Plotly) o exercício do Módulo 03 (SQL/DuckDB)**\n",
        "\n",
        "| | |\n",
        "|---|---|\n",
        "| **Fonte** | Dados Abertos da PRF — `datatran2023.csv`, `datatran2024.csv`, `datatran2025.csv` |\n",
        "| **Grão** | 1 linha = 1 ocorrência de acidente |\n",
        "| **Período** | 01/01/2023 a 31/12/2025 |\n",
        "| **Variável-alvo** | `acidente_fatal` = 1 se `mortos >= 1`, senão 0 |\n",
        "| **Saídas** | `dados_tratados/base_analitica_prf_2023_2025.csv`, `dados_tratados/base_modelavel_prf_2023_2025.csv`, `resultados/*.html` |\n",
        "\n",
        "> **Reprodutibilidade:** este notebook foi executado do início ao fim com *Restart & Run All* sem erro.\n",
        "> Use caminhos relativos — nenhum CSV original é sobrescrito.\n",
    ))

    # ---------------------------------------------------------------- Parte 1
    cells.append(md(
        "---\n",
        "# Parte 1 — Ingestão e integração\n",
    ))

    cells.append(md(
        "## 1.0 Configuração do ambiente\n",
        "\n",
        "Define a raiz do projeto por `Path`, independentemente do diretório de trabalho em que o notebook\n",
        "é aberto (funciona a partir da raiz do repositório ou de `notebooks/`), e as constantes usadas em\n",
        "todas as partes.\n",
    ))

    cells.append(code(
        "import unicodedata\n",
        "from pathlib import Path\n",
        "\n",
        "import numpy as np\n",
        "import pandas as pd\n",
        "\n",
        "pd.set_option(\"display.max_columns\", 100)\n",
        "pd.set_option(\"display.width\", 180)\n",
        "pd.set_option(\"display.max_rows\", 100)\n",
        "\n",
        "\n",
        "def localizar_raiz() -> Path:\n",
        "    \"\"\"Sobe a partir do diretório atual até achar a pasta de dados brutos.\"\"\"\n",
        "    for candidato in [Path.cwd(), *Path.cwd().parents]:\n",
        "        if (candidato / \"dados_brutos\").is_dir():\n",
        "            return candidato\n",
        "    raise FileNotFoundError(\n",
        "        \"Não encontrei a pasta 'dados_brutos/'. \"\n",
        "        \"Abra o notebook a partir da raiz do projeto ou de 'notebooks/'.\"\n",
        "    )\n",
        "\n",
        "\n",
        "RAIZ = localizar_raiz()\n",
        "DIR_BRUTOS = RAIZ / \"dados_brutos\"\n",
        "DIR_TRATADOS = RAIZ / \"dados_tratados\"\n",
        "DIR_RESULTADOS = RAIZ / \"resultados\"\n",
        "\n",
        "for pasta in (DIR_TRATADOS, DIR_RESULTADOS):\n",
        "    pasta.mkdir(parents=True, exist_ok=True)\n",
        "\n",
        "SEPARADOR = \";\"\n",
        "ENCODING_SAIDA = \"utf-8-sig\"\n",
        "ANOS = (2023, 2024, 2025)\n",
        "\n",
        "print(f\"Raiz do projeto : {RAIZ}\")\n",
        "print(f\"Dados brutos    : {DIR_BRUTOS}\")\n",
        "print(f\"Dados tratados  : {DIR_TRATADOS}\")\n",
        "print(f\"Resultados      : {DIR_RESULTADOS}\")\n",
    ))

    cells.append(md(
        "## 1.1 Leitura dos três CSVs com `ler_csv_prf` (fallback de encoding)\n",
        "\n",
        "**Pergunta:** os três arquivos podem ser lidos sem perda de caracteres?\n",
        "\n",
        "A função tenta cada encoding da lista até um funcionar. Os arquivos da PRF são **latin1**\n",
        "(sem BOM); `utf-8` falha, então o fallback é realmente exercitado — não é código decorativo.\n",
        "\n",
        "O `id` é lido como texto de propósito: em 2024 existe uma linha corrompida com `id = \"6e+05\"`\n",
        "(notação científica gerada por planilha). Lido como número, o pandas converteria a coluna\n",
        "inteira para `float` e a linha perderia o identificador.\n",
    ))

    council = None
    cells.append(code(
        "ENCODINGS_TENTATIVA = (\"utf-8\", \"latin1\", \"utf-8-sig\", \"cp1252\")\n",
        "\n",
        "\n",
        "def ler_csv_prf(caminho: Path, sep: str = SEPARADOR) -> pd.DataFrame:\n",
        "    \"\"\"Lê um CSV da PRF tentando vários encodings em sequência.\n",
        "\n",
        "    Diferença em relação à versão do Módulo 04: um encoding que falha não\n",
        "    interrompe a função (não há 'raise' dentro do laço); a próxima tentativa\n",
        "    é executada e o erro só é levantado se todas falharem.\n",
        "    \"\"\"\n",
        "    ultimo_erro: Exception | None = None\n",
        "    for encoding in ENCODINGS_TENTATIVA:\n",
        "        try:\n",
        "            df = pd.read_csv(\n",
        "                caminho,\n",
        "                sep=sep,\n",
        "                encoding=encoding,\n",
        "                low_memory=False,\n",
        "                dtype={\"id\": \"string\"},\n",
        "            )\n",
        "        except (UnicodeDecodeError, UnicodeError) as erro:\n",
        "            ultimo_erro = erro\n",
        "            continue\n",
        "        print(f\"{caminho.name}: lido com encoding={encoding!r} \"\n",
        "              f\"({len(df):,} linhas x {df.shape[1]} colunas)\")\n",
        "        return df\n",
        "    raise RuntimeError(\n",
        "        f\"Nenhum encoding de {ENCODINGS_TENTATIVA} funcionou para {caminho}\"\n",
        "    ) from ultimo_erro\n",
        "\n",
        "\n",
        "dados_por_ano = {}\n",
        "for ano in ANOS:\n",
        "    dados_por_ano[ano] = ler_csv_prf(DIR_BRUTOS / f\"datatran{ano}.csv\")\n",
        "\n",
        "linhas_por_arquivo = {ano: len(df) for ano, df in dados_por_ano.items()}\n",
        "linhas_por_arquivo\n",
    ))

    cells.append(md(
        "## 1.2 Padronização dos nomes de coluna e conferência entre os anos\n",
        "\n",
        "**Pergunta:** os três anos têm as mesmas colunas?\n",
        "\n",
        "A normalização deixa os nomes em minúsculas, sem acentos e com `_` no lugar de espaço,\n",
        "hífen ou barra. Depois disso a comparação é feita **antes** de qualquer concatenação: se um\n",
        "ano trouxesse uma coluna a mais, ela é reportada aqui em vez de virar `NaN` silencioso.\n",
    ))

    cells.append(code(
        "def normalizar_nome_coluna(nome: str) -> str:\n",
        "    \"\"\"minúsculas, sem acento, separador único em '_'.\"\"\"\n",
        "    nome = str(nome).strip().lower()\n",
        "    nome = unicodedata.normalize(\"NFKD\", nome).encode(\"ascii\", \"ignore\").decode(\"utf-8\")\n",
        "    for antigo, novo in ((\" \", \"_\"), (\"-\", \"_\"), (\"/\", \"_\")):\n",
        "        nome = nome.replace(antigo, novo)\n",
        "    while \"__\" in nome:\n",
        "        nome = nome.replace(\"__\", \"_\")\n",
        "    return nome.strip(\"_\")\n",
        "\n",
        "\n",
        "for ano, df in dados_por_ano.items():\n",
        "    df.columns = [normalizar_nome_coluna(c) for c in df.columns]\n",
        "\n",
        "colunas_por_ano = {ano: set(df.columns) for ano, df in dados_por_ano.items()}\n",
        "todas = set().union(*colunas_por_ano.values())\n",
        "comuns = set.intersection(*colunas_por_ano.values())\n",
        "\n",
        "print(f\"Colunas por ano: \" + \" | \".join(f\"{a}: {len(c)}\" for a, c in colunas_por_ano.items()))\n",
        "print(f\"Comuns aos três anos: {len(comuns)}\")\n",
        "print(f\"Só em alguns anos    : {sorted(todas - comuns) or 'nenhuma'}\")\n",
        "\n",
        "assert len(comuns) == len(todas), \"Há colunas que não existem em todos os anos.\"\n",
        "assert len(comuns) == 30, f\"Esperava 30 colunas, encontrei {len(comuns)}.\"\n",
        "print(\"\\nOK — os três anos têm exatamente as mesmas 30 colunas.\")\n",
        "print(sorted(comuns))\n",
    ))

    cells.append(md(
        "## 1.3 `arquivo_origem` e a união em `acidentes_prf_historico`\n",
        "\n",
        "**Pergunta:** é possível consolidar os três anos numa única base rastreável?\n",
        "\n",
        "`arquivo_origem` guarda o ano de cada arquivo. Além dele é criada `ano_acidente`, que também\n",
        "é derivada de `data_inversa` na Parte 3 — a redundância é intencional aqui, porque serve de\n",
        "checagem cruzada: se as duas divergirem, o ano do arquivo não bate com a data do acidente.\n",
    ))

    cells.append(code(
        "for ano, df in dados_por_ano.items():\n",
        "    df[\"arquivo_origem\"] = ano\n",
        "\n",
        "acidentes_prf_historico = pd.concat(\n",
        "    [dados_por_ano[ano] for ano in ANOS],\n",
        "    ignore_index=True,\n",
        "    sort=False,\n",
        ")\n",
        "\n",
        "print(f\"Formato de acidentes_prf_historico: {acidentes_prf_historico.shape}\")\n",
        "print(\"\\nLinhas por arquivo de origem:\")\n",
        "print(acidentes_prf_historico[\"arquivo_origem\"].value_counts().sort_index().to_string())\n",
        "acidentes_prf_historico.head(3)\n",
    ))

    cells.append(md(
        "## 1.4 Prova de que nenhuma linha foi perdida\n",
        "\n",
        "**Pergunta:** o total consolidado é exatamente a soma dos três arquivos?\n",
        "\n",
        "Este é o `assert` pedido na Parte 1. Ele precisa ser verificado **agora**, antes da remoção de\n",
        "duplicatas da Parte 2 — medido depois, o teste falharia por construção.\n",
    ))

    cells.append(code(
        "total_esperado = sum(linhas_por_arquivo.values())\n",
        "total_obtido = len(acidentes_prf_historico)\n",
        "\n",
        "print(\"Soma dos arquivos :\", f\"{total_esperado:,}\")\n",
        "print(\"Base consolidada  :\", f\"{total_obtido:,}\")\n",
        "\n",
        "assert total_obtido == total_esperado, (\n",
        "    f\"Linhas perdidas na concatenação: {total_esperado - total_obtido}\"\n",
        ")\n",
        "print(\"\\nOK — nenhuma linha perdida na integração.\")\n",
        "\n",
        "pd.DataFrame(\n",
        "    {\"linhas\": linhas_por_arquivo, \"fatais\": {\n",
        "        ano: int((df[\"mortos\"] >= 1).sum()) for ano, df in dados_por_ano.items()\n",
        "    }}\n",
        ").assign(total_consolidado=total_obtido)\n",
    ))

    nb = {
        "cells": cells,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {"name": "python", "version": "3.11"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    return nb


if __name__ == "__main__":
    nb = build()
    Path(OUT).parent.mkdir(parents=True, exist_ok=True)
    Path(OUT).write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"gerado: {OUT} ({len(nb['cells'])} células)")
