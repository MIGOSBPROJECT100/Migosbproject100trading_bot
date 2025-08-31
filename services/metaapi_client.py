from services.logger import get_logger
from config import METAAPI_TOKEN, MASTER_MT5_LOGIN
import asyncio
from typing import Optional, List, Dict

logger = get_logger("metaapi")
# MetaApi SDK (sync/async)
try:
    from metaapi_cloud_sdk import MetaApi
except Exception as e:
    logger.error("MetaApi import error: %s", e)
    MetaApi = None

class MetaApiClient:
    def __init__(self, token: str):
        self.token = token
        self.api = MetaApi(token) if MetaApi else None

    async def get_account_by_login(self, login: str) -> Optional[object]:
        if not self.api:
            logger.error("MetaApi SDK not available")
            return None
        try:
            accounts = await self.api.metatrader_account_api.get_accounts()
            for acc in accounts:
                if str(acc.login) == str(login):
                    return acc
            logger.warning("No MetaApi account found by login %s", login)
            return None
        except Exception as e:
            logger.exception("Error fetching accounts: %s", e)
            return None

    async def ensure_connected(self, account_obj) -> Optional[object]:
        try:
            connection = await account_obj.get_rpc_connection()
            await connection.connect()
            await connection.wait_synchronized()
            return connection
        except Exception as e:
            logger.exception("Error connecting to account: %s", e)
            return None

    async def get_balance(self, connection) -> Optional[float]:
        try:
            acc_info = await connection.get_account_information()
            return acc_info['balance']
        except Exception as e:
            logger.exception("Error fetching balance: %s", e)
            return None

    async def get_candles(self, connection, symbol: str, timeframe: str = 'M15', count: int = 500):
        try:
            # timeframe supports: '1m','5m','15m','1h','4h','1d','1w','1mo' (MetaApi formats)
            candles = await connection.get_candles(symbol, timeframe, count=count)
            return candles
        except Exception as e:
            logger.exception("Error fetching candles for %s/%s: %s", symbol, timeframe, e)
            return []

    async def place_market_order(self, connection, symbol: str, side: str, volume: float, sl: float, tp: float, comment: str = "migosconcept$"):
        try:
            params = {
                'symbol': symbol,
                'type': 'ORDER_TYPE_BUY' if side.lower() == 'buy' else 'ORDER_TYPE_SELL',
                'volume': volume,
                'sl': sl,
                'tp': tp,
                'comment': comment
            }
            res = await connection.create_market_order(**params)
            return res
        except Exception as e:
            logger.exception("Order placement error: %s", e)
            return None

    async def fetch_recent_history(self, connection, from_time=None):
        try:
            history = await connection.get_history_orders_by_time(from_time, None, 100)
            deals = await connection.get_deals_by_time(from_time, None, 200)
            return history, deals
        except Exception as e:
            logger.exception("History fetch error: %s", e)
            return ([], [])

# Helper to get master connection
async def get_master_connection() -> Optional[object]:
    client = MetaApiClient(METAAPI_TOKEN)
    acc = await client.get_account_by_login(MASTER_MT5_LOGIN)
    if not acc:
        return None
    return await client.ensure_connected(acc)
