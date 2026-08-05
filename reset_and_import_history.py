import csv
import os
import firebase_admin
from firebase_admin import credentials, firestore

# ==========================================
# 1. FIREBASE INIT
# ==========================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
KEY_PATH = os.path.join(BASE_DIR, "serviceAccountKey.json")

if not firebase_admin._apps:
    cred = credentials.Certificate(KEY_PATH)
    firebase_admin.initialize_app(cred)

db = firestore.client()
COLLECTION_NAME = "history"


# ==========================================
# 2. HELPER FUNCTIONS
# ==========================================
def format_2digit(val):
    """ဂဏန်း ၁ လုံးတည်းဖြစ်နေပါက ရှေ့တွင် '0' အလိုအလျောက်ဖြည့်ပေးခြင်း (ဥပမာ- 5 -> 05)"""
    if not val:
        return None
    val = str(val).strip()
    if not val or val == "--":
        return None
    if len(val) == 1 and val.isdigit():
        return f"0{val}"
    return val


def delete_collection(coll_ref, batch_size=100):
    """Collection ထဲမှ Data အဟောင်းများကို အကုန်ဖျက်ခြင်း"""
    docs = coll_ref.limit(batch_size).stream()
    deleted = 0

    for doc in docs:
        print(f"  🗑️ Deleting old doc: {doc.id}")
        doc.reference.delete()
        deleted += 1

    if deleted >= batch_size:
        return delete_collection(coll_ref, batch_size)


# ==========================================
# 3. RESET & IMPORT LOGIC
# ==========================================
def reset_and_import(csv_filename="data.csv"):
    csv_path = os.path.join(BASE_DIR, csv_filename)

    if not os.path.exists(csv_path):
        print(
            f"❌ Error: {csv_filename} ဖိုင်ကို ရှာမတွေ့ပါ။ server/ folder ထဲတွင် ရှိမရှိ စစ်ဆေးပါ။"
        )
        return

    # STEP 1: History Collection သန့်ရှင်းရေးလုပ်ခြင်း
    print(
        f"🔄 '{COLLECTION_NAME}' collection ထဲမှ Data အဟောင်းများကို စတင်ဖျက်နေပါသည်..."
    )
    coll_ref = db.collection(COLLECTION_NAME)
    delete_collection(coll_ref)
    print("✨ Data အဟောင်းများ အားလုံး ဖျက်ပြီးပါပြီ။\n")

    # STEP 2: CSV ဖတ်ယူပြီး Firestore သို့ ထည့်သွင်းခြင်း
    print(f"📥 '{csv_filename}' မှ Data များကို စတင်ထည့်သွင်းနေပါသည်...")
    count = 0

    with open(csv_path, mode="r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)

        for row in reader:
            date_str = row.get("date", "").strip()
            if not date_str:
                continue

            raw_status = row.get("status", "").strip().upper()
            m_val = format_2digit(row.get("morning"))
            e_val = format_2digit(row.get("evening"))

            # status က OFF ဟု ရေးထားလျှင် သို့မဟုတ် ဘာမှမရေးထားပါက (Blank) OFF ဟု သတ်မှတ်မည်
            if raw_status == "OFF" or not raw_status:
                status = "OFF"
                is_open = False
                morning = None
                evening = None
            else:
                status = "OPEN"
                is_open = True
                morning = m_val
                evening = e_val

            data = {
                "date": date_str,
                "status": status,
                "is_open": is_open,
                "morning": morning,
                "evening": evening,
                "updated_at": firestore.SERVER_TIMESTAMP,
            }

            # Firestore သို့ ထည့်သွင်းခြင်း
            db.collection(COLLECTION_NAME).document(date_str).set(data)

            m_text = morning if morning else "--"
            e_text = evening if evening else "--"
            print(
                f"  ✅ Added: [{date_str}] Status: {status} | M: {m_text} | E: {e_text}"
            )
            count += 1

    print(
        f"\n🎉 စုစုပေါင်း Data ({count}) ခုကို '{COLLECTION_NAME}' ထဲသို့ အောင်မြင်စွာ ထည့်သွင်းပြီးပါပြီ။"
    )


# ==========================================
# 4. EXECUTION
# ==========================================
if __name__ == "__main__":
    reset_and_import("data.csv")