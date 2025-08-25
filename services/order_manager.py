from utils.logger import get_logger
from db.models import SessionLocal, SignalLog, NewsLock

log = get_logger("orders")

class OrderManager:
    def __init__(self):
        pass

    def is_lockdown(self)->bool:
        with SessionLocal() as s:
            lk = s.query(NewsLock).first()
            return bool(lk and lk.active)

    def log_signal(self, symbol, direction, tp1, tp2, tp3, sl):
        with SessionLocal() as s:
            s.add(SignalLog(symbol=symbol, direction=direction, tp1=tp1, tp2=tp2, tp3=tp3, sl=sl))
            s.commit()
