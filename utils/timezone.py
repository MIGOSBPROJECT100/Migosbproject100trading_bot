from datetime import datetime
import pytz

def now_tz(tz_name: str):
    tz = pytz.timezone(tz_name)
    return datetime.now(tz)

def to_tz(dt: datetime, tz_name: str):
    tz = pytz.timezone(tz_name)
    return dt.astimezone(tz)
