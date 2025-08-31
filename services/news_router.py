from typing import List, Dict
from services.logger import get_logger
from services.reuters_scraper import fetch_reuters_fx_headlines
from services.db import list_users
from utils.constants import NEWS_CATEGORIES

logger = get_logger("news")

def build_user_delivery(headlines: List[Dict]) -> Dict[int, List[Dict]]:
    """
    Map user_id -> list of headlines matching their subscriptions.
    """
    out = {}
    users = list_users()
    for u in users:
        prefs = []
        if u["news_geo"]: prefs.append("Geopolitical Events")
        if u["news_cb"]: prefs.append("Central Bank News (Fed, ECB)")
        if u["news_cpi"]: prefs.append("Inflation & Economic Data")
        if not prefs:
            continue
        user_items = [h for h in headlines if h["category"] in prefs]
        if user_items:
            out[u["user_id"]] = user_items
    return out
