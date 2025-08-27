import requests, datetime as dt, pytz
from bs4 import BeautifulSoup
from utils.logger import get_logger
from utils.constants import NEWS_LOCK_WINDOW_MINUTES
from telegram.helpers import escape_markdown

log = get_logger("news.ff")

def fetch_high_impact_events(gmt3_tz="Etc/GMT-3"):
    """Scrape ForexFactory calendar for high-impact events in next ±N minutes."""
    try:
        url = "https://www.forexfactory.com/calendar?week=this"
        html = requests.get(url, timeout=15).text
        soup = BeautifulSoup(html, "html.parser")
        results = []
        for row in soup.select("tr.calendar__row--event"):
            impact = row.get("data-impact") or ""
            if "high" not in impact.lower():
                continue

            time_cell = row.select_one("td.calendar__time")
            title_cell = row.select_one("td.calendar__event")
            currency_cell = row.select_one("td.calendar__currency")
            if not (time_cell and title_cell and currency_cell):
                continue

            # sanitize title and currency
            raw_title = title_cell.get_text(strip=True)
            raw_ccy = currency_cell.get_text(strip=True)
            title = escape_markdown(raw_title, version=2)
            ccy = escape_markdown(raw_ccy, version=2)

            # parse time
            now_utc = dt.datetime.utcnow().replace(tzinfo=pytz.utc)
            event_time_utc = now_utc  # fallback
            try:
                tstr = time_cell.get_text(strip=True)  # e.g., "8:30am"
                if tstr.lower() != "all day" and tstr:
                    event_time_utc = pytz.utc.localize(
                        dt.datetime.combine(
                            now_utc.date(),
                            dt.datetime.strptime(
                                tstr.replace("am", " AM").replace("pm", " PM"),
                                "%I:%M %p"
                            ).time()
                        )
                    )
            except Exception:
                pass

            event_time_gmt3 = event_time_utc.astimezone(pytz.timezone(gmt3_tz))
            diff_minutes = abs((dt.datetime.now(pytz.timezone(gmt3_tz)) - event_time_gmt3).total_seconds()) / 60
            if diff_minutes <= NEWS_LOCK_WINDOW_MINUTES:
                results.append({"title": title, "ccy": ccy, "time": event_time_gmt3.isoformat()})
        return results
    except Exception as e:
        log.exception("FF scrape failed: %s", e)
        return []
