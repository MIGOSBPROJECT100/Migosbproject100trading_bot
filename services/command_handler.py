import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, ConversationHandler
from .db_manager import DBManager
from .user_handler import UserHandler
from .feedback_handler import FeedbackHandler
from .ui_builder import UIManager
from .signal_handler import SignalHandler
from .news_handler import NewsHandler
from config import is_admin, ADMIN_USERNAMES

logger = logging.getLogger(__name__)

# Conversation states
ASK_FEEDBACK, ASK_PREMIUM_SUB, ASK_ACCOUNT_LINK = range(3)

class BotCommandHandler:
    def __init__(self):
        self.db = DBManager()
        self.user_handler = UserHandler(self.db)
        self.feedback_handler = FeedbackHandler(self.db)
        self.ui = UIManager()
        self.signal_handler = SignalHandler(self.db)
        self.news_handler = NewsHandler(self.db)

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user = update.effective_user
        if not self.db.get_user(user.id):
            await update.message.reply_text(
                "Welcome to 𝕸𝕴𝕲𝕺𝕾 𝕭.™!\n\n"
                "Your 24/7 Digital Trading Twin. Powered by the migosconcept$ strategy to analyze markets, manage trades, and turn data into discipline. "
                "Ready to go from Grass to Grace? Press Register.",
                reply_markup=self.ui.get_register_keyboard()
            )
        else:
            await update.message.reply_text(
                "Welcome back! Here is the main menu:",
                reply_markup=self.ui.get_main_menu_keyboard(user.id)
            )

    async def button_router(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        query = update.callback_query
        await query.answer()
        user_id = query.from_user.id
        action = query.data

        if action == 'register':
            await self.user_handler.register_user(update, context)
        elif action == 'main_menu':
            await query.edit_message_text("Main Menu:", reply_markup=self.ui.get_main_menu_keyboard(user_id))
        elif action == 'show_disclaimer':
            await query.edit_message_text(self.ui.get_disclaimer_text(), parse_mode='Markdown', reply_markup=self.ui.get_back_to_main_menu_keyboard())
        elif action == 'show_terms':
            await query.edit_message_text(self.ui.get_terms_text(), parse_mode='Markdown', reply_markup=self.ui.get_back_to_main_menu_keyboard())
        elif action == 'unlock_premium':
            await query.edit_message_text("Choose how you'd like to unlock Premium features:", reply_markup=self.ui.get_premium_menu_keyboard())
        elif action == 'link_broker_account':
            await self.user_handler.start_account_linking(update, context)
            return ASK_ACCOUNT_LINK
        elif action == 'market_news':
            await self.news_handler.show_news_menu(update, context)
        elif action.startswith('toggle_news_'):
            await self.news_handler.toggle_news_subscription(update, context)
        else:
            await query.edit_message_text("This feature is under construction.", reply_markup=self.ui.get_back_to_main_menu_keyboard())

    async def feedback_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        query = update.callback_query
        await query.answer()
        return await self.feedback_handler.start_feedback(update, context)

    async def feedback_receive(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        return await self.feedback_handler.receive_feedback(update, context)
        
    async def link_account_receive(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        return await self.user_handler.receive_account_token(update, context)

    async def _admin_check(self, update: Update) -> bool:
        user_id = update.effective_user.id
        if not is_admin(user_id):
            message = (
                f"This action is denied. The requested command is for admin use only.\n"
                f"For assistance, please contact {ADMIN_USERNAMES}."
            )
            if update.message:
                await update.message.reply_text(message)
            elif update.callback_query:
                await update.callback_query.answer(message, show_alert=True)
            return False
        return True

    async def admin_list_users(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not await self._admin_check(update): return
        users = self.db.get_all_users()
        if not users:
            await update.message.reply_text("No users found in the database.")
            return
        message = "Registered Users:\n\n"
        for user in users:
            message += f"- ID: `{user['user_id']}`, Name: {user['telegram_name']}, Status: {user['account_status']}\n"
        await update.message.reply_text(message, parse_mode='Markdown')

    async def admin_broadcast(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not await self._admin_check(update): return
        # Logic for broadcast
        await update.message.reply_text("Broadcast command received. Feature in development.")

    async def admin_approve_payment(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not await self._admin_check(update): return
        # Logic to approve payment
        await update.message.reply_text("Approve payment command received. Feature in development.")

def setup_handlers(application: Application):
    command_handler = BotCommandHandler()

    feedback_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(command_handler.feedback_start, pattern='^feedback_start$')],
        states={ASK_FEEDBACK: [MessageHandler(None, command_handler.feedback_receive)]},
        fallbacks=[CommandHandler('start', command_handler.start)],
    )
    
    link_account_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(command_handler.button_router, pattern='^link_broker_account$')],
        states={ASK_ACCOUNT_LINK: [MessageHandler(None, command_handler.link_account_receive)]},
        fallbacks=[CommandHandler('start', command_handler.start)],
    )

    application.add_handler(CommandHandler("start", command_handler.start))
    application.add_handler(CallbackQueryHandler(command_handler.button_router))
    application.add_handler(feedback_conv)
    application.add_handler(link_account_conv)
    
    # Admin commands
    application.add_handler(CommandHandler("users", command_handler.admin_list_users))
    application.add_handler(CommandHandler("broadcast", command_handler.admin_broadcast))
    application.add_handler(CommandHandler("approve_payment", command_handler.admin_approve_payment))
