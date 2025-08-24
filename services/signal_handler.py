from telegram import Update
from telegram.ext import ContextTypes
from .db_manager import DBManager
from .trading_engine import TradingEngine
from .order_manager import OrderManager
from config import BOT_SLOGAN

class SignalHandler:
    def __init__(self, db_manager: DBManager):
        self.db = db_manager
        self.trading_engine = TradingEngine()

    async def check_for_signals(self, context: ContextTypes.DEFAULT_TYPE):
        # This function would be called periodically by a job queue
        signal = self.trading_engine.find_migos_concept_setup()
        
        if signal:
            # Get all premium users
            all_users = self.db.get_all_users()
            premium_users = [u for u in all_users if u['account_status'] == 'Premium' and u['meta_api_token']]
            
            # Create signal message
            signal_message = self.format_signal_message(signal)
            
            for user in premium_users:
                # Send signal message to user via Telegram
                await context.bot.send_message(chat_id=user['user_id'], text=signal_message, parse_mode='Markdown')
                
                # Execute trade on their linked account
                order_manager = OrderManager(user['meta_api_token'])
                # This needs the account_id from MetaApi, which we don't store yet.
                # This part needs more logic to map user_id to metaapi account_id.
                # await order_manager.execute_trade(account_id, signal)

    def format_signal_message(self, signal: dict) -> str:
        trade_type = "BUY" if signal['type'] == 'buy' else "SELL"
        emoji = "🟢" if trade_type == "BUY" else "🔴"
        
        message = (
            f"{emoji} **READY SIGNAL: {trade_type}** {emoji}\n\n"
            f"**Symbol:** {signal['symbol']}\n"
            f"**Entry At:** {signal['entry']}\n"
            f"**Target 1:** {signal['tp1']} ({signal['tp1_pips']} Pips)\n"
            f"**Target 2:** {signal['tp2']} ({signal['tp2_pips']} Pips)\n"
            f"**Target 3:** {signal['tp3']} ({signal['tp3_pips']} Pips)\n"
            f"🛑 **Stop-Loss:** {signal['sl']} ({signal['sl_pips']} Pips)\n\n"
            "_Disclaimer: This is not financial advice. Please conduct your own analysis. "
            "You are solely responsible for your trading decisions._\n\n"
            f"**{BOT_SLOGAN}**"
        )
        return message
