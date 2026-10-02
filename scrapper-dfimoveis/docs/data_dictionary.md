# 📖 Data Dictionary — Contrato de Dados

> **Arquivo de Saída:** `dfimoveis_raw.csv`
> **Escopo:** Apartamentos à venda — Brasília / Plano Piloto (DFImóveis)
> **Versão:** 1.0.0 | **Data:** 2026-09-04

---

## Visão Geral

Este documento é o **contrato formal** entre o pipeline de raspagem e os processos downstream (análise exploratória, modelagem de ML). Qualquer alteração de schema deve ser versionada aqui antes de ser implementada no código.

O CSV gerado deve ser **determinístico**: mesma URL → mesma linha (ignorando variações de data de coleta). O campo `url_anuncio` serve como chave natural para deduplicação.

---

## Schema do CSV

### Colunas Obrigatórias (linha descartada se ausente)

| # | Nome da Coluna | Tipo Python | Tipo Pandas | Exemplo | Regra de Nulo |
|---|---|---|---|---|---|
| 1 | `preco_venda` | `float` | `float64` | `450000.0` | **DESCARTAR LINHA** — sem preço, sem registro |
| 2 | `url_anuncio` | `str` | `object` | `https://dfimoveis.com.br/...` | **DESCARTAR LINHA** — chave primária natural |

### Colunas Numéricas de Imóvel

| # | Nome da Coluna | Tipo Python | Tipo Pandas | Exemplo | Regra de Nulo | Observações de Limpeza |
|---|---|---|---|---|---|---|
| 3 | `area_util` | `float` | `float64` | `87.5` | `None` → mantém `NaN` | Remove `"m²"`, vírgula → ponto; ex: `"87,50 m²"` → `87.5` |
| 4 | `quartos` | `int` | `Int64` (nullable) | `3` | `None` → mantém `NaN` | Extrai primeiro número inteiro; `"3 Quartos"` → `3` |
| 5 | `banheiros` | `int` | `Int64` (nullable) | `2` | `None` → mantém `NaN` | Pode incluir suítes no rótulo; extrair inteiro bruto |
| 6 | `vagas` | `int` | `Int64` (nullable) | `1` | `None` → **preencher com `0`** | Sem garagem = 0 vagas (válido para análise) |

### Colunas Financeiras

| # | Nome da Coluna | Tipo Python | Tipo Pandas | Exemplo | Regra de Nulo | Observações de Limpeza |
|---|---|---|---|---|---|---|
| 7 | `valor_condominio` | `float` | `float64` | `1200.0` | `None` → mantém `NaN` | Remove `"R$"`, pontos de milhar, troca vírgula por ponto |
| 8 | `valor_iptu` | `float` | `float64` | `350.0` | `None` → mantém `NaN` | Mesma lógica de `valor_condominio`; pode ser mensal ou anual — registrar na col. `iptu_periodo` |

### Colunas Textuais / Localização

| # | Nome da Coluna | Tipo Python | Tipo Pandas | Exemplo | Regra de Nulo | Observações de Limpeza |
|---|---|---|---|---|---|---|
| 9 | `bairro_quadra` | `str` | `object` | `"Asa Norte"` / `"SQN 304"` | `None` → mantém `NaN` | Strip de espaços e normalização de case (`str.strip().title()`) |
| 10 | `descricao_texto` | `str` | `object` | `"Lindo apartamento..."` | `None` → mantém `NaN` | Strip de espaços, remover `\n` excessivos; manter texto integral |
| 11 | `comodidades_lista` | `str` | `object` | `"Piscina, Academia, Salão de Festas"` | `None` → `""` (string vazia) | Cada comodidade separada por `", "` (vírgula + espaço); sem duplicatas; ordenadas alfabeticamente |

### Colunas de Metadados (Auditoria)

| # | Nome da Coluna | Tipo Python | Tipo Pandas | Exemplo | Regra de Nulo | Observações |
|---|---|---|---|---|---|---|
| 12 | `iptu_periodo` | `str` | `object` | `"mensal"` / `"anual"` | `None` → mantém `NaN` | Inferido do texto do anúncio; necessário para normalizar `valor_iptu` |
| 13 | `data_coleta` | `str` | `object` | `"2026-09-04"` | Sempre preenchido | Formato ISO 8601 (`YYYY-MM-DD`); gerado automaticamente pelo scraper |
| 14 | `id_anuncio` | `str` | `object` | `"12345"` | `None` → mantém `NaN` | Identificador interno do portal, se disponível na URL ou no DOM |

---

## Regras Globais de Limpeza

### Conversão de Valores Financeiros

```
Padrão de entrada:  "R$ 1.250.000,00"
Transformações:
  1. Remove "R$" e espaços → "1.250.000,00"
  2. Remove pontos de milhar → "1250000,00"
  3. Substitui vírgula decimal por ponto → "1250000.00"
  4. Converte para float → 1250000.0
```

### Conversão de Metragens

```
Padrão de entrada:  "87,50 m²"
Transformações:
  1. Extrai apenas os dígitos e separadores → "87,50"
  2. Substitui vírgula por ponto → "87.50"
  3. Converte para float → 87.5
```

### Conversão de Inteiros (quartos, banheiros, vagas)

```
Padrão de entrada:  "3 Quartos" | "2 Suítes" | "1"
Transformação:
  1. Extrai o primeiro grupo de dígitos com regex r"(\d+)"
  2. Converte para int
```

---

## Regras de Descarte de Linhas

| Condição | Ação |
|---|---|
| `preco_venda` é `NaN` ou `0` | Descartar linha |
| `url_anuncio` é vazio ou `None` | Descartar linha |
| `area_util <= 0` | Suspeitar de erro; manter linha com flag (TBD) |
| Linha duplicada por `url_anuncio` | Manter apenas a coleta mais recente (`data_coleta` maior) |

---

## Notas de Evolução

- **v1.1 (planejado):** Adicionar `tipo_anuncio` para filtrar Lançamento vs. Revenda.
- **v1.2 (planejado):** Adicionar `andar` e `total_andares` do edifício.
- **v1.3 (planejado):** Adicionar `codigo_postal` (CEP), se disponível.
