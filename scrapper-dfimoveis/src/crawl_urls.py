"""
Etapa A: Varredura de páginas de listagem para coletar URLs únicas de anúncios.
"""
import time
import random
import logging
from bs4 import BeautifulSoup
from curl_cffi import requests

from config import (
    LISTING_URL, BASE_URL, URLS_FILE, MAX_PAGES, REQUEST_TIMEOUT,
    DELAY_PAGINADOR_MIN, DELAY_PAGINADOR_MAX, USER_AGENTS, BASE_HEADERS,
    setup_logging
)

logger = logging.getLogger("crawl_urls")

def get_random_headers() -> dict:
    headers = BASE_HEADERS.copy()
    headers["User-Agent"] = random.choice(USER_AGENTS)
    return headers

def save_urls(urls: set):
    """Salva a lista de URLs no arquivo."""
    # Write to a temporary file first then rename to avoid corruption if killed
    temp_file = URLS_FILE.with_suffix('.tmp')
    with open(temp_file, "w", encoding="utf-8") as f:
        for url in sorted(list(urls)):
            f.write(f"{url}\n")
    temp_file.replace(URLS_FILE)

def main():
    setup_logging()
    logger.info("=== Iniciando Etapa A: Varredura de URLs ===")
    
    session = requests.Session()
    all_urls = set()
    
    if URLS_FILE.exists():
        with open(URLS_FILE, "r", encoding="utf-8") as f:
            all_urls = set(line.strip() for line in f if line.strip())
        logger.info(f"Retomando com {len(all_urls)} URLs já coletadas.")
    
    page = 1
    while page <= MAX_PAGES:
        url = f"{LISTING_URL}?pagina={page}"
        headers = get_random_headers()
        
        try:
            logger.info(f"Processando página {page}...")
            response = session.get(url, headers=headers, impersonate="chrome124", timeout=REQUEST_TIMEOUT)
            
            if response.status_code == 404:
                logger.info(f"Página {page} não encontrada (404). Fim da paginação.")
                break
                
            response.raise_for_status()
            
        except (requests.exceptions.RequestException, Exception) as e:
            logger.error(f"Erro ao acessar página {page}: {e}")
            logger.info("Aguardando 30s antes de tentar novamente...")
            time.sleep(30)
            continue
            
        soup = BeautifulSoup(response.text, "html.parser")
        cards = soup.select("a.imovel-card")
        
        if not cards:
            logger.info(f"Nenhum card encontrado na página {page}. Fim da varredura.")
            break
            
        new_urls = 0
        for card in cards:
            href = card.get("href", "")
            if href:
                full_url = f"{BASE_URL}{href}" if href.startswith("/") else href
                if full_url not in all_urls:
                    all_urls.add(full_url)
                    new_urls += 1
                    
        logger.info(f"Página {page}: {len(cards)} cards, {new_urls} URLs novas. Total: {len(all_urls)}")
        
        # Salvar checkpoint
        save_urls(all_urls)
        
        page += 1
        delay = random.uniform(DELAY_PAGINADOR_MIN, DELAY_PAGINADOR_MAX)
        time.sleep(delay)

    logger.info(f"=== Varredura concluída! Total final: {len(all_urls)} URLs ===")

if __name__ == "__main__":
    main()
