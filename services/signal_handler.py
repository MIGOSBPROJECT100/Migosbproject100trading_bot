from typing import Dict, Optional
from services.logger import get_logger
from services.trading_engine import TradingEngine
from services.metaapi_client import MetaApiClient, get_master_connection
from services.order_manager import OrderManager
from services.db import set_free_signal_date, get_user
from utils.timezone import now_tz
from config import METAAPI_TOKEN, APP_TZ

logger = get_logger("signal")

class SignalHandler:
    def __init__(self):
        self.engine = TradingEngine()
        self.meta = MetaApiClient(METAAPI_TOKEN)
        self.orders = OrderManager()

    async def free_signal_available(self, user_id: int) -> bool:
        u = get_user(user_id)
        if not u:
            return False
        today = now_tz(APP_TZ).strftime("%Y-%m-%d")
        return (u["free_signal_date"] or "") != today

    async def mark_free_signal_used(self, user_id: int):
        today = now_tz(APP_TZ).strftime("%Y-%m-%d")
        set_free_signal_date(user_id, today)

    async def prepare_signal(self, symbol: str) -> Optional[Dict]:
        conn = await get_master_connection()
        if not conn:
            logger.error("Master connection unavailable")
            return None
        sig = await self.engine.analyze_and_signal(conn, symbol.replace(" ", "").replace("_","/"))
        return sig

    async def execute_signal(self, signal: Dict) -> Optional[Dict]:
        conn = await get_master_connection()
        if not conn:
            return None
        return await self.orders.place_signal_order(conn, signal)
