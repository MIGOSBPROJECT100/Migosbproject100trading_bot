import os, sqlite3, threading
from typing import Optional, List, Tuple, Dict
from services.logger import get_logger

logger = get_logger("db")

DB_PATH = os.path.join(os.getcwd(), "data", "bot.db")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

_lock = threading.Lock()

def _connect():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

# Initialize schema
def init_db():
    with _lock:
        conn = _connect()
        cur = conn.cursor()
        cur.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            full_name TEXT,
            tier TEXT DEFAULT 'free',
            registered_at TEXT,
            premium_approved INTEGER DEFAULT 0,
            metaapi_token TEXT,
            news_geo INTEGER DEFAULT 0,
            news_cb INTEGER DEFAULT 0,
            news_cpi INTEGER DEFAULT 0,
            free_signal_date TEXT,
            feedback_last_ts INTEGER DEFAULT 0,
            daily_loss_count INTEGER DEFAULT 0,
            cooldown_until TEXT
        );
        CREATE TABLE IF NOT EXISTS alerts (
            user_id INTEGER,
            instrument TEXT,
            enabled INTEGER DEFAULT 0,
            PRIMARY KEY(user_id, instrument)
        );
        CREATE TABLE IF NOT EXISTS payments (
            user_id INTEGER,
            method TEXT,
            screenshot_file_id TEXT,
            approved INTEGER DEFAULT 0,
            created_at TEXT
        );
        CREATE TABLE IF NOT EXISTS signals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            instrument TEXT,
            direction TEXT,
            entry REAL, tp1 REAL, tp2 REAL, tp3 REAL, sl REAL,
            created_at TEXT,
            sent_to_user INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_login TEXT,
            instrument TEXT,
            open_time TEXT,
            close_time TEXT,
            profit REAL,
            result TEXT
        );
        """)
        conn.commit()
        conn.close()
        logger.info("Database initialized at %s", DB_PATH)

def upsert_user(user_id: int, username: str, full_name: str):
    with _lock:
        conn = _connect()
        cur = conn.cursor()
        cur.execute("""
        INSERT INTO users(user_id, username, full_name, registered_at)
        VALUES (?, ?, ?, datetime('now'))
        ON CONFLICT(user_id) DO UPDATE SET username=excluded.username, full_name=excluded.full_name
        """, (user_id, username, full_name))
        conn.commit()
        conn.close()

def set_user_tier(user_id: int, tier: str, approved: int = 0):
    with _lock:
        conn = _connect()
        conn.execute("UPDATE users SET tier=?, premium_approved=? WHERE user_id=?", (tier, approved, user_id))
        conn.commit(); conn.close()

def set_user_news_prefs(user_id: int, geo: int=None, cb: int=None, cpi: int=None):
    with _lock:
        conn = _connect()
        if geo is not None:
            conn.execute("UPDATE users SET news_geo=? WHERE user_id=?", (geo, user_id))
        if cb is not None:
            conn.execute("UPDATE users SET news_cb=? WHERE user_id=?", (cb, user_id))
        if cpi is not None:
            conn.execute("UPDATE users SET news_cpi=? WHERE user_id=?", (cpi, user_id))
        conn.commit(); conn.close()

def get_user(user_id: int) -> Optional[sqlite3.Row]:
    with _lock:
        conn = _connect()
        cur = conn.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
        row = cur.fetchone(); conn.close()
        return row

def list_users() -> List[sqlite3.Row]:
    with _lock:
        conn = _connect()
        rows = conn.execute("SELECT * FROM users ORDER BY registered_at DESC").fetchall()
        conn.close(); return rows

def toggle_alert(user_id: int, instrument: str) -> bool:
    with _lock:
        conn = _connect()
        cur = conn.execute("SELECT enabled FROM alerts WHERE user_id=? AND instrument=?", (user_id, instrument))
        row = cur.fetchone()
        if row:
            new_val = 0 if row["enabled"] else 1
            conn.execute("UPDATE alerts SET enabled=? WHERE user_id=? AND instrument=?", (new_val, user_id, instrument))
        else:
            new_val = 1
            conn.execute("INSERT INTO alerts(user_id, instrument, enabled) VALUES (?, ?, 1)", (user_id, instrument))
        conn.commit(); conn.close()
        return bool(new_val)

def alert_enabled(user_id: int, instrument: str) -> bool:
    with _lock:
        conn = _connect()
        row = conn.execute("SELECT enabled FROM alerts WHERE user_id=? AND instrument=?", (user_id, instrument)).fetchone()
        conn.close()
        return bool(row["enabled"]) if row else False

def mark_feedback_ts(user_id: int, ts: int):
    with _lock:
        conn = _connect()
        conn.execute("UPDATE users SET feedback_last_ts=? WHERE user_id=?", (ts, user_id))
        conn.commit(); conn.close()

def set_free_signal_date(user_id: int, day_str: str):
    with _lock:
        conn = _connect()
        conn.execute("UPDATE users SET free_signal_date=? WHERE user_id=?", (day_str, user_id))
        conn.commit(); conn.close()

def set_cooldown(user_id: int, until_iso: str):
    with _lock:
        conn = _connect()
        conn.execute("UPDATE users SET cooldown_until=?, daily_loss_count=0 WHERE user_id=?", (until_iso, user_id))
        conn.commit(); conn.close()

def inc_daily_loss(user_id: int) -> int:
    with _lock:
        conn = _connect()
        row = conn.execute("SELECT daily_loss_count FROM users WHERE user_id=?", (user_id,)).fetchone()
        count = (row["daily_loss_count"] if row else 0) + 1
        conn.execute("UPDATE users SET daily_loss_count=? WHERE user_id=?", (count, user_id))
        conn.commit(); conn.close()
        return count
