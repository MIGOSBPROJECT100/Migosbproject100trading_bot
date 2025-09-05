import asyncio, os, time
from typing import Dict, List
from datetime import timedelta
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
)
from telegram.constants import ParseMode
from telegram.ext import (
    Application, ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters, ChatMemberHandler
)

from config import BOT_TOKEN, ADMIN_IDS, APP_TZ, JUSTMARKETS_REF_LINK, SCREENSHOT_DIR, sanity_check
from utils.markdown import mdv2, with_footer
from utils.constants import (
    TERMS_AND_CONDITIONS, GENERAL_RISK, HIGH_IMPACT_CAUTION, POST_NEWS_WAITING,
    UNAUTHORIZED_ADMIN, GROUP_WELCOME, ASSET_CLASSES, CURRENCY_PAIRS, SINGLE_INSTRUMENTS,
    NEWS_CATEGORIES, SIGNAL_TEMPLATE, TARGET_HIT_TEMPLATE
)
from utils.timezone import now_tz
from services.logger import get_logger
from services.db import init_db, upsert_user, get_user, set_user_tier, list_users, set_user_news_prefs, toggle_alert, alert_enabled, mark_feedback_ts
from services.forexfactory_scraper import upcoming_high_impact_within
from services.reuters_scraper import fetch_reuters_fx_headlines
from services.news_router import build_user_delivery
from services.tradingview_client import screenshot_chart
from services.signal_handler import SignalHandler

logger = get_logger("bot")
signal_handler = SignalHandler()

LOCKDOWN = False

def main_menu_kb(is_admin: bool=False):
    rows = [
        [InlineKeyboardButton("📈 Trade Signals", callback_data="menu_signals")],
        [InlineKeyboardButton("📰 Market News", callback_data="menu_news")],
        [InlineKeyboardButton("🔗 My Account", callback_data="menu_account")],
        [InlineKeyboardButton("💎 Unlock Premium", callback_data="menu_premium")],
        [InlineKeyboardButton("📨 FEEDBACK", callback_data="menu_feedback")],
    ]
    if is_admin:
        rows.append([InlineKeyboardButton("⚙️ Admin Panel", callback_data="menu_admin")])
    return InlineKeyboardMarkup(rows)

def signals_level2_kb():
    rows = [
        [InlineKeyboardButton("CURRENCY PAIRS", callback_data="sig_cp")],
        [InlineKeyboardButton("METALS", callback_data="sig_metals")],
        [InlineKeyboardButton("INDICES", callback_data="sig_indices")],
        [InlineKeyboardButton("ENERGIES", callback_data="sig_energies")],
        [InlineKeyboardButton("CRYPTO", callback_data="sig_crypto")],
    ]
    return InlineKeyboardMarkup(rows)

def instruments_kb(category: str):
    buttons = []
    if category == "CURRENCY PAIRS":
        for pair in CURRENCY_PAIRS:
            buttons.append([InlineKeyboardButton(pair, callback_data=f"inst::{pair}")])
    else:
        for inst in SINGLE_INSTRUMENTS.get(category, []):
            buttons.append([InlineKeyboardButton(inst, callback_data=f"inst::{inst}")])
    return InlineKeyboardMarkup(buttons)

def instrument_actions_kb(instrument: str, alerts_on: bool):
    toggle = "🔕 Disable" if alerts_on else "🔔 Enable"
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Market Signal", callback_data=f"act::signal::{instrument}")],
        [InlineKeyboardButton(f"{toggle} {instrument} Alerts", callback_data=f"act::toggle::{instrument}")],
        [InlineKeyboardButton("⬅️ Back", callback_data="menu_signals")]
    ])

def account_menu_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Link My Broker Account (/link_account)", callback_data="acc_link")],
        [InlineKeyboardButton("My Status (/my_status)", callback_data="acc_status")],
        [InlineKeyboardButton("⬅️ Back", callback_data="back_main")],
    ])

def premium_menu_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Link My Broker Account", callback_data="acc_link")],
        [InlineKeyboardButton("Pay One-Time Fee", callback_data="premium_pay")],
        [InlineKeyboardButton("⬅️ Back", callback_data="back_main")],
    ])

