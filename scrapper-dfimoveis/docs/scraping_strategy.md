# 🕷️ Scraping Strategy — Estratégia de Coleta

> **Portal Alvo:** DFImóveis (`dfimoveis.com.br`)
> **Escopo:** Apartamentos à venda — Brasília / Plano Piloto
> **Versão:** 1.0.0 | **Data:** 2026-09-04

---

## 1. Visão Geral do Fluxo

O pipeline de coleta é dividido em **duas etapas sequenciais e bem separadas**. Essa separação garante resiliência: se a Etapa B falhar em um anúncio, a lista de URLs da Etapa A está preservada.

```
┌─────────────────────────────────────────────────────────────────────┐
│  ETAPA A — Varredura do Paginador (List Crawl)                      │
│                                                                     │
│  URL Base (filtros) → Página 1 → Página 2 → ... → Página N         │
│                          │           │                │             │
│                      [links]     [links]          [links]           │
│                          └───────────┴────────────────┘             │
│                                      │                              │
│                              urls_coletadas.txt                     │
└─────────────────────────────────────────┬───────────────────────────┘
                                          │
                                          ▼
┌─────────────────────────────────────────────────────────────────────┐
│  ETAPA B — Extração de Detalhes (Detail Scrape)                     │
│                                                                     │
│  Para cada URL em urls_coletadas.txt:                               │
│    → Requisição HTTP                                                │
│    → parse_detail_page()                                            │
│    → Append em dfimoveis_raw.csv                                    │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 2. Etapa A — Varredura do Paginador

### 2.1 URL Base e Filtros

A URL de listagem deve ser construída com os parâmetros de filtro do portal:

| Parâmetro | Valor Alvo | Descrição |
|---|---|---|
| Tipo de Imóvel | Apartamento | Excluir casas, comerciais, etc. |
| Finalidade | Venda | Excluir aluguel |
| Região | Plano Piloto / Brasília | Restringir geograficamente |

URL a ser usada: https://www.dfimoveis.com.br/venda/df/brasilia/apartamento

### 2.2 Lógica de Paginação

```
Enquanto houver botão "Próxima Página" (ou número de página atual < total):
  1. Extrair todos os links de anúncios da página atual
  2. Adicionar links ao conjunto (set) — evita duplicatas
  3. Aguardar DELAY_PAGINADOR segundos (ver Seção 4)
  4. Navegar para a próxima página
Salvar conjunto de links em arquivo intermediário: data/raw/urls_coletadas.txt
```

### 2.3 Critério de Parada

- **Primário:** Ausência do elemento de "próxima página" no DOM.
- **Secundário (fallback):** Limite máximo configurável `MAX_PAGES` (default: 999) para evitar loop infinito em caso de erro de detecção.

---

## 3. Etapa B — Extração de Detalhes

### 3.1 Fluxo por Anúncio

```
Para cada url em urls_coletadas.txt:
  1. Verificar se url já foi processada (checar dfimoveis_raw.csv pelo url_anuncio)
  2. Se já processada → pular (idempotência)
  3. Fazer requisição HTTP com headers rotacionados
  4. Se resposta OK (200): chamar parse_detail_page(html)
  5. Validar registro: preco_venda obrigatório; url_anuncio obrigatório
  6. Fazer append do registro no CSV
  7. Aguardar DELAY_DETALHE segundos
```

### 3.2 Idempotência

O scraper deve ser **re-executável sem duplicar dados**. A lógica de verificação usa `url_anuncio` como chave:

```python
# Pseudocódigo — verificação de idempotência
urls_ja_coletadas = set(pd.read_csv("dfimoveis_raw.csv")["url_anuncio"])
if url in urls_ja_coletadas:
    continue  # pular sem fazer requisição
