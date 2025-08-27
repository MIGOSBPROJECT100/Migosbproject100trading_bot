import os
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from utils.logger import get_logger
from config.settings import APP_TZ, BOT_TOKEN, BRAND, PAYMENTS, ADMIN_TAGS
from ui import texts
from ui.callbacks import show_main, handle_menu
from utils.storage import get_or_create_user, feedback_allowed, set_feedback_cooldown
from utils.decorators import admin_only
from db.models import SessionLocal, User
from services.scheduler import setup_scheduler

log = get_logger("bot")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    get_or_create_user(u.id, u.username or "")
    await update.message.reply_text(texts.WELCOME, parse_mode="Markdown")
    await show_main(update, context)

async def register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Registration complete. Proceed to Main Menu.")
    await show_main(update, context)

async def terms(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(texts.TERMS, parse_mode="Markdown")

async def disclaimer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(texts.DISCLAIMER, parse_mode="Markdown")

async def link_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "🔗 Linking your account via MetaApi:\n"
        "1) Go to https://metaapi.cloud and create/login your account\n"
        "2) Add your broker account (JustMarkets)\n"
        "3) Generate your MetaApi token\n"
        "4) Paste the token here in this chat (it will be stored securely)."
    )
    await update.message.reply_text(msg)

async def my_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    with SessionLocal() as s:
        u = s.get(User, update.effective_user.id)
        await update.message.reply_text(
            f"Status:\nPremium: {u.is_premium}\nNews prefs: {u.news_prefs}\n"
            f"MT token saved: {bool(u.mt_token)}")

async def handle_pasted_token(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if len(text) > 200 and "." in text:  # token-ish
        with SessionLocal() as s:
            u = s.get(User, update.effective_user.id)
            u.mt_token = text
            s.add(u); s.commit()
        await update.message.reply_text("✅ Success! Your account token has been received and stored securely.")
        return

async def users_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    with SessionLocal() as s:
        count = s.query(User).count()
    await update.message.reply_text(f"Total registered users: {count}")

@admin_only
async def approve_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Payment approved (stub).")

@admin_only
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /broadcast <message>")
        return
    msg = " ".join(context.args)
    with SessionLocal() as s:
        users = s.query(User).all()
        for u in users:
            try:
                await context.bot.send_message(u.id, msg)
            except Exception:
                pass
    await update.message.reply_text("Broadcast sent.")

async def feedback_flow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if not feedback_allowed(uid):
        await update.message.reply_text(
            f"Dear {update.effective_user.full_name},\n"
            "You are sending feedback requests too quickly. Please wait a moment before trying again."
        )
        return
    if context.user_data.get("awaiting_feedback"):
        context.user_data["awaiting_feedback"] = False
        set_feedback_cooldown(uid)
        from config.settings import ADMIN_IDS
        for aid in ADMIN_IDS:
            try:
                await context.bot.send_message(aid, f"📨 FEEDBACK from @{update.effective_user.username}: {update.message.text}")
            except Exception:
                pass
        await update.message.reply_text(
            f"Thank you, {update.effective_user.full_name}.\n"
            "Your message has been successfully delivered to the owner.\n"
            "Managed by @Bank_Rats | @Migos_B_Fx254")
    else:
        return

def application():
    app = Application.builder().token(BOT_TOKEN).build()

    # Scheduler setup
    setup_scheduler(app, app.bot, APP_TZ)

    # Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("register", register))
    app.add_handler(CommandHandler("terms", terms))
    app.add_handler(CommandHandler("disclaimer", disclaimer))
    app.add_handler(CommandHandler("link_account", link_account))
    app.add_handler(CommandHandler("my_status", my_status))
    app.add_handler(CommandHandler("users", users_cmd))
    app.add_handler(CommandHandler("approve_payment", approve_payment))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CallbackQueryHandler(handle_menu))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_pasted_token))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, feedback_flow))

    # Safe post init hook
    async def post_init(app: Application):
        try:
            await app.bot.set_my_short_description(texts.BOT_PUBLIC_DESC)
        except Exception:
            pass

    app.post_init = post_init
    return app

def main():
    app = application()
    log.info("Bot starting...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