def news_menu_kb(u):
    def icon(flag): return "✅" if flag else "☐"
    rows = [
        [InlineKeyboardButton(f"{icon(u['news_geo'])} Geopolitical Events", callback_data="news_geo")],
        [InlineKeyboardButton(f"{icon(u['news_cb'])} Central Bank News (Fed, ECB)", callback_data="news_cb")],
        [InlineKeyboardButton(f"{icon(u['news_cpi'])} Inflation & Economic Data", callback_data="news_cpi")],
        [InlineKeyboardButton("All Market News (toggle)", callback_data="news_all")],
        [InlineKeyboardButton("⬅️ Back", callback_data="back_main")],
    ]
    return InlineKeyboardMarkup(rows)

def admin_menu_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("/users", callback_data="admin_users")],
        [InlineKeyboardButton("/approve_payment", callback_data="admin_approve")],
        [InlineKeyboardButton("/broadcast", callback_data="admin_broadcast")],
        [InlineKeyboardButton("⬅️ Back", callback_data="back_main")],
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        u = update.effective_user
        upsert_user(u.id, u.username or "", f"{u.first_name or ''} {u.last_name or ''}".strip())
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("✍️ Register", callback_data="register")]])
        text = with_footer(mdv2("Welcome! Press the button below to register."))
        await update.effective_message.reply_text(text, reply_markup=kb, parse_mode=ParseMode.MARKDOWN_V2, protect_content=True, disable_web_page_preview=True)
    except Exception as e:
        logger.exception("start error: %s", e)

async def register_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        q = update.callback_query; await q.answer()
        u = q.from_user
        upsert_user(u.id, u.username or "", f"{u.first_name or ''} {u.last_name or ''}".strip())
        # Post-registration menu
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔔 Subscribe to General Updates", callback_data="sub_updates")],
            [InlineKeyboardButton("📜 Terms & Conditions", callback_data="terms")],
            [InlineKeyboardButton("⚠️ Disclaimer", callback_data="disclaimer")],
            [InlineKeyboardButton("➡️ Proceed to Main Menu", callback_data="to_main")],
        ])
        text = with_footer(mdv2("Registration complete. Configure your preferences below."))
        await q.edit_message_text(
    text=text,
    reply_markup=kb,
    parse_mode=ParseMode.MARKDOWN_V2
        )
    except Exception as e:
        logger.exception("register_cb error: %s", e)

async def to_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        q = update.callback_query; await q.answer()
        u = q.from_user
        row = get_user(u.id)
        kb = main_menu_kb(is_admin=(u.id in ADMIN_IDS))
        text = with_footer(mdv2("Main Menu"))
        await q.edit_message_text(
    text=text,
    reply_markup=kb,
    parse_mode=ParseMode.MARKDOWN_V2
        )
    except Exception as e:
        logger.exception("to_main error: %s", e)

async def post_registration_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        q = update.callback_query; await q.answer()
        data = q.data
        u = q.from_user
        if data == "terms":
            await q.message.reply_text(with_footer(mdv2(TERMS_AND_CONDITIONS)), parse_mode=ParseMode.MARKDOWN_V2, protect_content=True)
        elif data == "disclaimer":
            await q.message.reply_text(with_footer(mdv2(GENERAL_RISK)), parse_mode=ParseMode.MARKDOWN_V2, protect_content=True)
        elif data == "sub_updates":
            await q.message.reply_text(with_footer(mdv2("Subscribed to general updates.")), parse_mode=ParseMode.MARKDOWN_V2, protect_content=True)
        elif data == "to_main":
            await to_main(update, context)
    except Exception as e:
        logger.exception("post_registration_buttons error: %s", e)

