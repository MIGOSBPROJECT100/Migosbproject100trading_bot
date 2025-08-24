import requests
from bs4 import BeautifulSoup
import json
from telegram import Update
from telegram.ext import ContextTypes
from .db_manager import DBManager
from .ui_builder import UIManager

class NewsHandler:
    def __init__(self, db_manager: DBManager):
        self.db = db_manager
        self.ui = UIManager()
        self.news_categories = {
            "geopolitical": "Geopolitical Events",
            "central_bank": "Central Bank News (Fed, ECB)",
            "economic_data": "Inflation & Economic Data"
        }

    def scrape_forex_factory_calendar(self) -> List[Dict]:
        # This is a simplified scraper. A real one would need more robust error handling and parsing.
        headers = {'User-Agent': 'Mozilla/5.0'}
        url = "https://www.forexfactory.com/calendar"
        try:
            response = requests.get(url, headers=headers)
            soup = BeautifulSoup(response.content, 'lxml')
            # Logic to find high-impact (red folder) news events
            # This is complex and would require detailed parsing of the FF table structure
            # For now, returning a placeholder
            return [{"time": "14:30 GMT", "event": "US Core CPI", "impact": "High"}]
        except Exception as e:
            print(f"Error scraping Forex Factory: {e}")
            return []

    def scrape_reuters_news(self) -> List[Dict]:
        # Simplified scraper for Reuters Markets
        headers = {'User-Agent': 'Mozilla/5.0'}
        url = "https://www.reuters.com/markets/currencies/"
        news_list = []
        try:
            response = requests.get(url, headers=headers)
            soup = BeautifulSoup(response.content, 'lxml')
            # This selector is an example and will break if Reuters changes their site structure
            headlines = soup.find_all('a', {'data-testid': 'Heading'}, limit=10)
            for headline in headlines:
                title = headline.text
                link = "https://www.reuters.com" + headline['href']
                # Basic categorization logic
                category = "general"
                if any(keyword in title.lower() for keyword in ["fed", "ecb", "boj", "boe"]):
                    category = "central_bank"
                elif any(keyword in title.lower() for keyword in ["war", "conflict", "election"]):
                    category = "geopolitical"
                elif any(keyword in title.lower() for keyword in ["cpi", "inflation", "gdp", "jobs"]):
                    category = "economic_data"
                news_list.append({"title": title, "link": link, "category": category})
            return news_list
        except Exception as e:
            print(f"Error scraping Reuters: {e}")
            return []

    async def show_news_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        user_id = query.from_user.id
        await query.edit_message_text(
            "**Market News & Alerts**\n\n"
            "Select the real-time news categories you wish to subscribe to. The bot will automatically send you alerts for major breaking headlines in your chosen categories.",
            reply_markup=self.ui.get_news_menu_keyboard(user_id),
            parse_mode='Markdown'
        )

    async def toggle_news_subscription(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        user_id = query.from_user.id
        category_key = query.data.split('_')[-1]
        
        user_data = self.db.get_user(user_id)
        subscriptions = json.loads(user_data.get('news_subscriptions', '[]'))

        if category_key == 'all':
            if len(subscriptions) == len(self.news_categories):
                subscriptions = [] # Unsubscribe from all
            else:
                subscriptions = list(self.news_categories.keys()) # Subscribe to all
        else:
            if category_key in subscriptions:
                subscriptions.remove(category_key)
            else:
                subscriptions.append(category_key)
        
        self.db.update_news_subscriptions(user_id, subscriptions)
        await query.edit_message_text(
            "Your news subscriptions have been updated.",
            reply_markup=self.ui.get_news_menu_keyboard(user_id)
        )
