from apscheduler.schedulers.asyncio import AsyncIOScheduler
from db.models import SessionLocal, User, NewsLock
from services.news_forexfactory import fetch_high_impact_events
from services.news_reuters import fetch_latest_headlines, categorize
from utils.logger import get_logger

log = get_logger("sched")

def setup_scheduler(app, bot, tz):
    sch = AsyncIOScheduler(timezone=tz)

    async def news_lock_job():
        try:
            evts = fetch_high_impact_events()
            with SessionLocal() as s:
                lock = s.query(NewsLock).first()
                if not lock: 
                    from db.models import NewsLock as NL
                    lock = NL(active=False, reason="")
                    s.add(lock); s.commit()
                if evts:
                    lock.active, lock.reason = True, f"High-impact event: {evts[0]['title']}"
                else:
                    lock.active, lock.reason = False, ""
                s.add(lock); s.commit()
        except Exception as e:
            log.exception("news_lock_job failed: %s", e)

    async def reuters_push_job():
        try:
            headlines = fetch_latest_headlines()
            if not headlines: return
            with SessionLocal() as s:
                users = s.query(User).all()
                for h in headlines:
                    cat = categorize(h)
                    for u in users:
                        p = u.news_prefs or {}
                        if p.get("all") or p.get(cat):
                            try:
                                await bot.send_message(chat_id=u.id, text=f"📰 {h}")
                            except Exception:
                                pass
        except Exception as e:
            log.exception("reuters_push_job failed: %s", e)

    sch.add_job(news_lock_job, "interval", minutes=5, id="ff_lock")
    sch.add_job(reuters_push_job, "interval", minutes=15, id="reuters_push")
    sch.start()
    return sch
