from telegram import Update
from telegram.ext import ContextTypes
from ui import menus, texts
from utils.auth import is_admin
from db.models import SessionLocal, User

async def show_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    kb = menus.main_menu(is_admin=is_admin(uid))
    await update.effective_message.reply_text("Choose an option:", reply_markup=kb, parse_mode="Markdown")

async def handle_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    data = q.data
    await q.answer()
    if data == "menu.signals":
        await q.edit_message_text("Trade Signals:", reply_markup=menus.signals_menu())
    elif data == "menu.account":
        await q.edit_message_text("My Account:", reply_markup=menus.account_menu())
    elif data == "menu.premium":
        await q.edit_message_text("Unlock Premium:", reply_markup=menus.premium_menu())
    elif data == "menu.news":
        with SessionLocal() as s:
            u = s.get(User, q.from_user.id)
            if not u:
                u = User(id=q.from_user.id, username=q.from_user.username or "")
                s.add(u); s.commit()
            await q.edit_message_text("Market News & Alerts\nSelect categories to subscribe:", 
                                      reply_markup=menus.news_menu(u.news_prefs))
    elif data == "menu.feedback":
        context.user_data["awaiting_feedback"] = True
        await q.edit_message_text(
            f"Dear {q.from_user.full_name},\n"
            "Your feedback is vital for improving the 𝕸𝕴𝕲𝕺𝕾 𝕭.™ experience.\n"
            "Please type and send your message now in a single message.",
            parse_mode="Markdown"
        )
    elif data.startswith("news.toggle."):
        field = {"geo":"geopolitics", "cb":"central_banks", "infl":"inflation", "all":"all"}[data.split(".")[-1]]
        with SessionLocal() as s:
            u = s.get(User, q.from_user.id)
            prefs = u.news_prefs
            new_val = not prefs.get(field, False)
            prefs[field] = new_val
            if field=="all":
                for k in ["geopolitics","central_banks","inflation"]:
                    prefs[k] = new_val
            u.news_prefs = prefs
            s.add(u); s.commit()
            await q.edit_message_reply_markup(reply_markup=menus.news_menu(prefs))
    elif data == "menu.admin":
        await q.edit_message_text("Admin Panel:", reply_markup=menus.admin_menu())
    elif data == "back.main":
        await q.edit_message_text("Main Menu:", reply_markup=menus.main_menu(is_admin=is_admin(q.from_user.id)))
