# Análise Integrada de Acidentes Rodoviários Federais (2023 a 2025) com Python

Análise dos acidentes registrados pela Polícia Rodoviária Federal (PRF) nos anos de
**2023, 2024 e 2025**, refazendo em Python (pandas + Plotly) o exercício de SQL/DuckDB
do Módulo 03, com as práticas dos Módulos 04 e 05.

---

## Status da construção

| Parte | Conteúdo | Notebook | Situação |
|---|---|---|---|
| 1 | Ingestão e integração | `01_parte1_ingestao.ipynb` | ✅ concluída |
| 2 | Diagnóstico, limpeza e validação de domínio | `02_parte2_limpeza.ipynb` | ✅ concluída |
| 3 | Novas variáveis | ⏳ | ⏳ pendente |
| 4 | Duas bases | ⏳ | ⏳ pendente |
| 5 | Questões de negócio (Q1–Q12) | ⏳ | ⏳ pendente |
| 6 | Gráficos | ⏳ | ⏳ pendente |
| 7 | Síntese | ⏳ | ⏳ pendente |

Cada parte tem seu próprio notebook, executável de forma independente com *Restart & Run All*.
Os notebooks seguem a numeração do exercício.

## Dados

Os arquivos de origem **não são versionados** (`.gitignore`) por serem volumosos.
Baixe-os em [Dados Abertos da PRF](https://www.gov.br/prf/pt-br/acesso-a-informacao/dados-abertos)
e coloque em `dados_brutos/` com exatamente estes nomes:

```
dados_brutos/
├── datatran2023.csv    # 67.766 linhas
├── datatran2024.csv    # 73.202 linhas
└── datatran2025.csv    # 72.529 linhas
```

| Característica | Valor |
|---|---|
| Separador | `;` |
| Encoding | **latin1** (sem BOM, quebra de linha CRLF) |
| Decimal | vírgula (`km = "546,2"`) |
| `data_inversa` | **ISO `yyyy-mm-dd`** (atenção: não é `dd/mm/yyyy`) |
| Grão | 1 linha = 1 ocorrência de acidente |

## Estrutura do repositório

```
.
├── dados_brutos/          # CSVs originais (não versionados)
├── dados_tratados/        # bases geradas pelos notebooks
├── notebooks/
│   ├── 01_parte1_ingestao.ipynb
│   └── 02_parte2_limpeza.ipynb
├── resultados/            # gráficos gerados pelo notebook
├── tools/
│   └── build_notebooks.py # gera os .ipynb a partir de uma fonte única
└── README.md
```

> Os notebooks são gerados por `tools/build_notebooks.py`. Edite o gerador e rode
> `python tools/build_notebooks.py` para atualizar os `.ipynb` — assim o código-fonte fica
> revisável em diff, sem o ruído de JSON de notebook.

## Como executar

```bash
pip install pandas numpy plotly jupyter
jupyter notebook notebooks/analise_prf_2023_2025.ipynb
```

Execute **Restart & Run All**. O notebook resolve a raiz do projeto por `Path`, então roda
tanto aberto da raiz do repositório quanto de dentro de `notebooks/`. Nenhum CSV original é
sobrescrito.

## Números de controle

Ao final da Parte 1 a base consolidada deve ter exatamente:

| Métrica | Valor |
|---|---|
| Linhas 2023 | 67.766 |
| Linhas 2024 | 73.202 |
| Linhas 2025 | 72.529 |
| **Total consolidado** | **213.497** |
| Acidentes fatais (`mortos >= 1`) | 4.858 + 5.225 + 5.210 = **15.293** |

O notebook verifica o total com `assert`; se a integração perder qualquer linha, a execução
falha em vez de seguir com um número errado.

## Decisões de engenharia

Registradas aqui porque desviam do material dos Módulos 04/05 e precisam de rastreabilidade.

**1. `ler_csv_prf` corrigida.** A versão do Módulo 04 fazia `raise` dentro do `except`, então a
primeira falha de encoding interrompia a função e o fallback nunca era tentado. Nesta versão o
laço continua para o próximo encoding e o erro só é levantado se todos falharem. Nos três
arquivos, `utf-8` falha e `latin1` funciona — o fallback é realmente exercitado.

**2. `data_inversa` é ISO, não `dd/mm/yyyy`.** O Módulo 04 usava `format="%d/%m/%Y"`, que
transformaria as 213.497 datas em `NaT`. O parse correto é `%Y-%m-%d`.

**3. `id` lido como texto.** O arquivo de 2024 tem uma linha com `id = "6e+05"` (linha 37.162,
notação científica gerada por planilha). Lido como número, o pandas converteria a coluna inteira
para `float` e essa linha perderia o identificador. Com `dtype={"id": "string"}` a anomalia fica
visível em vez de silenciosa. **A linha é preservada**, não descartada — descartá-la quebraria o
`assert` da Parte 1.4.

**4. `arquivo_origem` + `ano_acidente`.** As duas colunas existem: a primeira registra de qual
arquivo a linha veio, a segunda é derivada de `data_inversa` na Parte 3. A redundância é
proposital — se divergirem, há registro no arquivo errado.

**5. Duplicidades exatas.** Os três arquivos têm **zero** duplicatas. A remoção da Parte 2.1 é
executada mesmo assim (o exercício pede), e o notebook reporta "0 removidas" explicitamente.

**6. Verificação de linhas nulas ou inválidas.** A Parte 2.3 compara cada coluna categórica com
o domínio esperado da PRF (`DOMINIOS`) e substitui por `IGNORADO` toda linha cujo valor seja nulo
ou esteja fora desse domínio. O notebook registra quantas linhas foram corrigidas em cada coluna
e reconfere depois que nada sobrou (`assert`). `IGNORADO` é aceito como valor válido na
reconferência.

## Diagnóstico da base (Parte 2)

| Item | Resultado |
|---|---|
| Nulos | `uop` 155 · `delegacia` 91 · `regional` 19 · `classificacao_acidente` 3 |
| Duplicatas exatas | 0 (remoção executada, 0 removidas) |
| Espaços duplos corrigidos | 32 (`municipio`) |
| Linhas nulas/inválidas → `IGNORADO` | 3 (`classificacao_acidente`) |
| Não-convertidos em numéricas/data | 0 |
| Colunas após limpeza | 26 (saíram latitude, longitude, regional, delegacia, uop) |
| Linhas preservadas | 213.497 |

## Licença e fonte

Dados públicos da Polícia Rodoviária Federal (Dados Abertos).
