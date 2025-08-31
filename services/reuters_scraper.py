import requests, re
from bs4 import BeautifulSoup
from typing import List, Dict
from services.logger import get_logger

logger = get_logger("reuters")

def fetch_reuters_fx_headlines() -> List[Dict]:
    """
    Fetch latest FX-related headlines (best-effort parsing, structure may change).
    Returns list of dicts: {'title': str, 'url': str, 'category': str}
    """
    try:
        url = "https://www.reuters.com/markets/currencies/"
        r = requests.get(url, timeout=15, headers={"User-Agent":"Mozilla/5.0"})
        soup = BeautifulSoup(r.text, "lxml")
        items = []
        for a in soup.select("a[href*='/markets/currencies/']")[:20]:
            title = a.get_text(strip=True)
            href = "https://www.reuters.com" + a.get("href", "")
            cat = categorize_headline(title)
            if title and href:
                items.append({"title": title, "url": href, "category": cat})
        return items
    except Exception as e:
        logger.exception("Reuters scraping failed: %s", e)
        return []

def categorize_headline(title: str) -> str:
    t = title.lower()
    if any(k in t for k in ["fed", "ecb", "boe", "central bank", "interest rate", "hike", "cut"]):
        return "Central Bank News (Fed, ECB)"
    if any(k in t for k in ["inflation", "cpi", "ppi", "jobs", "employment", "unemployment", "gdp"]):
        return "Inflation & Economic Data"
    if any(k in t for k in ["ukraine", "middle east", "geopolitics", "sanction", "election", "war", "conflict", "geopolitical"]):
        return "Geopolitical Events"
    return "Inflation & Economic Data"  # default bucket
