import json, os
from dotenv import load_dotenv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

APP_TZ = os.getenv("APP_TZ", "Etc/GMT-3")
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
DB_URL = os.getenv("DB_URL", f"sqlite:///{ROOT/'runtime'/'migosb.db'}")
ADMIN_IDS = [int(x.strip()) for x in os.getenv("ADMIN_IDS","").split(",") if x.strip().isdigit()]
ADMIN_TAGS = [x.strip() for x in os.getenv("ADMIN_TAGS","").split(",") if x.strip()]

SECURE_CFG = json.loads((ROOT / "config" / "secure_config.json").read_text(encoding="utf-8"))

BRAND = SECURE_CFG["brand"]
METAAPI = SECURE_CFG["metaapi"]
TRADINGVIEW = SECURE_CFG["tradingview"]
NEWS_CFG = SECURE_CFG["news"]
PAYMENTS = SECURE_CFG["payments"]
