import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = [int(x.strip()) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()]

APP_TZ = os.getenv("APP_TZ", "Africa/Nairobi")

TV_EMAIL = os.getenv("TV_EMAIL")
TV_USERNAME = os.getenv("TV_USERNAME")
TV_PASSWORD = os.getenv("TV_PASSWORD")

MASTER_MT5_LOGIN = os.getenv("MASTER_MT5_LOGIN")
MASTER_MT5_PASSWORD = os.getenv("MASTER_MT5_PASSWORD")

METAAPI_TOKEN = os.getenv("METAAPI_TOKEN")
JUSTMARKETS_REF_LINK = os.getenv("JUSTMARKETS_REF_LINK")

DATA_DIR = os.path.join(os.getcwd(), "data")
SCREENSHOT_DIR = os.path.join(DATA_DIR, "screenshots")

# Safety checks (no crashes; logged by services.logger)
def sanity_check():
    missing = []
    for key, val in {
        "BOT_TOKEN": BOT_TOKEN,
        "TV_EMAIL": TV_EMAIL,
        "TV_USERNAME": TV_USERNAME,
        "TV_PASSWORD": TV_PASSWORD,
        "MASTER_MT5_LOGIN": MASTER_MT5_LOGIN,
        "MASTER_MT5_PASSWORD": MASTER_MT5_PASSWORD,
        "METAAPI_TOKEN": METAAPI_TOKEN,
    }.items():
        if not val:
            missing.append(key)
    return missing