# Main Menu routing
async def main_menu_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        q = update.callback_query; await q.answer()
        data = q.data
        u = q.from_user
        if data == "menu_signals":
            await q.edit_message_text(with_footer(mdv2("Select an asset class")), reply_markup=signals_level2_kb(), parse_mode=ParseMode.MARKDOWN_V2)
        elif data.startswith("sig_"):
            mapping = {
                "sig_cp": "CURRENCY PAIRS",
                "sig_metals": "METALS",
                "sig_indices": "INDICES",
                "sig_energies": "ENERGIES",
                "sig_crypto": "CRYPTO"
            }
            cat = mapping[data]
            await q.edit_message_text(with_footer(mdv2(f"{cat}")), reply_markup=instruments_kb(cat), parse_mode=ParseMode.MARKDOWN_V2, protect_content=True)
        elif data.startswith("inst::"):
            instrument = data.split("::",1)[1]
            alerts_on = alert_enabled(u.id, instrument)
            await q.edit_message_text(with_footer(mdv2(f"{instrument}")), reply_markup=instrument_actions_kb(instrument, alerts_on), parse_mode=ParseMode.MARKDOWN_V2, protect_content=True)
        elif data.startswith("act::"):
            _, action, instrument = data.split("::", 2)
            if action == "toggle":
                new_state = toggle_alert(u.id, instrument)
                await q.edit_message_reply_markup(reply_markup=instrument_actions_kb(instrument, new_state))
            elif action == "signal":
                # High-impact news lockdown
                global LOCKDOWN
                if LOCKDOWN or upcoming_high_impact_within(30):
                    LOCKDOWN = True
                    await q.message.reply_text(with_footer(mdv2(HIGH_IMPACT_CAUTION)), parse_mode=ParseMode.MARKDOWN_V2, protect_content=True)
                    await q.message.reply_text(with_footer(mdv2(POST_NEWS_WAITING)), parse_mode=ParseMode.MARKDOWN_V2, protect_content=True)
                    return
                # Free tier: 1 free signal / day
                urow = get_user(u.id)
                if urow and urow["tier"] == "free":
                    if not await signal_handler.free_signal_available(u.id):
                        await q.message.reply_text(with_footer(mdv2("Free signal limit reached for today.")), parse_mode=ParseMode.MARKDOWN_V2, protect_content=True)
                        return
                msg = await q.message.reply_text(with_footer(mdv2("Analyzing...")), parse_mode=ParseMode.MARKDOWN_V2, protect_content=True)
                sig = await signal_handler.prepare_signal(instrument)
                if not sig:
                    await msg.edit_text(with_footer(mdv2("No high-probability setup right now. Check back later.")), parse_mode=ParseMode.MARKDOWN_V2, protect_content=True)
                    return
                # Screenshot first
                shot = await screenshot_chart(instrument.replace(" ", "").replace("_","/"), timeframe="15")
                try:
                    if shot and os.path.exists(shot):
                        await q.message.reply_photo(photo=open(shot, "rb"), caption=with_footer(mdv2("Chart Snapshot")), parse_mode=ParseMode.MARKDOWN_V2, protect_content=True)
                except Exception as e:
                    logger.exception("screenshot send failed: %s", e)
                # Signal message
                text = SIGNAL_TEMPLATE.format(
                    entry=sig["entry"], tp1=sig["tp1"], tp2=sig["tp2"], tp3=sig["tp3"], sl=sig["sl"],
                    tp1_pips=sig["tp1_pips"], tp2_pips=sig["tp2_pips"], tp3_pips=sig["tp3_pips"], sl_pips=sig["sl_pips"]
                )
                await q.message.reply_text(with_footer(mdv2(text)), parse_mode=ParseMode.MARKDOWN_V2, protect_content=True)
                if urow and urow["tier"] == "free":
                    await signal_handler.mark_free_signal_used(u.id)
    except Exception as e:
        logger.exception("main_menu_router error: %s", e)

