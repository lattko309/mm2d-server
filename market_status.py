import firebase_admin
from firebase_admin import credentials, firestore
from pathlib import Path
from datetime import datetime, time  # ⭐️ 'time' ကို ဤနေရာတွင် မဖြစ်မနေ import လုပ်ရပါမည်
from zoneinfo import ZoneInfo

# Timezones
MYANMAR_TIME = ZoneInfo("Asia/Yangon")
THAILAND_TIME = ZoneInfo("Asia/Bangkok")

# ===========================================
# Firebase Initialization
# ===========================================
BASE_DIR = Path(__file__).resolve().parent
KEY_PATH = BASE_DIR.parent / "tools" / "serviceAccountKey.json"

if not firebase_admin._apps:
    cred = credentials.Certificate(str(KEY_PATH))
    firebase_admin.initialize_app(cred)

db = firestore.client()


# ===========================================
# Market Status Function
# ===========================================
def get_market_status(data_history, now_mm: datetime, now_th: datetime):
    """
    Market Open/Close နှင့် Session အခြေအနေများကို စစ်ဆေးပေးသော Function
    """
    current_time = now_mm.time()

    # Morning Session (9:30 - 12:01)
    if time(9, 30) <= current_time <= time(12, 1):
        return {
            "is_open": True,
            "is_live": True,
            "is_official": (current_time >= time(12, 0)),
            "session": "12:01",
            "reason": "Morning market is open"
        }
    # Evening Session (14:00 - 16:30)
    elif time(14, 0) <= current_time <= time(16, 30):
        return {
            "is_open": True,
            "is_live": True,
            "is_official": (current_time >= time(16, 29)),
            "session": "16:30",
            "reason": "Evening market is open"
        }
    else:
        return {
            "is_open": False,
            "is_live": False,
            "is_official": False,
            "session": "CLOSED",
            "reason": "Market is closed"
        }