from db.models import SessionLocal, User
from datetime import datetime, timedelta
from utils.constants import FEEDBACK_COOLDOWN_SECONDS

def get_or_create_user(uid:int, username:str=""):
    with SessionLocal() as s:
        u = s.get(User, uid)
        if not u:
            u = User(id=uid, username=username or "")
            s.add(u); s.commit()
        return u

def set_feedback_cooldown(uid:int):
    with SessionLocal() as s:
        u = s.get(User, uid)
        if not u: return
        u.feedback_cooldown_until = datetime.utcnow() + timedelta(seconds=FEEDBACK_COOLDOWN_SECONDS)
        s.add(u); s.commit()

def feedback_allowed(uid:int)->bool:
    with SessionLocal() as s:
        u = s.get(User, uid)
        if not u or not u.feedback_cooldown_until:
            return True
        return datetime.utcnow() >= u.feedback_cooldown_until
