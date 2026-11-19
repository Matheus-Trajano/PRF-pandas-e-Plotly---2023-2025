#!/usr/bin/env python3
"""Gera os notebooks do exercício (construção incremental, parte por parte).

Uso:  python tools/build_notebooks.py
"""
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DIR_NB = RAIZ / "notebooks"


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


def gravar(nome: str, cells: list, *, titulo: str) -> None:
    nb = {
        "cells": cells,
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "version": "3.11"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    destino = DIR_NB / nome
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"gerado: {destino.relative_to(RAIZ)} ({len(cells)} células) — {titulo}")


# --------------------------------------------------------------------------- #
# 00 — setup compartilhado (mesmo conteúdo em ambos os notebooks)
# --------------------------------------------------------------------------- #
def celulas_setup() -> list:
    return [
        md(
            "## 0. Configuração do ambiente\n",
            "\n",
            "Resolve a raiz do projeto por `Path` (funciona aberto da raiz do repositório ou de\n",
            "`notebooks/`) e define as constantes usadas nas partes.\n",
        ),
        code(
            "import unicodedata\n",
            "from pathlib import Path\n",
            "\n",
            "import numpy as np\n",
            "import pandas as pd\n",
            "\n",
            "pd.set_option(\"display.max_columns\", 100)\n",
            "pd.set_option(\"display.width\", 180)\n",
            "pd.set_option(\"display.max_rows\", 120)\n",
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
            "ENCODINGS_TENTATIVA = (\"utf-8\", \"latin1\", \"utf-8-sig\", \"cp1252\")\n",
            "ANOS = (2023, 2024, 2025)\n",
            "\n",
            "print(f\"Raiz do projeto : {RAIZ}\")\n",
            "print(f\"Dados brutos    : {DIR_BRUTOS}\")\n",
            "print(f\"Dados tratados  : {DIR_TRATADOS}\")\n",
            "print(f\"Resultados      : {DIR_RESULTADOS}\")\n",
        ),
    ]


# --------------------------------------------------------------------------- #
# 01 — Parte 1: ingestão e integração
# --------------------------------------------------------------------------- #
NORM_COLUNA = (
    "def normalizar_nome_coluna(nome: str) -> str:\n",
    "    \"\"\"minúsculas, sem acento, separador único em '_'.\"\"\"\n",
    "    nome = str(nome).strip().lower()\n",
    "    nome = unicodedata.normalize(\"NFKD\", nome).encode(\"ascii\", \"ignore\").decode(\"utf-8\")\n",
    "    for antigo, novo in ((\" \", \"_\"), (\"-\", \"_\"), (\"/\", \"_\")):\n",
    "        nome = nome.replace(antigo, novo)\n",
    "    while \"__\" in nome:\n",
    "        nome = nome.replace(\"__\", \"_\")\n",
    "    return nome.strip(\"_\")\n",
)

LER_CSV = (
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
    "                caminho, sep=sep, encoding=encoding, low_memory=False,\n",
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
)


