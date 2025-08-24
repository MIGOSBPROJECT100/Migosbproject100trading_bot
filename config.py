import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- Telegram Bot Configuration ---
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_IDS_STR = os.getenv("ADMIN_IDS", "")
ADMIN_IDS = [int(admin_id.strip()) for admin_id in ADMIN_IDS_STR.split(',') if admin_id]
ADMIN_USERNAMES = os.getenv("ADMIN_USERNAMES", "")

# --- TradingView Configuration ---
TRADINGVIEW_EMAIL = os.getenv("TRADINGVIEW_EMAIL")
TRADINGVIEW_PASSWORD = os.getenv("TRADINGVIEW_PASSWORD")
TRADINGVIEW_USERNAME = os.getenv("TRADINGVIEW_USERNAME")

# --- MetaTrader (MetaApi) Configuration ---
META_API_TOKEN = os.getenv("META_API_TOKEN")

# --- Bot Settings ---
BOT_TIMEZONE = "GMT+3"
JUST_MARKETS_REFERRAL_LINK = "https://one.justmarkets.link/a/64u110s6oc"
BINANCE_PAY_EMAIL = "migosblazer4@gmail.com"
MPESA_DETAILS = "+254746362427 - Ndung'u Kibera"
FEEDBACK_COOLDOWN_SECONDS = 60

# --- Bot Branding & Footer ---
BOT_FOOTER = f"_Managed by {ADMIN_USERNAMES}_"
BOT_SLOGAN = "PATIENCE ✰ DISCIPLINE ✰ RISK MANAGEMENT"

# --- Helper function to check if a user is an admin ---
def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS
