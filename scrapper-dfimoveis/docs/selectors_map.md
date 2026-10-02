# 🗺️ Selectors Map — Mapeamento HTML

> **Portal Alvo:** DFImóveis (`dfimoveis.com.br`)
> **Versão:** 1.0.0 | **Data:** 2026-09-05
> **Status:** ✅ Validados contra HTML real (venda)

---

## Como Preencher Este Documento

1. Abra os arquivos HTML de amostra na pasta `./html/` (listagem e detalhe).
2. Use DevTools do navegador ou `beautifulsoup4` para localizar cada elemento.
3. Preencha as colunas `Seletor CSS` e/ou `XPath` na tabela correspondente.
4. Adicione o `Valor de Exemplo` extraído da amostra real.
5. Atualize o `Status` da linha para ✅ quando validado.

> **Regra de Ouro (ver AGENTS.md):** Sempre validar o seletor contra os arquivos locais `./html/` antes de usar em requisições HTTP reais.

---

## Seção 1 — Página de Listagem (List Page)

> Arquivo de referência: `./html/listagem_venda.html`

### 1.1 Estrutura Geral da Listagem

| Campo | Descrição | Seletor CSS | Valor de Exemplo | Status |
|---|---|---|---|---|
| `card_anuncio` | Elemento de cada card individual | `a.imovel-card` | — | ✅ |
| `link_detalhe` | Tag `<a>` com a URL da página de detalhe | Atributo `href` do card | `/imovel/lancamento...` | ✅ |

### 1.2 Paginação

| Campo | Descrição | Regra de Paginação | Status |
|---|---|---|---|
| `paginacao` | Controle de próximas páginas | Iterar sobre `?pagina=N` até receber 0 cards | ✅ |

---

## Seção 2 — Página de Detalhe (Detail Page)

> Arquivos de referência: `./html/detalhe_venda.html`, `./html/detalhe_venda_com_preco.html`

### 2.1 Informações Principais

| Campo | Coluna CSV | Seletor CSS | Atributo Alvo | Valor de Exemplo | Status |
|---|---|---|---|---|---|
| Preço de Venda | `preco_venda` | `p[itemprop='price']` | `content` | `1690000,00` | ✅ |
| Área Útil | `area_util` | `p[itemprop='floorSize']` | `text` | `110,00 m²` | ✅ |
| Bairro / Quadra | `bairro_quadra` | `span[itemprop='address']` | `text` | `BRASÍLIA - ASA NORTE` | ✅ |
| ID do Anúncio | `id_anuncio` | `input#id-imovel` | `value` | `1420507` | ✅ |

### 2.2 Características do Imóvel (Ícones / Badges)

| Campo | Coluna CSV | Seletor CSS | Atributo Alvo | Valor de Exemplo | Status |
|---|---|---|---|---|---|
| Quartos | `quartos` | `.info-details .room span` | `text` | `3 quartos` | ✅ |
| Banheiros / Suítes | `banheiros` | `.info-details .suite span` | `text` | `1 suíte` | ✅ |
| Vagas de Garagem | `vagas` | `.info-details .vacancy span` | `text` | `1 vaga` | ✅ |

### 2.3 Valores Financeiros Adicionais

| Campo | Coluna CSV | Seletor CSS | Atributo Alvo | Valor de Exemplo | Status |
|---|---|---|---|---|---|
| Valor do Condomínio | `valor_condominio` | `.info-details .condom span` | `text` | `Condomínio\nR$  1.237` | ✅ |
| Valor do IPTU | `valor_iptu` | `.dados-block ul.details-text li` | `text` (com regex) | `IPTU R$:1.290` | ✅ |
| Período do IPTU | `iptu_periodo` | Inferido via Regex | `text` (da descrição) | `mensal` / `anual` | ✅ |

### 2.4 Descrição Textual

| Campo | Coluna CSV | Seletor CSS | Atributo Alvo | Valor de Exemplo | Status |
|---|---|---|---|---|---|
| Descrição completa | `descricao_texto` | `.escondido-text` ou `.assined-imv` | `text` | `"Morar ao lado do..."` | ✅ |

### 2.5 Lista de Comodidades / Amenidades

| Campo | Coluna CSV | Seletor CSS Item | Valor de Exemplo (item) | Status |
|---|---|---|---|---|
| Item de comodidade | `comodidades_lista` | `#listaDeDetalhesDoImovel ul.feature-itens li` | `"Ar Condicionado"` | ✅ |

---

## Seção 3 — Notas de Manutenção

### 3.3 Padrões de Regex para Extração de Texto

| Campo | Texto Bruto Esperado | Regex Pattern | Grupo Capturado | Exemplo de Saída |
|---|---|---|---|---|
| `preco_venda` | `"1690000,00"` | `r"[\d\.]+(?:,\d{2})?"` | grupo 0 | `"1690000.0"` |
| `area_util` | `"110,00 m²"` | `r"([\d]+(?:[,\.]\d+)?)\s*m²"` | grupo 1 | `"110.0"` |
| `inteiros` | `"3 quartos"` | `r"(\d+)"` | grupo 1 | `"3"` |
| `valor_iptu` | `"IPTU R$:1.290"` | `r"IPTU\s*R?\$?\s*:?\s*([\d\.]+(?:,\d{2})?)"` | grupo 1 | `"1290.0"` |
| `iptu_periodo`| `"IPTU anual..."` | `r"IPTU[^.]{0,30}(mensal\|anual\|mês\|ano\|/mês\|/ano)"` | grupo 1 | `"anual"` |