# Account & Premium & Admin Menu
async def account_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        q = update.callback_query; await q.answer()
        data = q.data
        if data == "menu_account":
            await q.edit_message_text(with_footer(mdv2("Account Menu")), reply_markup=account_menu_kb(), parse_mode=ParseMode.MARKDOWN_V2, protect_content=True)
        elif data == "acc_link":
            text = (
                "1. Go to https://metaapi.cloud and create an account.\n"
                "2. Link your broker and add your MT5 account to MetaApi's secure vault.\n"
                "3. Generate your API Token.\n"
                "Your trading password is only ever given to MetaApi's secure vault, not to our bot.\n\n"
                "Please paste your MetaApi Token here."
            )
            await q.message.reply_text(with_footer(mdv2(text)), parse_mode=ParseMode.MARKDOWN_V2, protect_content=True)
            context.user_data["awaiting_metaapi_token"] = True
        elif data == "acc_status":
            urow = get_user(q.from_user.id)
            tier = urow["tier"] if urow else "free"
            await q.message.reply_text(with_footer(mdv2(f"Your status: {tier}")), parse_mode=ParseMode.MARKDOWN_V2, protect_content=True)
        elif data == "menu_premium":
            await q.edit_message_text(with_footer(mdv2("Unlock Premium")), reply_markup=premium_menu_kb(), parse_mode=ParseMode.MARKDOWN_V2, protect_content=True)
        elif data == "premium_pay":
            text = (
                "Pay Ksh 3000 via:\n"
                "• Binance Pay: migosblazer4@gmail.com\n"
                "• M-Pesa: +254746362427 - Ndung'u Kibera\n\n"
                "Upload your payment screenshot here for admin approval."
            )
            await q.message.reply_text(with_footer(mdv2(text)), parse_mode=ParseMode.MARKDOWN_V2, protect_content=True)
        elif data == "menu_admin":
            if q.from_user.id not in ADMIN_IDS:
                await q.message.reply_text(with_footer(mdv2(UNAUTHORIZED_ADMIN)), parse_mode=ParseMode.MARKDOWN_V2, protect_content=True)
                return
            await q.edit_message_text(with_footer(mdv2("Admin Panel")), reply_markup=admin_menu_kb(), parse_mode=ParseMode.MARKDOWN_V2, protect_content=True)
        elif data == "back_main":
            await to_main(update, context)
    except Exception as e:
        logger.exception("account_router error: %s", e)

async def news_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        q = update.callback_query; await q.answer()
        data = q.data
        urow = get_user(q.from_user.id)
        if data == "menu_news":
            await q.edit_message_text(with_footer(mdv2("Market News Preferences")), reply_markup=news_menu_kb(urow), parse_mode=ParseMode.MARKDOWN_V2, protect_content=True)
        elif data in ["news_geo","news_cb","news_cpi","news_all"]:
            geo, cb, cpi = urow["news_geo"], urow["news_cb"], urow["news_cpi"]
            if data == "news_geo": geo = 0 if geo else 1
            if data == "news_cb": cb = 0 if cb else 1
            if data == "news_cpi": cpi = 0 if cpi else 1
            if data == "news_all":
                val = 0 if (geo and cb and cpi) else 1
                geo, cb, cpi = val, val, val
            set_user_news_prefs(q.from_user.id, geo, cb, cpi)
            urow = get_user(q.from_user.id)
            await q.edit_message_reply_markup(reply_markup=news_menu_kb(urow))
    except Exception as e:
        logger.exception("news_router error: %s", e)

