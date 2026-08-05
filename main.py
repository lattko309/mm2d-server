import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timezone, timedelta
from fastapi import FastAPI
import firebase_admin
from firebase_admin import credentials, firestore
import httpx

# --- 1. FIREBASE INITIALIZATION ---
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

SESSION_TIME_TO_SUFFIX = {
    "11:00:00": "1100",
    "12:01:00": "1201",
    "15:00:00": "1500",
    "16:30:00": "1630",
}

MORNING_FINAL_TIME = "12:01:00"
EVENING_FINAL_TIME = "16:30:00"


def check_market_status():
    utc_now = datetime.now(timezone.utc)
    mm_time = utc_now + timedelta(hours=6, minutes=30)

    if mm_time.weekday() >= 5:
        return "CLOSED", "Weekend Holiday"

    current_seconds = mm_time.hour * 3600 + mm_time.minute * 60 + mm_time.second

    is_morning = (9 * 3600 + 30 * 60) <= current_seconds <= (12 * 3600 + 1 * 60)
    is_evening = (14 * 3600) <= current_seconds <= (16 * 3600 + 30 * 60)

    if is_morning or is_evening:
        return "LIVE", ""
    else:
        return "CLOSED", "Outside Trading Hours"


def _parse_number(value_str: str) -> float:
    try:
        return float(str(value_str).replace(",", "").strip())
    except (ValueError, TypeError):
        return 0.0


async def fetch_thaistock2d_live(client: httpx.AsyncClient) -> dict:
    response = await client.get("https://api.thaistock2d.com/live", timeout=10.0)
    response.raise_for_status()
    return response.json()


def _write_history_if_final(current_date_str: str, api_data: dict):
    results = api_data.get("result", [])
    for item in results:
        open_time = item.get("open_time")
        if open_time not in (MORNING_FINAL_TIME, EVENING_FINAL_TIME):
            continue

        suffix = SESSION_TIME_TO_SUFFIX.get(open_time)
        if not suffix:
            continue

        # ⭐ FIX: API ရဲ့ "result" array ထဲမှာ open_time ကိုက်ညီပေမယ့်
        # session က တကယ် confirm မဖြစ်သေးရင် (history_id == null
        # ဒါမှမဟုတ် twod == "--") history ထဲကို write မလုပ်ရအောင်
        # skip လုပ်ရန် (မဟုတ်ရင် setIndex:0/setValue:0/result:"--"
        # ဆိုတဲ့ placeholder document တွေ အစောကြီး ဝင်လာနိုင်သည်)
        twod_value = item.get("twod")
        history_id = item.get("history_id")
        is_confirmed = (
            history_id is not None
            and twod_value is not None
            and str(twod_value).strip() != "--"
        )
        if not is_confirmed:
            continue

        doc_id = f"{current_date_str}-{suffix}"
        session_label = "morning" if open_time == MORNING_FINAL_TIME else "evening"

        history_doc = {
            "date": current_date_str,
            "session": open_time,
            "sessionLabel": session_label,
            "result": twod_value,
            "setIndex": _parse_number(item.get("set")),
            "setValue": _parse_number(item.get("value")),
            "updatedAt": firestore.SERVER_TIMESTAMP,
        }

        db.collection("history").document(doc_id).set(history_doc, merge=True)


async def background_fetcher():
    print("🚀 Real Data Background Fetcher Started (thaistock2d.com)")

    consecutive_errors = 0

    async with httpx.AsyncClient(headers={"User-Agent": "Mozilla/5.0"}) as client:
        while True:
            try:
                mode, reason = check_market_status()

                mm_now = datetime.now(timezone.utc) + timedelta(hours=6, minutes=30)
                current_date_str = mm_now.strftime("%Y-%m-%d")

                if mode == "CLOSED":
                    print(f"💤 Market is CLOSED ({reason}).")
                    closed_data = {
                        "date": current_date_str,
                        "mode": "CLOSED",
                        "reason": reason,
                        "serverTime": mm_now.strftime("%H:%M:%S"),
                        "updatedAt": firestore.SERVER_TIMESTAMP,
                    }
                    db.collection("live").document("current").set(closed_data, merge=True)

                    # ⭐ FIX: CLOSED ဖြစ်နေရင်တောင် history ကို ဆက် check လုပ်ရန်လိုသည်
                    # (LIVE window ရဲ့ boundary time (12:01:00 / 16:30:00) အတိအကျမှာ
                    #  API ဘက်က confirmed result မထွက်သေးရင် history document က
                    #  ထာဝရ ကျန်ရစ်ခဲ့နိုင်လို့ CLOSED အချိန်မှာလည်း စစ်ပေးရန် လိုအပ်ပါသည်)
                    try:
                        api_data_check = await fetch_thaistock2d_live(client)
                        _write_history_if_final(current_date_str, api_data_check)
                    except Exception as backfill_err:
                        print(f"⚠️ Backfill check failed while CLOSED: {backfill_err}")

                    await asyncio.sleep(300)
                    continue

                api_data = await fetch_thaistock2d_live(client)
                consecutive_errors = 0

                live_info = api_data.get("live", {})
                real_set_index = _parse_number(live_info.get("set"))
                real_set_value = _parse_number(live_info.get("value"))
                calculated_result = live_info.get("twod", "--")

                live_data = {
                    "date": current_date_str,
                    "result": calculated_result,
                    "setIndex": real_set_index,
                    "setValue": real_set_value,
                    "mode": "LIVE",
                    "reason": "",
                    "serverTime": mm_now.strftime("%H:%M:%S"),
                    "sourceTime": live_info.get("time", ""),
                    "updatedAt": firestore.SERVER_TIMESTAMP,
                }

                db.collection("live").document("current").set(live_data, merge=True)
                print(f"📊 Live updated: set={real_set_index} value={real_set_value} twod={calculated_result}")

                _write_history_if_final(current_date_str, api_data)

            except httpx.HTTPError as fetch_err:
                consecutive_errors += 1
                print(f"⚠️ Failed to fetch thaistock2d API (attempt {consecutive_errors}): {fetch_err}")
            except Exception as e:
                consecutive_errors += 1
                print(f"⚠️ Error in background task (attempt {consecutive_errors}): {e}")

            if consecutive_errors >= 5:
                print("🚨 5+ consecutive failures — check network / API status / serviceAccountKey.")

            await asyncio.sleep(10)


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(background_fetcher())
    yield
    task.cancel()


app = FastAPI(lifespan=lifespan)


@app.get("/")
def read_root():
    mode, reason = check_market_status()
    mm_now = datetime.now(timezone.utc) + timedelta(hours=6, minutes=30)
    return {
        "status": "Server is running smoothly",
        "market_mode": mode,
        "reason": reason,
        "current_date": mm_now.strftime("%Y-%m-%d"),
        "current_time_mmt": mm_now.strftime("%H:%M:%S"),
    }