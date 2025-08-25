from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
from sqlalchemy import create_engine, Integer, String, Boolean, DateTime, JSON, Text
from datetime import datetime
from config.settings import DB_URL

class Base(DeclarativeBase): pass

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False)  # Telegram ID
    username: Mapped[str] = mapped_column(String(64), default="")
    is_premium: Mapped[bool] = mapped_column(Boolean, default=False)
    mt_token: Mapped[str] = mapped_column(Text, default="")   # MetaApi token per user (optional)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    feedback_cooldown_until: Mapped[datetime|None] = mapped_column(DateTime, nullable=True)
    news_prefs: Mapped[dict] = mapped_column(JSON, default=lambda: {
        "geopolitics": False, "central_banks": False, "inflation": False, "all": False
    })

class SignalLog(Base):
    __tablename__ = "signals"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    symbol: Mapped[str] = mapped_column(String(32))
    direction: Mapped[str] = mapped_column(String(4))  # BUY/SELL
    tp1: Mapped[float] = mapped_column()
    tp2: Mapped[float] = mapped_column()
    tp3: Mapped[float] = mapped_column()
    sl: Mapped[float] = mapped_column()
    sent_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class NewsLock(Base):
    __tablename__ = "news_lock"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    active: Mapped[bool] = mapped_column(Boolean, default=False)
    reason: Mapped[str] = mapped_column(String(255), default="")

engine = create_engine(DB_URL, echo=False, future=True)
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(engine, expire_on_commit=False)