def notebook_parte1() -> list:
    cells = [
        md(
            "# Parte 1 — Ingestão e integração\n",
            "\n",
            "**Exercício Prático — Análise Integrada de Acidentes Rodoviários Federais (2023 a 2025)**\n",
            "\n",
            "| | |\n",
            "|---|---|\n",
            "| **Fonte** | Dados Abertos da PRF — `datatran2023.csv`, `datatran2024.csv`, `datatran2025.csv` |\n",
            "| **Grão** | 1 linha = 1 ocorrência de acidente |\n",
            "| **Saída desta parte** | `acidentes_prf_historico` (DataFrame em memória) |\n",
            "\n",
            "> Notebook executado com *Restart & Run All* sem erro. Caminhos relativos; nenhum CSV original é sobrescrito.\n",
        ),
    ]
    cells += celulas_setup()

    cells.append(md(
        "## 1.1 Leitura dos três CSVs com `ler_csv_prf` (fallback de encoding)\n",
        "\n",
        "**Pergunta:** os três arquivos podem ser lidos sem perda de caracteres?\n",
        "\n",
        "A função tenta cada encoding da lista até um funcionar. Os arquivos da PRF são **latin1**\n",
        "(sem BOM); `utf-8` falha, então o fallback é realmente exercitado — não é código decorativo.\n",
        "\n",
        "O `id` é lido como texto de propósito: em 2024 existe uma linha com `id = \"6e+05\"`\n",
        "(notação científica gerada por planilha). Lido como número, o pandas converteria a coluna\n",
        "inteira para `float` e essa linha perderia o identificador.\n",
    ))
    cells.append(code(*LER_CSV, "\n",
        "dados_por_ano = {ano: ler_csv_prf(DIR_BRUTOS / f\"datatran{ano}.csv\") for ano in ANOS}\n",
        "linhas_por_arquivo = {ano: len(df) for ano, df in dados_por_ano.items()}\n",
        "linhas_por_arquivo\n",
    ))

    cells.append(md(
        "## 1.2 Padronização dos nomes e conferência de schema entre os anos\n",
        "\n",
        "**Pergunta:** os três anos têm as mesmas colunas?\n",
        "\n",
        "A comparação é feita **antes** da concatenação: se um ano trouxesse coluna a mais ou a menos,\n",
        "ela aparece aqui em vez de virar `NaN` silencioso.\n",
    ))
    cells.append(code(*NORM_COLUNA, "\n",
        "for df in dados_por_ano.values():\n",
        "    df.columns = [normalizar_nome_coluna(c) for c in df.columns]\n",
        "\n",
        "colunas_por_ano = {ano: set(df.columns) for ano, df in dados_por_ano.items()}\n",
        "todas = set().union(*colunas_por_ano.values())\n",
        "comuns = set.intersection(*colunas_por_ano.values())\n",
        "\n",
        "print(\"Colunas por ano: \" + \" | \".join(f\"{a}: {len(c)}\" for a, c in colunas_por_ano.items()))\n",
        "print(f\"Comuns aos três anos: {len(comuns)}\")\n",
        "print(f\"Só em alguns anos    : {sorted(todas - comuns) or 'nenhuma'}\")\n",
        "\n",
        "assert len(comuns) == len(todas), \"Há colunas que não existem em todos os anos.\"\n",
        "assert len(comuns) == 30, f\"Esperava 30 colunas, encontrei {len(comuns)}.\"\n",
        "print(\"\\nOK — os três anos têm exatamente as mesmas 30 colunas.\")\n",
    ))

    cells.append(md(
        "## 1.3 `arquivo_origem` e a união em `acidentes_prf_historico`\n",
        "\n",
        "**Pergunta:** é possível consolidar os três anos numa única base rastreável?\n",
        "\n",
        "`arquivo_origem` guarda o ano do arquivo. Na Parte 3 será criada `ano_acidente`, derivada de\n",
        "`data_inversa`; as duas existindo, dá para checar se algum registro está no arquivo errado.\n",
    ))
    cells.append(code(
        "for ano, df in dados_por_ano.items():\n",
        "    df[\"arquivo_origem\"] = ano\n",
        "\n",
        "acidentes_prf_historico = pd.concat(\n",
        "    [dados_por_ano[ano] for ano in ANOS], ignore_index=True, sort=False\n",
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
        "O `assert` precisa ser verificado **agora**, antes da remoção de duplicatas da Parte 2 —\n",
        "medido depois, o teste falharia por construção.\n",
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
        "pd.DataFrame({\n",
        "    \"linhas\": linhas_por_arquivo,\n",
        "    \"fatais\": {ano: int((df[\"mortos\"] >= 1).sum()) for ano, df in dados_por_ano.items()},\n",
        "})\n",
    ))
    return cells


