import requests
from bs4 import BeautifulSoup
from utils.logger import get_logger

log = get_logger("news.reuters")

def fetch_latest_headlines(limit=10):
    """Scrape Reuters Markets news (FX/central banks)."""
    urls = [
        "https://www.reuters.com/markets/currencies/",
        "https://www.reuters.com/markets/rates-bonds/"
    ]
    headlines = []
    try:
        for u in urls:
            html = requests.get(u, timeout=15, headers={"User-Agent":"Mozilla/5.0"}).text
            soup = BeautifulSoup(html, "html.parser")
            for a in soup.select("a.story-card, a[data-testid='Heading']"):
                text = a.get_text(strip=True)
                if text and text not in headlines:
                    headlines.append(text)
            if len(headlines)>=limit: break
    except Exception as e:
        log.exception("Reuters scrape failed: %s", e)
    return headlines[:limit]

def categorize(headline:str)->str:
    h = headline.lower()
    if any(k in h for k in ["fed","ecb","boe","boj","central bank","rate","hike","cut"]):
        return "central_banks"
    if any(k in h for k in ["inflation","cpi","ppi","jobs","payrolls","unemployment","gdp"]):
        return "inflation"
    if any(k in h for k in ["war","election","sanction","geopolit","conflict","ceasefire"]):
        return "geopolitics"
    return "other"
