import os
import json
import re
from datetime import datetime
from zoneinfo import ZoneInfo
import firebase_admin
from firebase_admin import credentials, firestore
from playwright.sync_api import sync_playwright

# ----------------------------------------------------
# Firebase Credentials (Cloud Environment & Local Support)
# ----------------------------------------------------
if not firebase_admin._apps:
    # Cloud (GitHub Actions) တွင် Environment Variable မှယူမည်
    if "SERVICE_ACCOUNT_KEY" in os.environ:
        cred_json = json.loads(os.environ["SERVICE_ACCOUNT_KEY"])
        cred = credentials.Certificate(cred_json)
    else:
        # Local PC တွင် File မှယူမည်
        cred = credentials.Certificate("../tools/serviceAccountKey.json")

    firebase_admin.initialize_app(cred)

db = firestore.client()
TIMEZONE = ZoneInfo("Asia/Yangon")
SET_URL = "https://www.set.or.th/en/market/index/set/overview"

def calculate_2d(index: float, value: float) -> str:
    if index <= 0 or value <= 0:
        return "--"
    index_str = f"{index:.2f}"
    index_digit = index_str.split(".")[1][-1]
    value_str = f"{value:.2f}"
    value_digit = value_str.split(".")[0][-1]
    return f"{index_digit}{value_digit}"

def run_auto_fetch():
    now = datetime.now(TIMEZONE)
    date_str = now.strftime("%Y-%m-%d")

    # စနေ/တနင်္ဂနွေ ဖြစ်ပါက ကျော်မည်
    if now.weekday() >= 5:
        print("Weekend - Market Closed")
        return

    sessions_to_check = []
    minutes = now.hour * 60 + now.minute

    # 12:01 ကျော်ပါက 12:01 ကို စစ်မည်
    if minutes >= 721:
        sessions_to_check.append("12:01")
    # 16:30 ကျော်ပါက 16:30 ကိုပါ စစ်မည်
    if minutes >= 990:
        sessions_to_check.append("16:30")

    missing_sessions = []
    for s in sessions_to_check:
        doc_id = f"{date_str}-{s.replace(':', '')}"
        doc = db.collection("history").document(doc_id).get()
        if not doc.exists:
            missing_sessions.append(s)

    if not missing_sessions:
        print(f"✅ {date_str} အတွက် Result (12:01 / 16:30) ရှိပြီးသား ဖြစ်ပါသည်။")
        return

    print(f"⚠️ Missing Sessions: {missing_sessions} -> Fetching SET Website...")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        try:
            page.goto(SET_URL, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(3000)
            body_text = page.locator("body").inner_text()

            set_index = 0.0
            set_value = 0.0

            m_idx = re.search(r"(?:SET|Last)\s*[\r\n\s]*([\d,]+\.\d{2})", body_text, re.IGNORECASE)
            if m_idx:
                set_index = float(m_idx.group(1).replace(",", ""))

            m_val = re.search(r"Value\s*(?:\(M\.Baht\))?\s*[\r\n\s:]*([\d,]+\.\d{2})", body_text, re.IGNORECASE)
            if m_val:
                set_value = float(m_val.group(1).replace(",", ""))

            result_2d = calculate_2d(set_index, set_value)

            for session in missing_sessions:
                doc_id = f"{date_str}-{session.replace(':', '')}"
                payload = {
                    "date": date_str,
                    "session": session,
                    "result": result_2d,
                    "setIndex": set_index,
                    "setValue": set_value,
                    "year": now.year,
                    "month": now.month,
                    "day": now.day,
                    "updatedAt": now.strftime("%H:%M:%S")
                }

                # Firestore History နှင့် Today ထဲ သိမ်းမည်
                db.collection("history").document(doc_id).set(payload)
                db.collection("today").document(session).set(payload)

                print(f"🎉 Saved successfully -> DocID: {doc_id} | Result: {result_2d}")

        except Exception as e:
            print(f"❌ Error: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    run_auto_fetch()