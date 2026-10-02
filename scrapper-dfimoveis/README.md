# 🏙️ DFImóveis Scrapper

> **Pipeline de coleta de dados de apartamentos à venda em Brasília / Plano Piloto.**
> Dados coletados do portal [DFImóveis](https://dfimoveis.com.br) para alimentar futuros modelos de análise e precificação de imóveis.

---

## 🎯 Objetivo

Este repositório implementa um **pipeline de Web Scraping** focado exclusivamente em:

- **Tipo de imóvel:** Apartamentos
- **Finalidade:** Venda
- **Localização:** Brasília — Plano Piloto (Asa Norte, Asa Sul, Lago Norte, Lago Sul, Noroeste, Sudoeste e adjacências)

O resultado é um arquivo CSV estruturado (`dfimoveis_raw.csv`) que serve como dataset bruto para um repositório separado de **Análise Exploratória e Modelagem de Machine Learning** (estimativa de preço).

> ⚠️ **Escopo Restrito:** Este projeto cuida **apenas** da raspagem e limpeza primária de dados. Nenhum código de análise estatística ou modelagem é gerado aqui.

---

## 📦 Pré-requisitos

### Python

Requer Python **3.10+**.

```bash
# Criar e ativar ambiente virtual (recomendado)
python -m venv .venv
source .venv/bin/activate        # Linux / macOS
# .venv\Scripts\activate         # Windows

# Instalar dependências
pip install -r requirements.txt
```

### Dependências principais (a detalhar em `requirements.txt`)

| Biblioteca | Finalidade |
|---|---|
| `requests` | Requisições HTTP |
| `beautifulsoup4` | Parsing de HTML |
| `lxml` | Parser HTML de alta performance (backend do BS4) |
| `pandas` | Manipulação e exportação do CSV |
| `tqdm` | Barra de progresso no terminal |
| `python-dotenv` | Gestão de variáveis de ambiente (opcional) |

---

## 🚀 Como Executar o Scraper

### Passo 1 — Etapa A: Coletar URLs dos Anúncios

Varre o paginador do portal e salva os links em `data/raw/urls_coletadas.txt`.

```bash
# Executar no terminal com o venv ativado
python src/crawl_urls.py
```

### Passo 2 — Etapa B: Extrair Detalhes de Cada Anúncio

Lê o arquivo de URLs e raspa os campos de cada página de detalhe, gerando o CSV. Essa etapa pode levar algumas horas devido ao volume e aos *delays* de segurança (politeness).

```bash
# Recomenda-se rodar em background (ex: nohup ou tmux)
python src/scrape_details.py
```

### Saída Esperada

```
data/
  raw/
    urls_coletadas.txt     ← Links únicos dos anúncios
    urls_com_erro.txt      ← URLs que falharam (timeout/404)
    dfimoveis_raw.csv      ← Dataset final estruturado
```

---

## 📁 Estrutura de Pastas

```
dfimoveis-scrapper/
│
├── data/
│   └── raw/
│       ├── urls_coletadas.txt     # Links coletados na Etapa A
│       ├── urls_com_erro.txt      # Log de URLs com falha
│       └── dfimoveis_raw.csv      # Saída final do scraper
│
├── docs/
│   ├── data_dictionary.md         # Contrato de dados — schema do CSV
│   ├── scraping_strategy.md       # Estratégia de coleta e politeness
│   └── selectors_map.md           # Mapeamento de seletores CSS/XPath
│
├── html/
│   └── *.html                     # Amostras reais de HTML para desenvolvimento/testes
│
├── logs/
│   └── scraper.log                # Arquivo de log geral da execução
│
├── src/
│   ├── crawl_urls.py              # Etapa A: varre paginador e coleta URLs
│   ├── scrape_details.py          # Etapa B: extrai dados de cada anúncio e salva o CSV
│   ├── parser.py                  # Funções de extração e limpeza com BeautifulSoup
│   └── config.py                  # Constantes e configurações (delays, paths, headers)
│
├── tests/
│   └── test_parser.py             # Testes unitários do parser utilizando pytest
│
├── .gitignore
├── AGENTS.md                      # Diretrizes para o agente de IA
├── README.md                      # Este arquivo
└── requirements.txt               # Dependências Python (versões fixadas)
```

---

## 📊 Schema de Saída (`dfimoveis_raw.csv`)

Consulte o [Data Dictionary](docs/data_dictionary.md) para a especificação completa de cada coluna, tipos de dados e regras de limpeza.

| Coluna | Tipo | Descrição |
|---|---|---|
| `preco_venda` | `float` | 🎯 **Target** — Preço de venda em R$ |
| `area_util` | `float` | Área útil em m² |
| `bairro_quadra` | `str` | Bairro ou quadra (ex: `"Asa Norte"`, `"SQN 304"`) |
| `quartos` | `int` | Número de quartos |
| `banheiros` | `int` | Número de banheiros/suítes |
| `vagas` | `int` | Vagas de garagem (`0` se ausente) |
| `valor_condominio` | `float` | Valor mensal do condomínio em R$ |
| `valor_iptu` | `float` | Valor do IPTU em R$ |
| `descricao_texto` | `str` | Descrição completa do anúncio |
| `comodidades_lista` | `str` | Comodidades separadas por vírgula |
| `url_anuncio` | `str` | URL original (chave para deduplicação) |
| `data_coleta` | `str` | Data da coleta (`YYYY-MM-DD`) |

---

## 📚 Documentação

| Documento | Descrição |
|---|---|
| [Data Dictionary](docs/data_dictionary.md) | Schema completo, tipos e regras de limpeza |
| [Scraping Strategy](docs/scraping_strategy.md) | Fluxo, politeness e tratamento de erros |
| [Selectors Map](docs/selectors_map.md) | Mapeamento de seletores CSS/XPath do portal |

---

## ⚖️ Aviso Legal

Os dados coletados são públicos e destinados exclusivamente a fins de pesquisa e desenvolvimento acadêmico/profissional. O scraper respeita as políticas de `robots.txt` do portal e implementa delays entre requisições para não sobrecarregar o servidor.

---

## 🗺️ Roadmap

- [x] Documentação inicial (Data Dictionary, Scraping Strategy, Selectors Map)
- [x] Mapeamento de seletores CSS/XPath (`docs/selectors_map.md`)
- [x] Implementação do `crawl_urls.py` (Etapa A)
- [x] Implementação do `scrape_details.py` (Etapa B)
- [x] Implementação do `parser.py` (parsers e cleaners num arquivo unificado)
- [x] Testes unitários de regex com pytest em `tests/test_parser.py`
- [x] Execução do pipeline completo e geração do `dfimoveis_raw.csv` (Pronto para uso)
