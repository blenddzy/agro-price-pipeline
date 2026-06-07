import os

# ── Base paths ──────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
LOGS_DIR = os.path.join(BASE_DIR, "logs")

# ── Database ─────────────────────────────────────────────────────────────────
DB_PATH = os.path.join(DATA_DIR, "precios_agro.db")

# ── Scraping ──────────────────────────────────────────────────────────────────
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

# Bolsa de Cereales de Buenos Aires — precios pizarra
URL_BOLSA_CEREALES = "https://www.bolsadecereales.com/precios"

# Productos a rastrear
PRODUCTOS = ["Trigo", "Maíz", "Soja", "Girasol", "Sorgo"]

# ── Scheduler ────────────────────────────────────────────────────────────────
# Hora de ejecución diaria (formato 24h)
SCHEDULE_HOUR = 9
SCHEDULE_MINUTE = 0

# ── Logging ───────────────────────────────────────────────────────────────────
LOG_FILE = os.path.join(LOGS_DIR, "pipeline.log")
LOG_LEVEL = "INFO"