async def on_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        u = update.effective_user
        text = (update.message.text or "").strip()
        if context.user_data.get("awaiting_metaapi_token"):
            # Store securely
            from services.db import _connect, _lock
            with _lock:
                conn = _connect()
                conn.execute("UPDATE users SET metaapi_token=?, tier=?, premium_approved=? WHERE user_id=?", (text, "premium", 1, u.id))
                conn.commit(); conn.close()
            context.user_data["awaiting_metaapi_token"] = False
            msg = "✅ Success! Your account token has been received and is now securely encrypted. Your account is linked. The bot will now begin monitoring for migosconcept$ opportunities to manage your account as per the agreed Terms & Conditions."
            await update.message.reply_text(with_footer(mdv2(msg)), parse_mode=ParseMode.MARKDOWN_V2, protect_content=True)
            return

        # Upload payment screenshot (premium one-time fee)
        if update.message.photo:
            file_id = update.message.photo[-1].file_id
            from services.db import _connect, _lock
            with _lock:
                conn = _connect()
                conn.execute("INSERT INTO payments(user_id, method, screenshot_file_id, created_at) VALUES (?, ?, ?, datetime('now'))", (u.id, "upload", file_id))
                conn.commit(); conn.close()
            await update.message.reply_text(with_footer(mdv2("Payment screenshot received. Await admin approval.")), parse_mode=ParseMode.MARKDOWN_V2, protect_content=True)
            return

        # Feedback (rate limited 60 sec)
        if "feedback_mode" in context.user_data and context.user_data["feedback_mode"]:
            now = int(time.time())
            urow = get_user(u.id)
            last = urow["feedback_last_ts"] if urow else 0
            if now - last < 60:
                warn = f"Dear {u.first_name}, You are sending feedback requests too quickly. To prevent spam, please wait a moment before trying again. This is an automated message to ensure fair usage for all users."
                await update.message.reply_text(with_footer(mdv2(warn)), parse_mode=ParseMode.MARKDOWN_V2, protect_content=True)
                return
            mark_feedback_ts(u.id, now)
            # Forward to owner (first admin)
            await context.bot.send_message(chat_id=ADMIN_IDS[0], text=with_footer(mdv2(f"Feedback from {u.id} @{u.username or ''}: {text}")), parse_mode=ParseMode.MARKDOWN_V2, protect_content=True)
            confirm = f"Thank you, {u.first_name}. Your message has been successfully delivered to the owner. We appreciate you taking the time to help us improve."
            await update.message.reply_text(with_footer(mdv2(confirm)), parse_mode=ParseMode.MARKDOWN_V2, protect_content=True)
            context.user_data["feedback_mode"] = False
            return

    except Exception as e:
        logger.exception("on_message error: %s", e)

async def menu_feedback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        q = update.callback_query; await q.answer()
        prompt = f"Dear {q.from_user.first_name}, Your feedback is vital for improving the 𝕸𝕴𝕲𝕺𝕾 𝕭.™ experience. Please type and send your message now. Whether it's a suggestion, a compliment, or a concern, I will forward it directly to the owner for review. Please send your entire feedback in a single message."
        await q.message.reply_text(with_footer(mdv2(prompt)), parse_mode=ParseMode.MARKDOWN_V2, protect_content=True)
        context.user_data["feedback_mode"] = True
    except Exception as e:
        logger.exception("menu_feedback error: %s", e)

# Admin Commands
async def cmd_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text(with_footer(mdv2(UNAUTHORIZED_ADMIN)), parse_mode=ParseMode.MARKDOWN_V2, protect_content=True)
        return
    try:
        rows = list_users()
        lines = [f"{r['user_id']} @{r['username'] or ''} {r['full_name']} | {r['tier']} | approved={r['premium_approved']}" for r in rows]
        text = "Registered Users:\n" + "\n".join(lines) if lines else "No users."
        await update.message.reply_text(with_footer(mdv2(text)), parse_mode=ParseMode.MARKDOWN_V2, protect_content=True)
    except Exception as e:
        logger.exception("/users error: %s", e)

async def cmd_approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text(with_footer(mdv2(UNAUTHORIZED_ADMIN)), parse_mode=ParseMode.MARKDOWN_V2, protect_content=True)
        return
    try:
        if not context.args:
            await update.message.reply_text(with_footer(mdv2("Usage: /approve_payment <user_id>")), parse_mode=ParseMode.MARKDOWN_V2, protect_content=True); return
        user_id = int(context.args[0])
        set_user_tier(user_id, "premium", 1)
        await update.message.reply_text(with_footer(mdv2(f"User {user_id} upgraded to Premium.")), parse_mode=ParseMode.MARKDOWN_V2, protect_content=True)
    except Exception as e:
        logger.exception("/approve_payment error: %s", e)

async def cmd_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text(with_footer(mdv2(UNAUTHORIZED_ADMIN)), parse_mode=ParseMode.MARKDOWN_V2, protect_content=True)
        return
    try:
        msg = " ".join(context.args) if context.args else ""
        if not msg:
            await update.message.reply_text(with_footer(mdv2("Usage: /broadcast <message>")), parse_mode=ParseMode.MARKDOWN_V2, protect_content=True); return
        for r in list_users():
            try:
                await context.bot.send_message(r["user_id"], with_footer(mdv2(msg)), parse_mode=ParseMode.MARKDOWN_V2, protect_content=True)
            except Exception as e:
                logger.exception("Broadcast to %s failed: %s", r["user_id"], e)
        await update.message.reply_text(with_footer(mdv2("Broadcast completed.")), parse_mode=ParseMode.MARKDOWN_V2, protect_content=True)
    except Exception as e:
        logger.exception("/broadcast error: %s", e)

