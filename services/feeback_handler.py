import time
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from .db_manager import DBManager
from config import FEEDBACK_COOLDOWN_SECONDS, BOT_FOOTER, ADMIN_IDS

# Conversation states
ASK_FEEDBACK = range(1)

class FeedbackHandler:
    def __init__(self, db_manager: DBManager):
        self.db = db_manager

    async def start_feedback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        user_id = update.effective_user.id
        user_data = self.db.get_user(user_id)
        current_time = int(time.time())

        if current_time - user_data.get('last_feedback_time', 0) < FEEDBACK_COOLDOWN_SECONDS:
            await context.bot.send_message(
                chat_id=user_id,
                text=f"Dear {update.effective_user.mention_html()},\n\n"
                     "You are sending feedback requests too quickly. To prevent spam, please wait a moment before trying again.\n\n"
                     "_This is an automated message to ensure fair usage for all users._",
                parse_mode='HTML'
            )
            return ConversationHandler.END

        await context.bot.send_message(
            chat_id=user_id,
            text=f"Dear {update.effective_user.mention_html()},\n\n"
                 "Your feedback is vital for improving the 𝕸𝕴𝕲𝕺𝕾 𝕭.™ experience.\n\n"
                 "Please type and send your message now. Whether it's a suggestion, a compliment, or a concern, I will forward it directly to the owner for review.\n\n"
                 "_Please send your entire feedback in a single message._",
            parse_mode='HTML'
        )
        return ASK_FEEDBACK

    async def receive_feedback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        user = update.effective_user
        
        # Forward the original message to all admins
        for admin_id in ADMIN_IDS:
            try:
                await context.bot.forward_message(chat_id=admin_id, from_chat_id=user.id, message_id=update.message.message_id)
            except Exception as e:
                print(f"Could not forward message to admin {admin_id}: {e}")

        # Send confirmation to the user
        await update.message.reply_text(
            f"Thank you, {user.mention_html()}.\n\n"
            "Your message has been successfully delivered to the owner. We appreciate you taking the time to help us improve.\n\n"
            f"{BOT_FOOTER}",
            parse_mode='HTML'
        )

        self.db.update_user_feedback_time(user.id)
        return ConversationHandler.END
