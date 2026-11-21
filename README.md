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
| 5 | Questões de negócio — Nível 4 (Q11–Q12) | `08_parte5_nivel4.ipynb` | ✅ concluída |
| 6 | Gráficos | `09_parte6_graficos.ipynb` | ✅ concluída |
| 7 | Síntese | `10_parte7_sintese.ipynb` | ✅ concluída |

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
│   ├── 07_parte5_nivel3.ipynb
│   ├── 08_parte5_nivel4.ipynb
│   ├── 09_parte6_graficos.ipynb
│   └── 10_parte7_sintese.ipynb
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
jupyter notebook notebooks/09_parte6_graficos.ipynb
```

Cada parte é um notebook próprio: abra o da parte que quer rodar e use **Restart & Run All**.
O notebook resolve a raiz do projeto por `Path`, então roda tanto aberto da raiz do
repositório quanto de dentro de `notebooks/`. Nenhum CSV original é sobrescrito.

Ordem de execução: as Partes 1 a 4 precisam de `dados_brutos/`; a Parte 4 gera as bases em
`dados_tratados/`; as Partes 5 e 6 leem essas bases. Para o **PNG** dos gráficos é preciso
`pip install kaleido` **e** o Chrome instalado — sem eles o notebook da Parte 6 salva só o
HTML e avisa no output, sem falhar.

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

**7. `strip` + `upper` só nos identificadores.** O enunciado da Parte 2 pede padronizar textos
com `strip` e `upper`. Verifiquei a fonte: `uf`, `br` e `municipio` já vêm **100% em caixa
alta**, então o `upper()` é aplicado de forma explícita e é comprovadamente inócuo — as duas
bases geradas têm MD5 idêntico antes e depois da mudança. As colunas **descritivas**
(`tipo_acidente`, `causa_acidente`, `fase_dia`, `classificacao_acidente`, `dia_semana`,
`tipo_pista`, `condicao_metereologica`) vêm em **caixa de título**, que é a forma publicada
pela PRF e a usada nos rótulos de todo o relatório; maiusculizá-las exigiria reescrever todos
os conjuntos `DOMINIOS` e todos os títulos das 12 questões sem acrescentar informação. O
`upper()` é guardado por dtype, para não tocar em `br` (que é numérico).

**8. Numeração das questões conforme o enunciado.** O enunciado oficial (PDF de 27/10/2026)
numera o Nível 3 como Q8 `tipo_pista` × clima, Q9 BRs em plena noite e Q10 feriados. A
primeira entrega da Parte 5 havia seguido outra ordem (feriados, clima, BRs) — as três
questões estavam respondidas e corretas, mas com os números trocados. As células foram
**reordenadas** e renumeradas, e as variáveis do código (`q8`, `q9`, `q10`) renomeadas para
casar com a pergunta que servem.

**9. Critério de ordenação da Q12.** O enunciado pede o top 5 de PE 2024–2025 por **número
de acidentes fatais** — não por número de mortos (critério do ranking de BRs na Q9, definido
como decisão do usuário). A ordenação segue o enunciado, com desempate por mortos e por
volume para ser determinística; o ranking por mortos é mantido no notebook como contraponto.
O **conjunto** dos cinco é o mesmo nos dois critérios, então a resposta não muda — muda a
ordem dentro do grupo.

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
| 4 — casos críticos | Q11–Q12 | `08_parte5_nivel4.ipynb` |

**Definição usada:** taxa de letalidade = **% de acidentes fatais do grupo** (conforme o
enunciado), sempre comparada à taxa global de **7,16%**. Cada questão declara o volume mínimo
aplicado e traz interpretação de 2–3 linhas, sem linguagem causal.

### Resultados do Nível 1

| Questão | Achado |
|---|---|
| Q1 | Taxa estável: 7,17% → 7,14% → 7,18% (+0,015 p.p. de variação) |
| Q2 | Maio lidera (7,71%); maio–agosto acima da global; fevereiro menor (6,57%) |
| Q3 | Plena Noite 10,09% vs Pleno dia 5,02% — o dobro, com 37,6% menos volume |
| Q4 | Risco relativo fim de semana / dias úteis = **1,285** |

### Resultados do Nível 2

| Questão | Achado |
|---|---|
| Q5 | Colisão frontal (lift 4,16) e atropelamento de pedestre (lift 4,04) — 45% dos fatais |
| Q6 | Top 5 dominado por pedestre e contramão; álcool do pedestre 2,25 (e 1,29 na outra categoria) vs **álcool no condutor 0,63** |
| Q7 | Curva 8,19% > reta 7,35%, mas ponte (10,75%) e declive (9,85%) são piores; explode declarado como não-partição |

### Resultados do Nível 3

| Questão | Achado |
|---|---|
| Q8 | Pista Simples (9,83%) mais que dobra a Dupla (4,69%) em **7 de 7** condições; pior célula Simples+Nevoeiro (13,95%); chuva com lift 0,86 |
| Q9 | Por **mortos**: BR-116 (1.190) e BR-101 (1.076); top 10 = 52,4% das mortes noturnas; só a BR-316 aparece também no ranking por taxa |
| Q10 | Letalidade quase igual nos três períodos (6,63%–7,40%); Fim de Ano tem +8,7% acidentes/dia e +25,2% mortos/dia; Carnaval tem acidentes/dia iguais ao normal (−0,5%) mas **15,4% menos mortos/dia** |

### Resultados do Nível 4

| Questão | Achado |
|---|---|
| Q11 | 437 acidentes com 3+ mortos (0,205% da base) concentram **9,36% das mortes**; **MG lidera** (75 acidentes, 303 mortos, 27 UFs); principal causa: contramão (27,0%); colisão frontal 62,9% (razão 2,27); pista Simples 88,6%; fases sobrerrepresentadas: Amanhecer (1,47) e Pleno dia (1,13) |
| Q12 | Top 5 de PE 2024–2025 por **acidentes fatais**: Recife (45), Garanhuns (24), Jaboatão (24), Caruaru (24), Petrolina (23) — 23,7% dos fatais de PE; mesmo conjunto no ranking por mortos; SALOA (13 acidentes, 20 mortos) fica de fora pelo volume mínimo |

## Gráficos (Parte 6)

Três gráficos Plotly em `resultados/`. Cada um responde a uma pergunta escrita na célula de
texto imediatamente acima, tem a **mensagem principal no título** e uma **legenda de 2 linhas**
com o que está sendo medido e como ler.

| Gráfico | Pergunta | Mensagem principal | Arquivo |
|---|---|---|---|
| 1 | Que tipos de acidente elevam a chance de morte? | Frontal (29,81%) e atropelamento de pedestre (28,96%) têm taxa **4× a global**; volume mínimo de 100 acidentes | `g1_taxa_por_tipo_acidente.html` |
| 2 | A taxa de letalidade varia ao longo dos 36 meses? | Oscila só **1,92 p.p.** (6,36% a 8,28%) e **sem tendência** — 12 primeiros e 12 últimos meses com a mesma média | `g2_serie_mensal.html` |
| 3 | Que horas do dia concentram os acidentes fatais? | **03h–06h** tem a taxa mais alta (12,26%), 2,5× a mais segura, com apenas 6,9% dos acidentes | `g3_faixa_horaria.html` |

Os gráficos 2 e 3 combinam **volume em barras** (eixo à direita) e **taxa de letalidade em
linha** (eixo à esquerda), com a taxa global marcada por tracejado — a separação entre
volume e gravidade é justamente o que o exercício pede que se enxergue.

`resultados/` **não é versionado** (`.gitignore`): o notebook regenera os arquivos a cada
execução. O HTML é **autocontido** (abre offline); o PNG depende do Chrome e é opcional.

## Síntese (Parte 7)

`notebooks/10_parte7_sintese.ipynb` — **três achados**, cada um com observação, tabela ou
gráfico onde aparece, comparação com a taxa global, hipótese e limitação. Todo número é
recalculado no notebook, a partir da base analítica.

| # | Achado | Observação | Onde | vs taxa global | Limitação |
|---|---|---|---|---|---|
| 1 | Colisão frontal e atropelamento de pedestre concentram a letalidade | 29,81% e 28,96%: 11,05% dos acidentes, **45,47% dos fatais** | Gráfico 1 + Q5/Q6 | lift **4,16** e **4,04** | classificação do BO, subnotificação, sem velocidade |
| 2 | A madrugada tem a taxa mais alta e o volume mais baixo | 03h–06h: 6,9% dos acidentes e **11,9% dos fatais**; 2,50× a faixa mais segura | Gráfico 3 + Q3 | lift **1,71** (mais segura: 0,69) | `horario` é o do registro, sem exposição por km |
| 3 | O problema é de geometria de via, não de sazonalidade | Pista Simples 9,89% contra Dupla 4,71%; contramão 6,1× mais frequente; 36 meses sem tendência | Gráfico 2 + Q8/Q11 | lift **1,38** (Dupla: 0,66) | `tipo_pista` é proxy, confundido com a BR |

**Categoria descartada pelo filtro de volume:** `Participar de racha` — 52 acidentes, 13
fatais, **25,00% de letalidade (lift 3,49)**. Não passa do corte de 100 acidentes da Q6 e,
sem o filtro, ocuparia a **6ª posição** por lift, logo atrás do top 5 (lift 3,60). O mesmo
custo se repete nos outros filtros: `Sinistro pessoal de trânsito` (20 acidentes, 15,00%,
lift 2,09) seria o 3º colocado entre os tipos de acidente; `Túnel` (125) sai da Q7; 36
das 119 BRs saem da Q9; 64 dos 90 municípios de PE saem da Q12; e 6 células de pista ×
clima (Granizo e Neve, 0 a 3 registros) ficam fora da Q8.

O **gráfico de síntese** (`resultados/g4_sintese_achados.html`) junta os três achados em
uma escala só — o lift de cada grupo contra a linha da taxa global — com dois contraponto
(`Contramão`, lift 4,04; `Faixa 09h–12h`, lift 0,69).

Nenhum dos três achados é uma explicação causal: são leituras de **concentração**, com
hipótese e limitação explicitadas.

## Licença e fonte

Dados públicos da Polícia Rodoviária Federal (Dados Abertos).