# Group welcome
async def on_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        cm = update.chat_member
        if cm.new_chat_member and cm.new_chat_member.user and cm.new_chat_member.user.id != context.bot.id:
            name = cm.new_chat_member.user.first_name
            group = update.effective_chat.title or "the group"
            text = GROUP_WELCOME.format(name=name, group=group)
            kb = InlineKeyboardMarkup([[InlineKeyboardButton('✍️ Press "Register" to Use Me', callback_data="register")]])
            await context.bot.send_message(update.effective_chat.id, with_footer(mdv2(text)), parse_mode=ParseMode.MARKDOWN_V2, reply_markup=kb, protect_content=True)
    except Exception as e:
        logger.exception("on_member error: %s", e)

# Weekly report
async def cmd_weekly_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # Minimal stub: in production, aggregate signals/trades from DB
        text = "Weekly Report: Total Pips: N/A | Win/Loss: N/A (data aggregation in progress)"
        await update.message.reply_text(with_footer(mdv2(text)), parse_mode=ParseMode.MARKDOWN_V2, protect_content=True)
    except Exception as e:
        logger.exception("/weekly_report error: %s", e)

# Periodic tasks: lockdown toggle & news pushing
async def scheduler_tick(app: Application):
    global LOCKDOWN
    try:
        LOCKDOWN = upcoming_high_impact_within(30)
        if LOCKDOWN:
            logger.info("High-impact lockdown active.")
        # Push personalized Reuters news
        headlines = fetch_reuters_fx_headlines()
        delivery = build_user_delivery(headlines)
        for uid, items in delivery.items():
            for h in items[:5]:
                try:
                    await app.bot.send_message(uid, with_footer(mdv2(f"{h['title']}\n{h['url']}")), parse_mode=ParseMode.MARKDOWN_V2, protect_content=True, disable_web_page_preview=False)
                except Exception as e:
                    logger.exception("News push to %s failed: %s", uid, e)
    except Exception as e:
        logger.exception("scheduler_tick error: %s", e)

async def run_scheduler(app: Application):
    while True:
        await scheduler_tick(app)
        await asyncio.sleep(900)  # every 15 minutes

async def on_error(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.exception("Unhandled error: %s", context.error)

async def on_ready(app: Application):
    logger.info("Bot started. Sanity missing keys: %s", sanity_check())

def build_app() -> Application:
    init_db()
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("weekly_report", cmd_weekly_report))
    application.add_handler(CommandHandler("users", cmd_users))
    application.add_handler(CommandHandler("approve_payment", cmd_approve))
    application.add_handler(CommandHandler("broadcast", cmd_broadcast))
    application.add_handler(CallbackQueryHandler(register_cb, pattern="^register$"))
    application.add_handler(CallbackQueryHandler(post_registration_buttons, pattern="^(terms|disclaimer|sub_updates|to_main)$"))
    application.add_handler(CallbackQueryHandler(main_menu_router, pattern="^(menu_signals|sig_.*|inst::.*|act::.*)$"))
    application.add_handler(CallbackQueryHandler(account_router, pattern="^(menu_account|acc_link|acc_status|menu_premium|premium_pay|menu_admin|back_main)$"))
    application.add_handler(CallbackQueryHandler(news_router, pattern="^(menu_news|news_.*)$"))
    application.add_handler(CallbackQueryHandler(menu_feedback, pattern="^menu_feedback$"))
    application.add_handler(MessageHandler(filters.TEXT | filters.PHOTO, on_message))
    application.add_handler(ChatMemberHandler(on_member, ChatMemberHandler.CHAT_MEMBER))
    application.add_error_handler(on_error)
    return application

async def main():
    app = build_app()
    asyncio.create_task(run_scheduler(app))
    await on_ready(app)
    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    import nest_asyncio
    nest_asyncio.apply()
    asyncio.run(main())
