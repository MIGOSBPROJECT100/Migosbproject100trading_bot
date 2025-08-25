from services.order_manager import OrderManager
from services.tradingview_client import TradingViewClient
from utils.logger import get_logger

log = get_logger("signals")

class SignalHandler:
    def __init__(self):
        self.om = OrderManager()
        self.tv = TradingViewClient()

    async def send_signal(self, bot, chat_id:int, symbol:str, direction:str, entry:float, tp1:float, tp2:float, tp3:float, sl:float):
        if self.om.is_lockdown():
            await bot.send_message(chat_id, 
                "🚫 Lockdown active due to high-impact news. No new trades will be opened." +
                "\nPATIENCE ✰ DISCIPLINE ✰ RISK MANAGEMENT")
            return
        shot = await self.tv.screenshot_symbol(symbol, timeframe="15")
        try:
            await bot.send_photo(chat_id=chat_id, photo=open(shot, "rb"))
        except Exception:
            pass
        txt = (
            f"🟢 READY SIGNAL: {direction.upper()} 🟢\n"
            "Disclaimer: This is not financial advice. Please conduct your own analysis. "
            "If you are seeing this alert more than 5 minutes after it was sent, consider waiting for the next opportunity. "
            "You are solely responsible for your trading decisions.\n\n"
            f"{direction.upper()} At: {entry}\n"
            f"Target 1: {tp1}\nTarget 2: {tp2}\nTarget 3: {tp3}\n"
            f"🛑 Stop-Loss: {sl}\n"
            "PATIENCE ✰ DISCIPLINE ✰ RISK MANAGEMENT"
        )
        await bot.send_message(chat_id=chat_id, text=txt)
