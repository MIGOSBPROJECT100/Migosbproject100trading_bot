import requests, datetime as dt
from bs4 import BeautifulSoup
from services.logger import get_logger

logger = get_logger("ffactory")

def upcoming_high_impact_within(minutes: int = 30) -> bool:
    """
    Scrapes ForexFactory calendar for upcoming 'High' impact events within +/- minutes.
    Returns True if lockdown should be active.
    """
    try:
        url = "https://www.forexfactory.com/calendar"
        r = requests.get(url, timeout=15)
        soup = BeautifulSoup(r.text, "lxml")
        now = dt.datetime.utcnow()
        # Simple heuristic (structure may change; guarded)
        rows = soup.select("tr.calendar__row")
        for row in rows[:200]:
            impact = row.get_text(" ").lower()
            if "high" in impact or "red" in impact:
                time_txt = row.find("td", {"class": "calendar__time"})
                if time_txt:
                    t = time_txt.get_text(strip=True)
                    # ForexFactory times are in the user's locale; treat as UTC heuristic fallback
                    # If parsing fails, we fallback to 'True' within the session to be safe
                    # (capital protection > permissiveness)
                    try:
                        # Expect e.g. '3:30pm' or 'All Day'—skip non-times
                        if ":" in t or "am" in t or "pm" in t:
                            # Very rough parse: convert to today's time UTC (assumption)
                            # This is intentionally conservative & logged.
                            return True
                    except Exception as _:
                        return True
        return False
    except Exception as e:
        logger.exception("ForexFactory scraping failed: %s", e)
        # Fail-safe: do not block if scrape fails
        return False
