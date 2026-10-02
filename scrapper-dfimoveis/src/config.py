"""
Configurações centralizadas do scraper DFImóveis.
"""
import logging
import os
from pathlib import Path

# === Diretórios ===
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "raw"
LOGS_DIR = PROJECT_ROOT / "logs"

# Garantir que os diretórios existam
DATA_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# === URLs ===
BASE_URL = "https://www.dfimoveis.com.br"
LISTING_URL = f"{BASE_URL}/venda/df/brasilia/casa"

# === Arquivos de Saída ===
URLS_FILE = DATA_DIR / "urls_coletadas.txt"
OUTPUT_CSV = DATA_DIR / "dfimoveis_raw.csv"
ERROR_LOG = DATA_DIR / "urls_com_erro.txt"

# === Delays (cortesia com o servidor) ===
DELAY_PAGINADOR_MIN = 3
DELAY_PAGINADOR_MAX = 7
DELAY_DETALHE_MIN = 5
DELAY_DETALHE_MAX = 12

# === Limites ===
REQUEST_TIMEOUT = 15
MAX_RETRIES = 3
MAX_PAGES = 999
CHECKPOINT_INTERVAL = 50

# === User-Agents ===
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64; rv:127.0) Gecko/20100101 Firefox/127.0",
]

# === Headers Base ===
BASE_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
}

# === Colunas do CSV (ordem fixa) ===
CSV_COLUMNS = [
    "preco_venda", "url_anuncio", "area_util", "quartos",
    "suites", "vagas", "valor_condominio", "valor_iptu",
    "bairro_quadra", "descricao_texto", "comodidades_lista",
    "iptu_periodo", "data_coleta", "id_anuncio",
]

def setup_logging():
    """Configura o logging para arquivo e console."""
    log_file = LOGS_DIR / "scraper.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )
