from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def main_menu(is_admin=False):
    rows = [
        [InlineKeyboardButton("📈 Trade Signals", callback_data="menu.signals")],
        [InlineKeyboardButton("🔗 My Account", callback_data="menu.account")],
        [InlineKeyboardButton("💎 Unlock Premium", callback_data="menu.premium")],
        [InlineKeyboardButton("📰 Market News", callback_data="menu.news")],
        [InlineKeyboardButton("📨 FEEDBACK", callback_data="menu.feedback")],
    ]
    if is_admin:
        rows.append([InlineKeyboardButton("⚙️ Admin Panel", callback_data="menu.admin")])
    return InlineKeyboardMarkup(rows)

def signals_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("CURRENCY PAIRS", callback_data="signals.fx"),
         InlineKeyboardButton("METALS", callback_data="signals.metals")]
    ])

def account_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Link Account", callback_data="account.link"),
         InlineKeyboardButton("My Status", callback_data="account.status")],
        [InlineKeyboardButton("⬅️ Back", callback_data="back.main")]
    ])

def premium_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Link My Broker Account", callback_data="premium.link")],
        [InlineKeyboardButton("Pay One-Time Fee", callback_data="premium.pay")],
        [InlineKeyboardButton("⬅️ Back", callback_data="back.main")]
    ])

def news_menu(user_prefs):
    def mark(b): return "✅" if b else "⬜️"
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"{mark(user_prefs.get('geopolitics',False))} Geopolitical Events", callback_data="news.toggle.geo")],
        [InlineKeyboardButton(f"{mark(user_prefs.get('central_banks',False))} Central Bank News", callback_data="news.toggle.cb")],
        [InlineKeyboardButton(f"{mark(user_prefs.get('inflation',False))} Inflation & Economic Data", callback_data="news.toggle.infl")],
        [InlineKeyboardButton(f"{mark(user_prefs.get('all',False))} All Market News", callback_data="news.toggle.all")],
        [InlineKeyboardButton("⬅️ Back to Main Menu", callback_data="back.main")]
    ])

def admin_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Users", callback_data="admin.users"),
         InlineKeyboardButton("Approve Payment", callback_data="admin.approve")],
        [InlineKeyboardButton("Broadcast", callback_data="admin.broadcast")],
        [InlineKeyboardButton("⬅️ Back", callback_data="back.main")]
    ])
