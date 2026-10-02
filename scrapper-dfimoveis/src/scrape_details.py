"""
Etapa B: Visita cada URL coletada, extrai os detalhes e salva no CSV.
"""
import time
import random
import logging
import signal
import sys
import csv
import pandas as pd
from curl_cffi import requests

from config import (
    URLS_FILE, OUTPUT_CSV, ERROR_LOG, MAX_RETRIES, REQUEST_TIMEOUT,
    DELAY_DETALHE_MIN, DELAY_DETALHE_MAX, USER_AGENTS, BASE_HEADERS,
    CSV_COLUMNS, CHECKPOINT_INTERVAL, setup_logging
)
from parser import parse_detail_page

logger = logging.getLogger("scrape_details")

# Variáveis globais para gerenciar interrupções graciosas
is_running = True
buffer_data = []

def signal_handler(sig, frame):
    global is_running
    logger.info("\n[!] Sinal de interrupção recebido (Ctrl+C). Salvando progresso antes de sair...")
    is_running = False

def get_random_headers(referer: str = None) -> dict:
    headers = BASE_HEADERS.copy()
    headers["User-Agent"] = random.choice(USER_AGENTS)
    if referer:
        headers["Referer"] = referer
    return headers

def flush_buffer():
    global buffer_data
    if not buffer_data:
        return
        
    df_new = pd.DataFrame(buffer_data)
    
    # Garantir a ordem das colunas
    for col in CSV_COLUMNS:
        if col not in df_new.columns:
            df_new[col] = None
    df_new = df_new[CSV_COLUMNS]
    
    if OUTPUT_CSV.exists():
        df_new.to_csv(OUTPUT_CSV, mode="a", header=False, index=False, encoding="utf-8", quoting=csv.QUOTE_NONNUMERIC)
    else:
        df_new.to_csv(OUTPUT_CSV, mode="w", header=True, index=False, encoding="utf-8", quoting=csv.QUOTE_NONNUMERIC)
        
    logger.info(f"Flushed {len(buffer_data)} registros para {OUTPUT_CSV.name}")
    buffer_data.clear()

def log_error(url: str, error_type: str, reason: str):
    timestamp = pd.Timestamp.now().isoformat()
    with open(ERROR_LOG, "a", encoding="utf-8") as f:
        f.write(f"{url} | {error_type} | {reason} | {timestamp}\n")

def main():
    global is_running
    signal.signal(signal.SIGINT, signal_handler)
    setup_logging()
    
    logger.info("=== Iniciando Etapa B: Extração de Detalhes ===")
    
    if not URLS_FILE.exists():
        logger.error(f"Arquivo {URLS_FILE} não encontrado. Rode a Etapa A primeiro.")
        return
        
    # Ler URLs coletadas
    with open(URLS_FILE, "r", encoding="utf-8") as f:
        all_urls = [line.strip() for line in f if line.strip()]
        
    logger.info(f"Encontradas {len(all_urls)} URLs para processar.")
    
    # Verificar idempotência
    processed_urls = set()
    if OUTPUT_CSV.exists():
        try:
            with open(OUTPUT_CSV, "r", encoding="utf-8", errors="replace") as f:
                reader = csv.reader(f)
                header = next(reader, None)
                url_idx = 1
                if header and "url_anuncio" in header:
                    url_idx = header.index("url_anuncio")
                for row in reader:
                    if len(row) > url_idx and row[url_idx].startswith("http"):
                        processed_urls.add(row[url_idx].strip())
            logger.info(f"Dessas, {len(processed_urls)} já foram processadas e serão ignoradas.")
        except Exception as e:
            logger.warning(f"Erro ao ler URLs existentes de {OUTPUT_CSV}: {e}")
    
    pending_urls = [url for url in all_urls if url not in processed_urls]
    logger.info(f"Restam {len(pending_urls)} URLs pendentes.")
    
    if not pending_urls:
        logger.info("Nada a processar.")
        return

    session = requests.Session()
    
    for i, url in enumerate(pending_urls):
        if not is_running:
            break
            
        logger.info(f"[{i+1}/{len(pending_urls)}] Raspando: {url}")
        
        success = False
        for attempt in range(MAX_RETRIES):
            try:
                headers = get_random_headers()
                response = session.get(url, headers=headers, impersonate="chrome124", timeout=REQUEST_TIMEOUT)
                
                if response.status_code == 404:
                    logger.warning(f"Anúncio não encontrado (404): {url}")
                    log_error(url, "404", "Not Found")
                    success = True # Não tentar de novo
                    break
                    
                response.raise_for_status()
                
                parsed_data = parse_detail_page(response.text, url)
                if parsed_data:
                    buffer_data.append(parsed_data)
                    logger.info(f"  -> Sucesso. Preço: {parsed_data.get('preco_venda')}")
                else:
                    logger.warning(f"  -> Descartado (sem preço/inválido).")
                
                success = True
                break
                
            except (requests.exceptions.RequestException, Exception) as e:
                logger.warning(f"Erro (tentativa {attempt+1}/{MAX_RETRIES}): {e}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(random.uniform(5, 10))
                else:
                    log_error(url, "RequestError", str(e))
        
        if not success:
            logger.error(f"Falha definitiva ao processar: {url}")
            
        if len(buffer_data) >= CHECKPOINT_INTERVAL:
            flush_buffer()
            
        # Delay de cortesia
        if is_running and i < len(pending_urls) - 1:
            delay = random.uniform(DELAY_DETALHE_MIN, DELAY_DETALHE_MAX)
            time.sleep(delay)
            
    # Flush final
    flush_buffer()
    logger.info("=== Processamento concluído! ===")

if __name__ == "__main__":
    main()
