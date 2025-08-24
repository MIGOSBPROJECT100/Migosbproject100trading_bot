from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from .db_manager import DBManager
from .ui_builder import UIManager
from config import BOT_FOOTER

ASK_ACCOUNT_LINK = range(1)

class UserHandler:
    def __init__(self, db_manager: DBManager):
        self.db = db_manager
        self.ui = UIManager()

    async def register_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        user = query.from_user
        
        if not self.db.get_user(user.id):
            self.db.add_user(user.id, user.full_name)
            await query.edit_message_text(
                "✅ Registration successful!\n\n"
                "Before you proceed, please review our terms and disclaimer.",
                reply_markup=self.ui.get_post_registration_keyboard()
            )
        else:
            await query.edit_message_text(
                "You are already registered. Welcome back!",
                reply_markup=self.ui.get_main_menu_keyboard(user.id)
            )

    async def start_account_linking(self, update: Update, context: ContextTypes.DEFAULT_TYPE