```

---

## 4. Políticas de Politeness (Cortesia com o Servidor)

> **Princípio:** Comportar-se como um usuário humano lento e cauteloso. Evitar bloqueios e não sobrecarregar o servidor alvo.

### 4.1 Delays entre Requisições

| Contexto | Delay Mínimo | Delay Máximo | Estratégia |
|---|---|---|---|
| Entre páginas da listagem (Etapa A) | 3s | 7s | `random.uniform(3, 7)` |
| Entre páginas de detalhe (Etapa B) | 5s | 12s | `random.uniform(5, 12)` |
| Após erro 429 (Too Many Requests) | 60s | 120s | Exponential back-off + jitter |
| Após erro 403 (Forbidden) | 300s | 600s | Pausa longa + rotação de User-Agent |

### 4.2 Rotação de User-Agent

Manter uma lista de User-Agents de navegadores modernos e selecionar aleatoriamente a cada requisição:

```
Candidatos (atualizar periodicamente):
- Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 ... Chrome/125.0
- Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/605.1.15 ... Safari/605.1.15
- Mozilla/5.0 (X11; Linux x86_64; rv:127.0) Gecko/20100101 Firefox/127.0
```

### 4.3 Headers Padrão

Além do `User-Agent`, incluir headers que simulam um navegador real:

```
Accept:          text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8
Accept-Language: pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7
Accept-Encoding: gzip, deflate, br
Connection:      keep-alive
Referer:         [URL da página de listagem anterior]
```

### 4.4 Sessão HTTP

Usar `requests.Session()` para reutilizar conexões TCP e manter cookies de sessão, o que reduz a probabilidade de bloqueio por comportamento anômalo.

---

## 5. Estratégia de Tratamento de Erros

### 5.1 Hierarquia de Exceções

```
Requisição HTTP
├── Timeout (requests.Timeout)
│     → Retry até MAX_RETRIES (3x) com back-off exponencial
│     → Se esgotar retries: logar URL como falha; continuar loop
│
├── ConnectionError (requests.ConnectionError)
│     → Aguardar 30s e tentar novamente
│     → Se persistir: salvar estado e encerrar com aviso
│
├── HTTP 403 (Forbidden)
│     → Pausa longa (ver Seção 4.1) + trocar User-Agent
│     → Logar evento no arquivo de log
│
├── HTTP 404 (Not Found)
│     → Anúncio removido/expirado; logar e pular
│
├── HTTP 429 (Too Many Requests)
│     → Respeitar Retry-After header se presente
│     → Caso contrário: back-off exponencial (60s → 120s → 240s)
│
└── Erro de Parsing (AttributeError, ValueError)
      → Campo individual capturado como None
      → O registro é preservado; nunca abortar o loop por campo ausente
```

### 5.2 Salvamento de Estado (Checkpoint)

Para runs longas, salvar progresso regularmente:

| Gatilho | Ação |
|---|---|
| A cada 50 anúncios processados | Flush do buffer para o CSV |
| Ao receber sinal SIGINT (Ctrl+C) | Salvar CSV parcial e exibir resumo |
| Ao atingir 3 erros 403 consecutivos | Salvar CSV parcial e encerrar com código de saída 1 |

### 5.3 Arquivo de Log de Falhas

Manter `data/raw/urls_com_erro.txt` com as URLs que falharam, permitindo re-processamento seletivo:

```
# Formato: url | codigo_http | motivo | timestamp
https://dfimoveis.com.br/imovel/123 | 404 | Not Found | 2026-09-04T10:15:32
https://dfimoveis.com.br/imovel/456 | timeout | ReadTimeout | 2026-09-04T10:16:45
```

---

## 6. Configurações (Constantes do Projeto)

Todas as configurações de comportamento devem ser centralizadas em um arquivo `config.py` ou seção de constantes, **nunca hardcoded** nas funções:

| Constante | Valor Padrão | Descrição |
|---|---|---|
| `REQUEST_TIMEOUT` | `15` (segundos) | Timeout por requisição HTTP |
| `MAX_RETRIES` | `3` | Máximo de tentativas por URL |
| `DELAY_PAGINADOR_MIN` | `3` | Delay mínimo entre páginas de listagem |
| `DELAY_PAGINADOR_MAX` | `7` | Delay máximo entre páginas de listagem |
| `DELAY_DETALHE_MIN` | `5` | Delay mínimo entre detalhes |
| `DELAY_DETALHE_MAX` | `12` | Delay máximo entre detalhes |
| `MAX_PAGES` | `999` | Limite de segurança de páginas |
| `CHECKPOINT_INTERVAL` | `50` | Anúncios entre cada flush do CSV |
| `OUTPUT_CSV` | `dfimoveis_raw.csv` | Caminho do arquivo de saída |
| `URLS_FILE` | `data/raw/urls_coletadas.txt` | Arquivo intermediário de URLs |
| `ERROR_LOG` | `data/raw/urls_com_erro.txt` | Log de URLs com falha |

---

## 7. Considerações Legais e Éticas

- Verificar e respeitar o arquivo `robots.txt` do portal antes da execução.
- Coletar apenas dados publicamente disponíveis (sem autenticação).
- Não armazenar dados pessoais identificáveis de proprietários/corretores.
- Uso dos dados exclusivamente para pesquisa e desenvolvimento de modelos analíticos.
