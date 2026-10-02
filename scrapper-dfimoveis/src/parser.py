"""
Módulo de parsing e limpeza de dados HTML.
"""
import re
import logging
from datetime import date
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# === Expressões Regulares ===
RE_CURRENCY = re.compile(r"[\d\.]+(?:,\d{2})?")
RE_AREA = re.compile(r"([\d]+(?:[,\.]\d+)?)\s*m²", re.IGNORECASE)
RE_INTEGER = re.compile(r"(\d+)")
RE_IPTU = re.compile(r"IPTU\s*R?\$?\s*:?\s*([\d\.]+(?:,\d{2})?)", re.IGNORECASE)
RE_IPTU_PERIOD = re.compile(r"IPTU[^.]{0,30}(mensal|anual|mês|ano|/mês|/ano)", re.IGNORECASE)

# === Seletores CSS ===
SELECTORS = {
    "id": "input#id-imovel",
    "price": "p[itemprop='price']",
    "area": "p[itemprop='floorSize']",
    "rooms": ".info-details .room span",
    "suites": ".info-details .suite span",
    "parking": ".info-details .vacancy span",
    "condo": ".info-details .condom span",
    "address": ".info-details span[itemprop='address']",
    "description": ".escondido-text",
    "description_alt": ".assined-imv",
    "amenities": "#listaDeDetalhesDoImovel ul.feature-itens li",
    "dados_block": ".dados-block ul.details-text li",
}

# === Funções de Limpeza ===

def clean_currency(text: str) -> float | None:
    """Converte string financeira ('R$ 1.250.000,00' ou '1250000,00') para float."""
    if not text or "sob consulta" in text.lower():
        return None
    match = RE_CURRENCY.search(text)
    if match:
        val_str = match.group(0).replace(".", "").replace(",", ".")
        try:
            return float(val_str)
        except ValueError:
            return None
    return None

def clean_area(text: str) -> float | None:
    """Extrai metragem ('87,50 m²') para float."""
    if not text:
        return None
    match = RE_AREA.search(text)
    if match:
        val_str = match.group(1).replace(".", "").replace(",", ".")
        try:
            return float(val_str)
        except ValueError:
            return None
    return None

def clean_integer(text: str) -> int | None:
    """Extrai o primeiro inteiro ('3 Quartos', '1 Suíte')."""
    if not text:
        return None
    match = RE_INTEGER.search(text)
    if match:
        return int(match.group(1))
    return None

# === Funções de Extração ===

def extract_price(soup: BeautifulSoup) -> float | None:
    price_el = soup.select_one(SELECTORS["price"])
    if not price_el:
        return None
    # Priorizar o content que já vem semi-limpo (ex: "1690000,00")
    content_val = price_el.get("content")
    if content_val:
        val = clean_currency(content_val)
        if val is not None:
            return val
    return clean_currency(price_el.get_text(strip=True))

def extract_area(soup: BeautifulSoup) -> float | None:
    el = soup.select_one(SELECTORS["area"])
    return clean_area(el.get_text(strip=True)) if el else None

def extract_rooms(soup: BeautifulSoup) -> int | None:
    el = soup.select_one(SELECTORS["rooms"])
    return clean_integer(el.get_text(strip=True)) if el else None

def extract_suites(soup: BeautifulSoup) -> int | None:
    # Suites mapeados a partir de suites
    el = soup.select_one(SELECTORS["suites"])
    val = clean_integer(el.get_text(strip=True)) if el else None
    return val if val is not None else 0

def extract_parking(soup: BeautifulSoup) -> int:
    # Se não houver vaga explícita, retorna 0
    el = soup.select_one(SELECTORS["parking"])
    val = clean_integer(el.get_text(strip=True)) if el else None
    return val if val is not None else 0

def extract_condo_fee(soup: BeautifulSoup) -> float | None:
    el = soup.select_one(SELECTORS["condo"])
    return clean_currency(el.get_text(strip=True)) if el else None

def extract_iptu(soup: BeautifulSoup) -> float | None:
    items = soup.select(SELECTORS["dados_block"])
    for item in items:
        text = item.get_text(strip=True)
        if "IPTU" in text.upper():
            match = RE_IPTU.search(text)
            if match:
                val_str = match.group(1).replace(".", "").replace(",", ".")
                try:
                    return float(val_str)
                except ValueError:
                    return None
    return None

def extract_description(soup: BeautifulSoup) -> str | None:
    el = soup.select_one(SELECTORS["description"]) or soup.select_one(SELECTORS["description_alt"])
    if not el:
        return None
    text = el.get_text(separator=" ", strip=True)
    # Normalizar quebras de linha e espaços múltiplos
    text = text.replace("\r\n", " ").replace("\r", " ").replace("\n", " ")
    text = re.sub(r'\s+', ' ', text).strip()
    return text if text else None

def extract_iptu_period(description: str) -> str | None:
    if not description:
        return None
    match = RE_IPTU_PERIOD.search(description)
    if match:
        val = match.group(1).lower()
        if "mês" in val or "mensal" in val:
            return "mensal"
        if "ano" in val or "anual" in val:
            return "anual"
    return None

def extract_neighborhood(soup: BeautifulSoup) -> str | None:
    el = soup.select_one(SELECTORS["address"])
    if not el:
        return None
    text = el.get_text(strip=True)
    # Exemplo: "BRASÍLIA - ASA NORTE" -> "Asa Norte"
    parts = text.split("-", 1)
    if len(parts) > 1:
        return parts[1].strip().title()
    return text.strip().title()

def extract_amenities(soup: BeautifulSoup) -> str:
    items = soup.select(SELECTORS["amenities"])
    amenities = [item.get_text(strip=True) for item in items if item.get_text(strip=True)]
    # Remover duplicatas mantendo ordem alfabética
    unique_amenities = sorted(list(set(amenities)))
    return ", ".join(unique_amenities)

def extract_id(soup: BeautifulSoup) -> str | None:
    el = soup.select_one(SELECTORS["id"])
    return el.get("value") if el else None


def parse_detail_page(html: str, url: str) -> dict | None:
    """
    Extrai todos os campos de uma página de detalhe.
    Retorna None se preco_venda for ausente ou 0 (regra de descarte).
    """
    soup = BeautifulSoup(html, "html.parser")
    
    preco = extract_price(soup)
    if preco is None or preco == 0:
        logger.warning(f"Preço ausente ou zero, descartando: {url}")
        return None
    
    descricao = extract_description(soup)
    
    return {
        "preco_venda": preco,
        "url_anuncio": url,
        "area_util": extract_area(soup),
        "quartos": extract_rooms(soup),
        "suites": extract_suites(soup),
        "vagas": extract_parking(soup),
        "valor_condominio": extract_condo_fee(soup),
        "valor_iptu": extract_iptu(soup),
        "bairro_quadra": extract_neighborhood(soup),
        "descricao_texto": descricao,
        "comodidades_lista": extract_amenities(soup),
        "iptu_periodo": extract_iptu_period(descricao) if descricao else None,
        "data_coleta": date.today().isoformat(),
        "id_anuncio": extract_id(soup),
    }
