import logging
from telegram import Update
from telegram.ext import ContextTypes
from config import is_admin, ADMIN_USERNAMES

# Set up logging
logger = logging.getLogger(__name__)

def admin_only(func):
    """
    A decorator to restrict access to a function to admins only.
    This provides a cleaner way to protect admin commands.
    """
    async def wrapped(self, update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        if not is_admin(user_id):
            message = (
                f"This action is denied. The requested command is for admin use only.\n"
                f"For assistance, please contact {ADMIN_USERNAMES}."
            )
            
            # Handle both command messages and callback queries
            if update.message:
                await update.message.reply_text(message)
            elif update.callback_query:
                await update.callback_query.answer(message, show_alert=True)
            
            logger.warning(f"Unauthorized access attempt by user {user_id}.")
            return
        return await func(self, update, context, *args, **kwargs)
    return wrapped

def get_user_mention(user) -> str:
    """
    Safely gets a user's HTML mention tag.
    """
    if not user:
        return "Unknown User"
    return user.mention_html()

# You can add more helper functions here as the bot grows.
# For example, a function to format numbers, parse dates, etc.

