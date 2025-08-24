import json
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from config import is_admin
from .db_manager import DBManager

class UIManager:
    def __init__(self):
        self.db = DBManager()
        self.news_categories = {
            "geopolitical": "Geopolitical Events",
            "central_bank": "Central Bank News",
            "economic_data": "Economic Data"
        }

    def get_register_keyboard(self) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup([[InlineKeyboardButton("✍️ Register", callback_data='register')]])

    def get_post_registration_keyboard(self) -> InlineKeyboardMarkup:
        keyboard = [
            [InlineKeyboardButton("📜 Terms & Conditions", callback_data='show_terms')],
            [InlineKeyboardButton("⚠️ Disclaimer", callback_data='show_disclaimer')],
            [InlineKeyboardButton("➡️ Proceed to Main Menu", callback_data='main_menu')]
        ]
        return InlineKeyboardMarkup(keyboard)

    def get_main_menu_keyboard(self, user_id: int) -> InlineKeyboardMarkup:
        keyboard = [
            [InlineKeyboardButton("📈 Trade Signals", callback_data='trade_signals')],
            [InlineKeyboardButton("📰 Market News", callback_data='market_news')],
            [InlineKeyboardButton("🔗 My Account", callback_data='my_account')],
            [InlineKeyboardButton("💎 Unlock Premium", callback_data='unlock_premium')],
            [InlineKeyboardButton("📨 FEEDBACK", callback_data='feedback_start')]
        ]
        if is_admin(user_id):
            keyboard.append([InlineKeyboardButton("⚙️ Admin Panel", callback_data='admin_panel')])
        return InlineKeyboardMarkup(keyboard)

    def get_premium_menu_keyboard(self) -> InlineKeyboardMarkup:
        keyboard = [
            [InlineKeyboardButton("🔗 Link My Broker Account", callback_data='link_broker_account')],
            [InlineKeyboardButton("💳 Pay One-Time Fee", callback_data='pay_one_time_fee')],
            [InlineKeyboardButton("⬅️ Back to Main Menu", callback_data='main_menu')]
        ]
        return InlineKeyboardMarkup(keyboard)

    def get_news_menu_keyboard(self, user_id: int) -> InlineKeyboardMarkup:
        user_data = self.db.get_user(user_id)
        subscriptions = json.loads(user_data.get('news_subscriptions', '[]'))
        
        keyboard = []
        for key, text in self.news_categories.items():
            status_emoji = "✅" if key in subscriptions else "🔲"
            keyboard.append([InlineKeyboardButton(f"{status_emoji} {text}", callback_data=f'toggle_news_{key}')])
        
        all_status_emoji = "✅" if len(subscriptions) == len(self.news_categories) else "🔲"
        keyboard.append([InlineKeyboardButton(f"{all_status_emoji} All Market News", callback_data='toggle_news_all')])
        keyboard.append([InlineKeyboardButton("⬅️ Back to Main Menu", callback_data='main_menu')])
        return InlineKeyboardMarkup(keyboard)

    def get_back_to_main_menu_keyboard(self) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back to Main Menu", callback_data='main_menu')]])

    def get_disclaimer_text(self) -> str:
        return (
            "**General Risk Disclaimer**\n\n"
            "Trading foreign exchange, indices, commodities, and cryptocurrencies on margin carries a high level of risk..."
        )

    def get_terms_text(self) -> str:
        return (
            "**Terms & Conditions for Linked Account Management**\n\n"
            "Welcome to the 𝕸𝕴𝕲𝕺𝕾 𝕭.™ premium service..."
        )