# --------------------------------------------------------------------------- #
# 02 — Parte 2: diagnóstico, limpeza e validador de domínio
# --------------------------------------------------------------------------- #
def notebook_parte2() -> list:
    cells = [
        md(
            "# Parte 2 — Diagnóstico, limpeza e validação de domínio\n",
            "\n",
            "| | |\n",
            "|---|---|\n",
            "| **Entrada** | os três CSVs em `dados_brutos/` |\n",
            "| **Saída desta parte** | `df_limpo` (DataFrame em memória) + relatório de qualidade |\n",
            "\n",
            "> Notebook executado com *Restart & Run All* sem erro. Caminhos relativos; nenhum CSV original é sobrescrito.\n",
            "\n",
            "**Escopo:** 2.1 diagnóstico (nulos, duplicatas), 2.2 conversão de tipos, 2.3 padronização de\n",
            "textos com validação contra o dicionário da PRF, 2.4 remoção das colunas de localidade fina.\n",
        ),
    ]
    cells += celulas_setup()

    cells.append(md(
        "## 2.0 Reconstrução da base consolidada\n",
        "\n",
        "Este notebook é autônomo: refaz a leitura e a concatenação da Parte 1 para poder rodar isolado.\n",
    ))
    cells.append(code(*LER_CSV, "\n", *NORM_COLUNA, "\n",
        "dados_por_ano = {}\n",
        "for ano in ANOS:\n",
        "    df = ler_csv_prf(DIR_BRUTOS / f\"datatran{ano}.csv\")\n",
        "    df.columns = [normalizar_nome_coluna(c) for c in df.columns]\n",
        "    df[\"arquivo_origem\"] = ano\n",
        "    dados_por_ano[ano] = df\n",
        "\n",
        "acidentes_prf_historico = pd.concat(\n",
        "    [dados_por_ano[ano] for ano in ANOS], ignore_index=True, sort=False\n",
        ")\n",
        "linhas_na_integracao = len(acidentes_prf_historico)\n",
        "\n",
        "assert linhas_na_integracao == sum(len(d) for d in dados_por_ano.values())\n",
        "print(f\"\\nBase consolidada: {acidentes_prf_historico.shape}\")\n",
    ))

    cells.append(md(
        "## 2.1 Diagnóstico: `info()`, nulos e duplicidades\n",
        "\n",
        "**Pergunta:** o que a base tem de sujeira estrutural?\n",
        "\n",
        "O diagnóstico vem **antes** de qualquer alteração, para que o relatório descreva o dado\n",
        "original e não o já tratado.\n",
    ))
    cells.append(code(
        "print(\"=\" * 70)\n",
        "print(\"INFO\")\n",
        "print(\"=\" * 70)\n",
        "acidentes_prf_historico.info(memory_usage=\"deep\", show_counts=True)\n",
        "\n",
        "print(\"\\n\" + \"=\" * 70)\n",
        "print(\"TIPOS DE DADOS\")\n",
        "print(\"=\" * 70)\n",
        "resumo_tipos = (\n",
        "    acidentes_prf_historico.dtypes.astype(str)\n",
        "    .value_counts().rename_axis(\"tipo\").reset_index(name=\"qtd_colunas\")\n",
        ")\n",
        "display(resumo_tipos)\n",
    ))

    cells.append(code(
        "nulos = pd.DataFrame({\n",
        "    \"qtd_nulos\": acidentes_prf_historico.isna().sum(),\n",
        "    \"perc_nulos\": acidentes_prf_historico.isna().mean().mul(100).round(4),\n",
        "}).sort_values(\"perc_nulos\", ascending=False)\n",
        "\n",
        "print(f\"Colunas com pelo menos um nulo: {(nulos['qtd_nulos'] > 0).sum()} de {len(nulos)}\")\n",
        "display(nulos[nulos[\"qtd_nulos\"] > 0])\n",
    ))

    cells.append(md(
        "### Duplicidades exatas\n",
        "\n",
        "**Pergunta:** existem linhas 100% idênticas?\n",
        "\n",
        "A remoção é executada mesmo que o resultado seja zero — é o item pedido pelo exercício, e o\n",
        "notebook declara explicitamente quantas linhas saíram. Nesta base os três arquivos já vêm sem\n",
        "duplicatas exatas, então a operação remove **0 linhas** e o total não muda.\n",
    ))
    cells.append(code(
        "qtd_duplicadas = int(acidentes_prf_historico.duplicated().sum())\n",
        "print(f\"Duplicidades exatas encontradas: {qtd_duplicadas:,}\")\n",
        "\n",
        "df_deduplicado = acidentes_prf_historico.drop_duplicates().copy()\n",
        "removidas = len(acidentes_prf_historico) - len(df_deduplicado)\n",
        "\n",
        "print(f\"Linhas removidas              : {removidas:,}\")\n",
        "print(f\"Formato antes                 : {acidentes_prf_historico.shape}\")\n",
        "print(f\"Formato depois                : {df_deduplicado.shape}\")\n",
        "\n",
        "assert removidas == qtd_duplicadas\n",
        "assert len(df_deduplicado) == len(acidentes_prf_historico) - qtd_duplicadas\n",
        "\n",
        "if removidas == 0:\n",
        "    print(\"\\nNenhuma duplicidade exata: a base já estava sem repetição integral de linha.\")\n",
    ))

    cells.append(md(
        "### Duplicidade de chave: `id`\n",
        "\n",
        "**Pergunta:** o identificador de ocorrência se repete, dentro do ano ou entre anos?\n",
        "\n",
        "A chave lógica é `(arquivo_origem, id)`, não `id` sozinho. Também registro o caso do `id`\n",
        "corrompido (`6e+05`, em 2024), que não é duplicata, mas é uma perda de identificador.\n",
    ))
    cells.append(code(
        "chave = acidentes_prf_historico[[\"arquivo_origem\", \"id\"]]\n",
        "print(f\"Duplicidade em (arquivo_origem, id): {int(chave.duplicated().sum())}\")\n",
        "print(f\"Duplicidade em id isolado          : {int(acidentes_prf_historico['id'].duplicated().sum())}\")\n",
        "\n",
        "ids_invalidos = acidentes_prf_historico[\n",
        "    ~acidentes_prf_historico[\"id\"].fillna(\"\").str.strip().str.fullmatch(r\"\\d+\")\n",
        "]\n",
        "print(f\"\\nIDs não numéricos (sinalizados, NÃO descartados): {len(ids_invalidos)}\")\n",
        "display(ids_invalidos[[\"id\", \"data_inversa\", \"uf\", \"municipio\", \"arquivo_origem\"]])\n",
    ))

    cells.append(md(
        "## 2.2 Conversão de tipos\n",
        "\n",
        "**Pergunta:** quais colunas são numéricas ou de data e precisam de conversão?\n",
        "\n",
        "Dois cuidados que o dado exige:\n",
        "\n",
        "1. **Decimal com vírgula** (`km = \"546,2\"`, `latitude = \"-23,48586772\"`).\n",
        "2. **`data_inversa` é ISO (`yyyy-mm-dd`)**, não `dd/mm/yyyy`. Usar `%d/%m/%Y` transformaria\n",
        "   as 213.497 datas em `NaT`.\n",
        "\n",
        "Toda conversão é registrada numa tabela de não-convertidos: se algo falhar, aparece em vez de\n",
        "virar `NaN` silencioso.\n",
    ))
    cells.append(code(
        "COLUNAS_NUMERICAS = [\n",
        "    \"br\", \"km\", \"pessoas\", \"mortos\", \"feridos\", \"feridos_leves\",\n",
        "    \"feridos_graves\", \"ilesos\", \"ignorados\", \"veiculos\",\n",
        "    \"latitude\", \"longitude\",\n",
        "]\n",
        "\n",
        "df_limpo = df_deduplicado.copy()\n",
        "diagnostico_conversao = []\n",
        "\n",
        "for coluna in COLUNAS_NUMERICAS:\n",
        "    original = df_limpo[coluna]\n",
        "    texto = original.astype(\"string\").str.strip().str.replace(\",\", \".\", regex=False)\n",
        "    convertido = pd.to_numeric(texto, errors=\"coerce\")\n",
        "    df_limpo[coluna] = convertido\n",
        "    diagnostico_conversao.append({\n",
        "        \"coluna\": coluna,\n",
        "        \"convertidos\": int(convertido.notna().sum()),\n",
        "        \"nao_convertidos\": int(convertido.isna().sum() - original.isna().sum()),\n",
        "    })\n",
        "\n",
        "df_limpo[\"data_inversa\"] = pd.to_datetime(\n",
        "    df_limpo[\"data_inversa\"], format=\"%Y-%m-%d\", errors=\"coerce\"\n",
        ")\n",
        "\n",
        "diag = pd.DataFrame(diagnostico_conversao)\n",
        "diag.loc[len(diag)] = {\n",
        "    \"coluna\": \"data_inversa\",\n",
        "    \"convertidos\": int(df_limpo[\"data_inversa\"].notna().sum()),\n",
        "    \"nao_convertidos\": int(df_limpo[\"data_inversa\"].isna().sum()),\n",
        "}\n",
        "\n",
        "display(diag)\n",
        "assert diag[\"nao_convertidos\"].sum() == 0, \"Há valores que não puderam ser convertidos.\"\n",
        "print(\"OK — todas as colunas numéricas e a data foram convertidas sem perda.\")\n",
    ))

    cells.append(md(
        "## 2.3 Padronização de textos e validação de domínio\n",
        "\n",
        "**Pergunta:** existe valor com formatação inválida ou fora do dicionário da PRF?\n",
        "\n",
        "Esta é a etapa pedida no exercício (\"padronize textos, nulos de categorias como `IGNORADO`\"),\n",
        "implementada como **validador**: em vez de só aplicar `strip`/`upper` no escuro, o notebook\n",
        "confere cada coluna categórica contra o domínio esperado e registra toda substituição.\n",
        "\n",
        "### 2.3.1 Limpeza de formatação\n",
        "\n",
        "Remove espaços nas pontas, espaços duplicados no meio e caracteres invisíveis\n",
        "(espaço não separável, zero-width). Esses defeitos existem na fonte: `municipio` tem\n",
        "32 linhas com espaço duplo (ex.: `SAO SEBASTIAO DE LAGOA DE  ROCA`).\n",
    ))
    cells.append(code(
        "def limpar_espacos(serie: pd.Series) -> pd.Series:\n",
        "    \"\"\"Remove espaço nas pontas, espaço duplicado no meio e caracteres invisíveis.\"\"\"\n",
        "    return (\n",
        "        serie.astype(\"string\")\n",
        "        .str.replace(r\"[\\u00a0\\u200b\\u200e\\u200f]\", \" \", regex=True)\n",
        "        .str.strip()\n",
        "        .str.replace(r\"\\s{2,}\", \" \", regex=True)\n",
        "    )\n",
        "\n",
        "\n",
        "# Em pandas 3, colunas de texto têm dtype 'str' (antes eram 'object');\n",
        "# 'string' é o StringDtype opcional. As três formas precisam ser aceitas.\n",
        "def eh_texto(serie: pd.Series) -> bool:\n",
        "    return str(serie.dtype) in (\"object\", \"string\", \"str\")\n",
        "\n",
        "\n",
        "COLUNAS_TEXTO = [c for c in df_limpo.columns if eh_texto(df_limpo[c])]\n",
        "print(f\"Colunas de texto detectadas ({len(COLUNAS_TEXTO)}): {COLUNAS_TEXTO}\")\n",
        "\n",
        "registro_formatacao = []\n",
        "for coluna in COLUNAS_TEXTO:\n",
        "    antes = df_limpo[coluna]\n",
        "    depois = limpar_espacos(antes)\n",
        "    alteradas = int((antes.notna() & (antes != depois)).sum())\n",
        "    if alteradas:\n",
        "        registro_formatacao.append({\"coluna\": coluna, \"linhas_alteradas\": alteradas})\n",
        "    df_limpo[coluna] = depois\n",
        "\n",
        "if registro_formatacao:\n",
        "    display(pd.DataFrame(registro_formatacao))\n",
        "else:\n",
        "    print(\"Nenhuma alteração de espaçamento necessária.\")\n",
        "\n",
        "print(\"\\nExemplo de município corrigido (se havia espaço duplo):\")\n",
        "exemplo = df_limpo[df_limpo[\"municipio\"].str.contains(\"LAGOA DE ROCA\", na=False)]\n",
        "display(exemplo[[\"uf\", \"municipio\"]].drop_duplicates().head(3))\n",
        "if exemplo.empty:\n",
        "    print(\"Nenhum município com esse padrão na base.\")\n",
    ))

    cells.append(md(
        "### 2.3.2 Dicionário de domínio das categóricas controladas\n",
        "\n",
        "Domínio esperado por coluna, conforme o dicionário de dados da PRF. `None` significa\n",
        "\"vocabulário aberto\" — nesse caso só se verifica formatação, não pertencimento.\n",
        "\n",
        "A comparação é tolerante a caixa: um valor como `plena noite` seria **normalizado** para\n",
        "`Plena Noite` em vez de virar `IGNORADO` — é correção de forma, não de conteúdo.\n",
    ))
    cells.append(code(
        "DOMINIOS = {\n",
        "    \"fase_dia\": {\"Amanhecer\", \"Anoitecer\", \"Plena Noite\", \"Pleno dia\"},\n",
        "    \"tipo_pista\": {\"Dupla\", \"Múltipla\", \"Simples\"},\n",
        "    \"uso_solo\": {\"Não\", \"Sim\"},\n",
        "    \"sentido_via\": {\"Crescente\", \"Decrescente\", \"Não Informado\"},\n",
        "    \"classificacao_acidente\": {\"Com Vítimas Fatais\", \"Com Vítimas Feridas\", \"Sem Vítimas\"},\n",
        "    \"dia_semana\": {\n",
        "        \"domingo\", \"segunda-feira\", \"terça-feira\", \"quarta-feira\",\n",
        "        \"quinta-feira\", \"sexta-feira\", \"sábado\",\n",
        "    },\n",
        "    # vocabulário aberto: só formatação\n",
        "    \"causa_acidente\": None,\n",
        "    \"tipo_acidente\": None,\n",
        "    \"condicao_metereologica\": None,\n",
        "    \"tracado_via\": None,\n",
        "    \"municipio\": None,\n",
        "}\n",
        "\n",
        "UF_VALIDAS = {\n",
        "    \"AC\", \"AL\", \"AM\", \"AP\", \"BA\", \"CE\", \"DF\", \"ES\", \"GO\", \"MA\", \"MG\", \"MS\",\n",
        "    \"MT\", \"PA\", \"PB\", \"PE\", \"PI\", \"PR\", \"RJ\", \"RN\", \"RO\", \"RR\", \"RS\", \"SC\",\n",
        "    \"SE\", \"SP\", \"TO\",\n",
        "}\n",
        "DOMINIOS[\"uf\"] = UF_VALIDAS\n",
        "\n",
        "placeholder = pd.DataFrame({\n",
        "    \"coluna\": list(DOMINIOS),\n",
        "    \"dominio_fechado\": [d is not None for d in DOMINIOS.values()],\n",
        "    \"qtd_valores_aceitos\": [len(d) if d else np.nan for d in DOMINIOS.values()],\n",
        "})\n",
        "display(placeholder)\n",
    ))

    cells.append(md(
        "### 2.3.3 Validador: `validar_e_corrigir_dominio`\n",
        "\n",
        "Para cada coluna com domínio fechado:\n",
        "\n",
        "| Situação | Ação |\n",
        "|---|---|\n",
        "| Valor nulo (`NaN`/vazio) | → `IGNORADO` |\n",
        "| Difere do domínio só por caixa ou acento | → normaliza para o rótulo canônico |\n",
        "| Valor que não existe no domínio | → `IGNORADO` **e** registra o valor original |\n",
        "| Valor válido | mantém |\n",
        "\n",
        "O retorno é um log auditável: quantas linhas mudaram, por qual motivo e qual valor caiu em\n",
        "`IGNORADO`. Nada é substituído em silêncio.\n",
    ))
    cells.append(code(
        "LITERAL_IGNORADO = \"IGNORADO\"\n",
        "\n",
        "\n",
        "def _assinatura(valor: str) -> str:\n",
        "    \"\"\"Chave insensível a caixa, acento e pontuação.\"\"\"\n",
        "    valor = unicodedata.normalize(\"NFKD\", str(valor))\n",
        "    valor = valor.encode(\"ascii\", \"ignore\").decode(\"utf-8\")\n",
        "    return \"\".join(ch for ch in valor.lower() if ch.isalnum())\n",
        "\n",
        "\n",
        "def validar_e_corrigir_dominio(\n",
        "    base: pd.DataFrame, coluna: str, dominio: set[str] | None, *,\n",
        "    literal_ignorado: str = LITERAL_IGNORADO,\n",
        ") -> pd.DataFrame:\n",
        "    \"\"\"Valida uma categórica contra o domínio e devolve o log das correções.\n",
        "\n",
        "    Só atua em coluna com domínio fechado; para vocabulário aberto devolve\n",
        "    um log vazio (a formatação já foi tratada em 2.3.1).\n",
        "    \"\"\"\n",
        "    if dominio is None:\n",
        "        return pd.DataFrame(columns=[\"coluna\", \"motivo\", \"linhas\", \"valores\"])\n",
        "\n",
        "    canonical = {_assinatura(v): v for v in dominio}\n",
        "    serie = base[coluna]\n",
        "    novo = serie.copy()\n",
        "    eventos: dict[str, dict] = {}\n",
        "\n",
        "    for idx, valor in serie.items():\n",
        "        if pd.isna(valor) or str(valor).strip() == \"\":\n",
        "            novo.at[idx] = literal_ignorado\n",
        "            eventos.setdefault(\"nulo → IGNORADO\", {}).setdefault(\"valores\", set()).add(\"<vazio>\")\n",
        "            eventos[\"nulo → IGNORADO\"][\"linhas\"] = eventos[\"nulo → IGNORADO\"].get(\"linhas\", 0) + 1\n",
        "            continue\n",
        "        if valor in dominio:\n",
        "            continue\n",
        "        chave = _assinatura(valor)\n",
        "        if chave in canonical:\n",
        "            novo.at[idx] = canonical[chave]\n",
        "            eventos.setdefault(\"forma normalizada\", {}).setdefault(\"valores\", set()).add(\n",
        "                f\"{valor} → {canonical[chave]}\"\n",
        "            )\n",
        "            eventos[\"forma normalizada\"][\"linhas\"] = eventos[\"forma normalizada\"].get(\"linhas\", 0) + 1\n",
        "        else:\n",
        "            novo.at[idx] = literal_ignorado\n",
        "            eventos.setdefault(\"fora do domínio → IGNORADO\", {}).setdefault(\"valores\", set()).add(str(valor))\n",
        "            eventos[\"fora do domínio → IGNORADO\"][\"linhas\"] = eventos[\"fora do domínio → IGNORADO\"].get(\"linhas\", 0) + 1\n",
        "\n",
        "    base[coluna] = novo.astype(\"string\")\n",
        "\n",
        "    linhas_log = [\n",
        "        {\"coluna\": coluna, \"motivo\": motivo,\n",
        "         \"linhas\": dados[\"linhas\"],\n",
        "         \"valores\": \"; \".join(sorted(dados[\"valores\"]))[:120]}\n",
        "        for motivo, dados in eventos.items()\n",
        "    ]\n",
        "    return pd.DataFrame(linhas_log)\n",
    ))

    cells.append(md(
        "### 2.3.4 Teste do validador com valores inválidos injetados\n",
        "\n",
        "**Pergunta:** o validador realmente detecta problemas, ou apenas passa por tudo?\n",
        "\n",
        "Um validador que nunca acusa nada não é verificação. Este teste injeta numa cópia os quatro\n",
        "tipos de defeito (`nulo`, caixa errada, acento faltando, valor inexistente) e confere que cada\n",
        "um é classificado corretamente — sem tocar na base real.\n",
    ))
    cells.append(code(
        "amostra = pd.DataFrame({\n",
        "    \"fase_dia\": [\n",
        "        \"Plena Noite\",              # válido\n",
        "        \"plena noite\",              # caixa errada -> normaliza\n",
        "        \"Pleno Dia\",                # caixa errada -> normaliza para 'Pleno dia'\n",
        "        None,                       # nulo -> IGNORADO\n",
        "        \"Madrugada\",                # inexistente -> IGNORADO\n",
        "        \"Anoitecer \",               # espaço sobrando (já limpo em 2.3.1) -> válido\n",
        "    ]\n",
        "})\n",
        "\n",
        "log_teste = validar_e_corrigir_dominio(amostra, \"fase_dia\", DOMINIOS[\"fase_dia\"])\n",
        "display(log_teste)\n",
        "display(amostra.rename(columns={\"fase_dia\": \"resultado\"}))\n",
        "\n",
        "obtido = amostra[\"fase_dia\"].tolist()\n",
        "esperado = [\"Plena Noite\", \"Plena Noite\", \"Pleno dia\", \"IGNORADO\", \"IGNORADO\", \"Anoitecer\"]\n",
        "assert obtido == esperado, f\"Validador falhou.\\nesperado={esperado}\\nobtido={obtido}\"\n",
        "assert len(log_teste) == 3, \"Esperava 3 motivos distintos de correção.\"\n",
        "print(\"OK — o validador detecta e classifica os quatro tipos de defeito.\")\n",
    ))

    cells.append(md(
        "### 2.3.5 Execução do validador em todas as categóricas\n",
        "\n",
        "**Pergunta:** sobrou algum valor inválido depois da validação?\n",
        "\n",
        "Agora com a base real. Depois de aplicar, o notebook revalida: nenhuma coluna de domínio\n",
        "fechado pode conter valor nulo ou fora do dicionário (exceto o próprio `IGNORADO`).\n",
    ))
    cells.append(code(
        "logs = []\n",
        "for coluna, dominio in DOMINIOS.items():\n",
        "    if coluna not in df_limpo.columns:\n",
        "        continue\n",
        "    log = validar_e_corrigir_dominio(df_limpo, coluna, dominio)\n",
        "    if not log.empty:\n",
        "        logs.append(log)\n",
        "\n",
        "log_dominio = (\n",
        "    pd.concat(logs, ignore_index=True) if logs\n",
        "    else pd.DataFrame(columns=[\"coluna\", \"motivo\", \"linhas\", \"valores\"])\n",
        ")\n",
        "\n",
        "print(f\"Total de substituições registradas: {int(log_dominio['linhas'].sum()) if len(log_dominio) else 0}\")\n",
        "display(log_dominio)\n",
    ))

    cells.append(code(
        "falhas = []\n",
        "for coluna, dominio in DOMINIOS.items():\n",
        "    if dominio is None or coluna not in df_limpo.columns:\n",
        "        continue\n",
        "    presentes = set(df_limpo[coluna].dropna().unique())\n",
        "    permitidos = set(dominio) | {LITERAL_IGNORADO}\n",
        "    invalidos = presentes - permitidos\n",
        "    nulos = int(df_limpo[coluna].isna().sum())\n",
        "    if invalidos or nulos:\n",
        "        falhas.append({\"coluna\": coluna, \"fora_do_dominio\": sorted(invalidos), \"nulos\": nulos})\n",
        "    print(f\"{coluna:<24} valores={len(presentes):>2} inválidos={len(invalidos):>2} nulos={nulos}\")\n",
        "\n",
        "assert not falhas, f\"Ainda há valores inválidos: {falhas}\"\n",
        "print(\"\\nOK — nenhuma categórica de domínio fechado tem valor inválido ou nulo.\")\n",
    ))

    cells.append(md(
        "### 2.3.6 Nulos das contagens → 0\n",
        "\n",
        "**Pergunta:** as contagens de vítimas têm nulos?\n",
        "\n",
        "Nenhuma tem (a base é completa), mas a regra é aplicada e verificada: `0` é o valor correto\n",
        "para \"nenhuma vítima\", e um `NaN` inflaria as médias e quebraria somas.\n",
    ))
    cells.append(code(
        "COLUNAS_CONTAGEM = [\"pessoas\", \"mortos\", \"feridos\", \"feridos_leves\",\n",
        "                    \"feridos_graves\", \"ilesos\", \"ignorados\", \"veiculos\"]\n",
        "\n",
        "nulos_antes = {c: int(df_limpo[c].isna().sum()) for c in COLUNAS_CONTAGEM}\n",
        "for c in COLUNAS_CONTAGEM:\n",
        "    df_limpo[c] = df_limpo[c].fillna(0).astype(\"int64\")\n",
        "nulos_depois = {c: int(df_limpo[c].isna().sum()) for c in COLUNAS_CONTAGEM}\n",
        "\n",
        "display(pd.DataFrame({\"nulos_antes\": nulos_antes, \"nulos_depois\": nulos_depois}))\n",
        "assert sum(nulos_depois.values()) == 0\n",
        "print(\"OK — contagens sem nulos e tipadas como inteiro.\")\n",
    ))

    cells.append(md(
        "## 2.4 Remoção das colunas de localidade fina\n",
        "\n",
        "**Pergunta:** quais colunas saem e o que permanece para localizar o acidente?\n",
        "\n",
        "Saem `latitude`, `longitude`, `regional`, `delegacia` e `uop` (localidade administrativa fina,\n",
        "com muitos nulos e sem uso nas análises). Permanecem `uf`, `br` e `municipio`, que são os\n",
        "níveis de agregação usados nas questões de negócio.\n",
    ))
    cells.append(code(
        "COLUNAS_REMOVER = [\"latitude\", \"longitude\", \"regional\", \"delegacia\", \"uop\"]\n",
        "presentes = [c for c in COLUNAS_REMOVER if c in df_limpo.columns]\n",
        "\n",
        "formato_antes = df_limpo.shape\n",
        "df_limpo = df_limpo.drop(columns=presentes)\n",
        "formato_depois = df_limpo.shape\n",
        "\n",
        "print(f\"Removidas : {presentes}\")\n",
        "print(f\"Formato   : {formato_antes} → {formato_depois}\")\n",
        "\n",
        "for obrigatoria in (\"uf\", \"br\", \"municipio\"):\n",
        "    assert obrigatoria in df_limpo.columns, f\"'{obrigatoria}' deveria ter sido mantida.\"\n",
        "for removida in COLUNAS_REMOVER:\n",
        "    assert removida not in df_limpo.columns, f\"'{removida}' deveria ter sido removida.\"\n",
        "\n",
        "print(f\"\\nColunas finais ({len(df_limpo.columns)}): {sorted(df_limpo.columns)}\")\n",
    ))

    cells.append(md(
        "## 2.5 Fechamento da Parte 2\n",
        "\n",
        "**Pergunta:** a base limpa preservou todas as ocorrências?\n",
        "\n",
        "A remoção de colunas muda a largura, nunca a altura. O `assert` garante que nenhuma linha foi\n",
        "perdida na limpeza.\n",
    ))
    cells.append(code(
        "assert len(df_limpo) == linhas_na_integracao, \"A limpeza alterou o número de linhas.\"\n",
        "\n",
        "resumo = pd.DataFrame([\n",
        "    {\"etapa\": \"base consolidada (Parte 1)\", \"linhas\": linhas_na_integracao,\n",
        "     \"colunas\": acidentes_prf_historico.shape[1]},\n",
        "    {\"etapa\": \"após deduplicação (2.1)\", \"linhas\": len(df_deduplicado),\n",
        "     \"colunas\": df_deduplicado.shape[1]},\n",
        "    {\"etapa\": \"df_limpo final (2.5)\", \"linhas\": len(df_limpo),\n",
        "     \"colunas\": df_limpo.shape[1]},\n",
        "])\n",
        "display(resumo)\n",
        "\n",
        "print(f\"Acidentes fatais preservados: {int((df_limpo['mortos'] >= 1).sum()):,}\")\n",
        "print(f\"Total de mortos preservado  : {int(df_limpo['mortos'].sum()):,}\")\n",
    ))
    return cells


def main() -> None:
    alvo = sys.argv[1] if len(sys.argv) > 1 else "todos"
    if alvo in ("todos", "1"):
        gravar("01_parte1_ingestao.ipynb", notebook_parte1(), titulo="Parte 1")
    if alvo in ("todos", "2"):
        gravar("02_parte2_limpeza.ipynb", notebook_parte2(), titulo="Parte 2")


if __name__ == "__main__":
    main()
