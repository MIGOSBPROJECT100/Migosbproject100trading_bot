from functools import wraps
from telegram.ext import ContextTypes
from utils.auth import is_admin
from utils.constants import ADMIN_DENIAL

def admin_only(func):
    @wraps(func)
    async def wrapper(update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        uid = update.effective_user.id if update.effective_user else 0
        if not is_admin(uid):
            await update.effective_message.reply_text(ADMIN_DENIAL, parse_mode="Markdown")
            return
        return await func(update, context, *args, **kwargs)
    return wrapper
