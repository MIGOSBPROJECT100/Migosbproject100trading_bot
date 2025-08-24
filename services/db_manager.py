import sqlite3
import time
import json
from typing import Optional, Dict, Any, List

class DBManager:
    def __init__(self, db_name="data/migos_bot.db"):
        self.db_name = db_name
        self.conn = sqlite3.connect(self.db_name, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            telegram_name TEXT NOT NULL,
            registration_date INTEGER NOT NULL,
            account_status TEXT DEFAULT 'Free',
            meta_api_token TEXT,
            payment_approved BOOLEAN DEFAULT FALSE,
            last_feedback_time INTEGER DEFAULT 0,
            news_subscriptions TEXT
        )
        """)
        self.conn.commit()

    def add_user(self, user_id: int, telegram_name: str):
        self.cursor.execute(
            "INSERT OR IGNORE INTO users (user_id, telegram_name, registration_date, news_subscriptions) VALUES (?, ?, ?, ?)",
            (user_id, telegram_name, int(time.time()), json.dumps([]))
        )
        self.conn.commit()

    def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        self.cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        user_data = self.cursor.fetchone()
        return dict(user_data) if user_data else None

    def get_all_users(self) -> List[Dict[str, Any]]:
        self.cursor.execute("SELECT * FROM users")
        users = self.cursor.fetchall()
        return [dict(user) for user in users]

    def update_user_feedback_time(self, user_id: int):
        self.cursor.execute(
            "UPDATE users SET last_feedback_time = ? WHERE user_id = ?",
            (int(time.time()), user_id)
        )
        self.conn.commit()
        
    def update_user_account_token(self, user_id: int, token: str):
        self.cursor.execute(
            "UPDATE users SET meta_api_token = ?, account_status = 'Premium' WHERE user_id = ?",
            (token, user_id)
        )
        self.conn.commit()

    def update_news_subscriptions(self, user_id: int, subscriptions: List[str]):
        self.cursor.execute(
            "UPDATE users SET news_subscriptions = ? WHERE user_id = ?",
            (json.dumps(subscriptions), user_id)
        )
        self.conn.commit()

    def __del__(self):
        self.conn.close()
