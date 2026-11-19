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
| 3 | Novas variáveis | `03_parte3_variaveis.ipynb` | ✅ concluída |
| 4 | Duas bases | `04_parte4_bases.ipynb` | ✅ concluída |
| 5 | Questões de negócio — Nível 1 (Q1–Q4) | `05_parte5_nivel1.ipynb` | ✅ concluída |
| 5 | Questões de negócio — Nível 2 (Q5–Q7) | `06_parte5_nivel2.ipynb` | ✅ concluída |
| 5 | Questões de negócio — Nível 3 (Q8–Q10) | `07_parte5_nivel3.ipynb` | ✅ concluída |
| 5 | Questões de negócio — Nível 4 (Q11–Q12) | ⏳ | ⏳ pendente |
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
│   ├── 02_parte2_limpeza.ipynb
│   ├── 03_parte3_variaveis.ipynb
│   ├── 04_parte4_bases.ipynb
│   ├── 05_parte5_nivel1.ipynb
│   ├── 06_parte5_nivel2.ipynb
│   └── 07_parte5_nivel3.ipynb
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

## Variáveis derivadas (Parte 3)

| Variável | Regra |
|---|---|
| `acidente_fatal` | 1 se `mortos >= 1`, senão 0 |
| `ano_acidente`, `mes_acidente` | extraídos de `data_inversa` |
| `fim_de_semana` | 1 se sábado ou domingo (`dt.day_of_week`) |
| `data_comemorativa` | Fim de Ano (20/12–02/01) · Carnaval (janelas por ano) · Normal |
| `faixa_horaria` | blocos de 3h: `00h-03h` … `21h-24h`, fechado no início |

`df_enriquecido`: 213.497 linhas × 32 colunas · 15.293 acidentes fatais (7,16%) · zero violações da regra do alvo.

### Janelas usadas

| Período | Intervalo | Dias | Acidentes |
|---|---|---|---|
| Fim de Ano | 20/12 a 02/01 | 42 | 8.863 |
| Carnaval | 18–22/02/2023 · 10–14/02/2024 · 01–05/03/2025 | 15 | 2.897 |
| Normal | restante | 1.039 | 201.737 |

## As duas bases (Parte 4)

| Base | Linhas | Colunas | Uso |
|---|---|---|---|
| `base_analitica_prf_2023_2025.csv` | 213.497 | 32 | EDA, gráficos, Power BI |
| `base_modelavel_prf_2023_2025.csv` | 213.497 | 27 | modelagem, sem vazamento |

`base_modelavel` exclui as 5 colunas proibidas pelo exercício: `mortos`, `feridos`,
`feridos_leves`, `feridos_graves` e `classificacao_acidente`. Zero nulos.
Alvo: 15.293 fatais (7,16%).

As bases são gravadas com `;` e `utf-8-sig`, reabertas e conferidas com `assert` contra o
original (linhas, colunas e alvo). Ficam fora do versionamento (`dados_tratados/*.csv`) por
somarem ~97 MB — o notebook as regenera.

## Questões de negócio (Parte 5)

A Parte 5 é construída **um nível por vez**:

| Nível | Questões | Notebook |
|---|---|---|
| 1 — visão geral e temporal | Q1–Q4 | `05_parte5_nivel1.ipynb` |
| 2 — fatores de risco | Q5–Q7 | `06_parte5_nivel2.ipynb` |
| 3 — cruzamentos | Q8–Q10 | `07_parte5_nivel3.ipynb` |
| 4 — casos críticos | Q11–Q12 | pendente |

**Definição usada:** taxa de letalidade = **% de acidentes fatais do grupo** (conforme o
enunciado), sempre comparada à taxa global de **7,16%**. Cada questão declara o volume mínimo
aplicado e traz interpretação de 2–3 linhas, sem linguagem causal.

### Resultados do Nível 1

| Questão | Achado |
|---|---|
| Q1 | Taxa estável: 7,17% → 7,14% → 7,18% (0,014 p.p. de variação) |
| Q2 | Maio lidera (7,71%); maio–agosto acima da global; fevereiro menor (6,57%) |
| Q3 | Plena Noite 10,09% vs Pleno dia 5,02% — o dobro, com metade do volume |
| Q4 | Risco relativo fim de semana / dias úteis = **1,285** |

### Resultados do Nível 2

| Questão | Achado |
|---|---|
| Q5 | Colisão frontal (lift 4,16) e atropelamento de pedestre (lift 4,04) — 45% dos fatais |
| Q6 | Top 5 dominado por pedestre e contramão; álcool no pedestre 2,25 vs **álcool no condutor 0,63** |
| Q7 | Curva 8,19% > reta 7,35%, mas ponte (10,75%) e declive (9,85%) são piores; explode declarado como não-partição |

### Resultados do Nível 3

| Questão | Achado |
|---|---|
| Q8 | Letalidade quase igual nos três períodos (6,63%–7,40%); Fim de Ano tem +8,7% acidentes/dia e +25% mortos/dia; Carnaval não se distingue de dia normal |
| Q9 | Pista Simples (9,83%) mais que dobra a Dupla (4,69%) em **7 de 7** condições; pior célula Simples+Nevoeiro (13,95%); chuva com lift 0,86 |
| Q10 | Por **mortos**: BR-116 (1.190) e BR-101 (1.076); top 10 = 52,4% das mortes noturnas; só a BR-316 aparece também no ranking por taxa |

## Licença e fonte

Dados públicos da Polícia Rodoviária Federal (Dados Abertos).
