from typing import Dict, Optional
from services.logger import get_logger
from services.metaapi_client import MetaApiClient
from services.db import inc_daily_loss, set_cooldown
from utils.timezone import now_tz
from config import METAAPI_TOKEN, APP_TZ
from datetime import timedelta

logger = get_logger("orders")

class OrderManager:
    def __init__(self):
        self.meta = MetaApiClient(METAAPI_TOKEN)

    async def _lot_sizing(self, balance: float) -> Dict[str, float]:
        # Implements "The Risk Bible"
        tiers = [
            (30, 100, 0.01, 0.03, 0.04),
            (100, 200, 0.02, 0.05, 0.07),
            (200, 400, 0.04, 0.06, 0.10),
            (400, 700, 0.05, 0.10, 0.15),
            (700, 1100,0.07, 0.16, 0.20),
            (1100, float("inf"), 0.08, 0.17, 0.25),
        ]
        for lo, hi, min_l, max_l, max_cum in tiers:
            if lo <= balance < hi or (hi == float("inf") and balance >= lo):
                return {"min": min_l, "max": max_l, "max_cum": max_cum}
        return {"min": 0.01, "max": 0.03, "max_cum": 0.04}

    async def place_signal_order(self, connection, signal: Dict) -> Optional[Dict]:
        try:
            bal = await self.meta.get_balance(connection)
            if bal is None:
                return None
            lots = await self._lot_sizing(bal)
            volume = lots["min"]  # conservative start
            side = signal["direction"].lower()
            res = await self.meta.place_market_order(
                connection, signal["symbol"].replace("/", ""), side, volume, signal["sl"], signal["tp1"]
            )
            return res
        except Exception as e:
            logger.exception("place_signal_order failed: %s", e)
            return None

    async def post_trade_loss_protocol(self, user_id: int, loss: bool):
        if not loss: 
            return
        try:
            cnt = inc_daily_loss(user_id)
            if cnt >= 3:
                until = now_tz(APP_TZ) .replace(hour=23, minute=59, second=59, microsecond=0)
                set_cooldown(user_id, until.isoformat())
                logger.info("User %s entered Cool-Down until %s", user_id, until)
        except Exception as e:
            logger.exception("Cool-Down protocol error: %s", e)
