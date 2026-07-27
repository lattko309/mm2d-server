import asyncio
from datetime import datetime
from contextlib import asynccontextmanager
from pathlib import Path
import re
import traceback
from zoneinfo import ZoneInfo

import firebase_admin
from fastapi import FastAPI
from firebase_admin import credentials, firestore
from playwright.async_api import async_playwright

# ===========================================
# Firebase Config
# ===========================================

BASE_DIR = Path(__file__).resolve().parent
KEY_PATH = BASE_DIR.parent / "tools" / "serviceAccountKey.json"

if not firebase_admin._apps:
    cred = credentials.Certificate(str(KEY_PATH))
    firebase_admin.initialize_app(cred)

db = firestore.client()

TIMEZONE = ZoneInfo("Asia/Yangon")
SET_URL = "https://www.set.or.th/en/market/index/set/overview"

# History သိမ်းပြီးသား Session များကို ခေတ္တမှတ်ထားရန် In-Memory Cache
saved_history_keys = set()


# ===========================================
# Helper Functions
# ===========================================


def calculate_2d(index: float, value: float) -> str:
    if index <= 0 or value <= 0:
        return "--"

    index_str = f"{index:.2f}"
    index_digit = index_str.split(".")[1][-1]

    value_str = f"{value:.2f}"
    value_digit = value_str.split(".")[0][-1]

    return f"{index_digit}{value_digit}"


def market_status(now: datetime):
    if now.weekday() >= 5:
        return {"marketOpen": False, "session": None, "isFinal": False}

    minutes = now.hour * 60 + now.minute

    if 570 <= minutes < 721:
        return {"marketOpen": True, "session": "LIVE-AM", "isFinal": False}
    if 721 <= minutes < 780:
        return {"marketOpen": True, "session": "12:01", "isFinal": True}
    if 780 <= minutes < 990:
        return {"marketOpen": True, "session": "LIVE-PM", "isFinal": False}
    if 990 <= minutes <= 995:
        return {"marketOpen": True, "session": "16:30", "isFinal": True}

    return {"marketOpen": False, "session": None, "isFinal": False}


# ===========================================
# Firestore Functions
# ===========================================


def save_live_result(data: dict):
    try:
        doc_ref = db.collection("live").document("current")
        doc_ref.set(data)
        print(
            f"[{datetime.now().strftime('%H:%M:%S')}] ⚡ Live Updated -> 2D: {data['result']} | SET: {data['setIndex']} | Val: {data['setValue']}"
        )
    except Exception as e:
        print("Firestore Live Save Error:", e)


def save_today_result(data: dict):
    try:
        session = data.get("session")
        if not session or not data.get("isFinal"):
            return

        doc_ref = db.collection("today").document(session)
        doc_ref.set({
            "result": data["result"],
            "setIndex": data["setIndex"],
            "setValue": data["setValue"],
            "updatedAt": data["serverTime"],
        })
    except Exception as e:
        print("Today Save Error:", e)


def save_history_result(data: dict):
    """Optimized History Save: Firestore Read ကို ၁ ကြိမ်သာ ပြုလုပ်မည်"""
    try:
        session = data.get("session")
        if session not in ["12:01", "16:30"] or data["result"] == "--":
            return

        doc_id = f'{data["date"]}-{session.replace(":", "")}'

        # ① Memory Cache ထဲတွင် ရှိနေပါက Firestore Read/Write ကို လုံးဝ မလုပ်ပါ
        if doc_id in saved_history_keys:
            return

        doc_ref = db.collection("history").document(doc_id)

        # Firestore ထဲတွင် ရှိပြီးသားလား ၁ ကြိမ်သာ စစ်ဆေးမည်
        if doc_ref.get().exists:
            saved_history_keys.add(doc_id)  # Memory တွင် မှတ်ထားမည်
            return

        doc_ref.set({
            "date": data["date"],
            "session": session,
            "result": data["result"],
            "setIndex": data["setIndex"],
            "setValue": data["setValue"],
            "year": int(data["date"][:4]),
            "month": int(data["date"][5:7]),
            "day": int(data["date"][8:10]),
            "updatedAt": data["serverTime"],
        })

        saved_history_keys.add(doc_id)
        print(f"📜 [OPTIMIZED] History Saved Successfully -> DocID: {doc_id}")

    except Exception as e:
        print("History Save Error:", e)


# ===========================================
# High-Speed Background Fetch Loop
# ===========================================


async def background_fetch_loop():
    print("🚀 High-Speed & Resilient Background Fetcher Started")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1600, "height": 900},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        )
        page = await context.new_page()

        # Initial Page Load
        try:
            await page.goto(
                SET_URL, wait_until="domcontentloaded", timeout=30000
            )
            await page.wait_for_timeout(2000)
        except Exception as e:
            print("Initial Page Load Error:", e)

        while True:
            loop_start = asyncio.get_event_loop().time()
            now = datetime.now(TIMEZONE)
            status = market_status(now)

            try:
                # ② Reload Fail ဖြစ်ပါက goto() ဖြင့် Re-connect လုပ်ပေးသော Logic
                try:
                    await page.reload(
                        wait_until="domcontentloaded", timeout=10000
                    )
                except Exception as reload_err:
                    print(
                        f"⚠️ Reload failed ({reload_err}), attempting page.goto()..."
                    )
                    await page.goto(
                        SET_URL, wait_until="domcontentloaded", timeout=20000
                    )

                body_text = await page.locator("body").inner_text()

                set_index = 0.0
                set_value = 0.0

                # SET Index 解析
                patterns = [
                    r"SET\s+([\d,]+\.\d{2})",
                    r"Last\s+([\d,]+\.\d{2})",
                    r"Index\s+([\d,]+\.\d{2})",
                    r"(1\d{3}\.\d{2})",
                ]
                for pat in patterns:
                    m = re.search(pat, body_text, re.IGNORECASE)
                    if m:
                        val = float(m.group(1).replace(",", ""))
                        if 1000.0 <= val <= 3000.0:
                            set_index = val
                            break

                # SET Value 解析
                val_match = re.search(
                    r"Value\s*(?:\(M\.Baht\))?\s*[\r\n\s:]*([\d,]+\.\d{2})",
                    body_text,
                    re.IGNORECASE,
                )
                if val_match:
                    set_value = float(val_match.group(1).replace(",", ""))

                result = calculate_2d(set_index, set_value)

                mode = (
                    "CLOSED"
                    if not status["marketOpen"]
                    else ("OFFICIAL" if status["isFinal"] else "LIVE")
                )

                payload = {
                    "status": "success",
                    "date": now.strftime("%Y-%m-%d"),
                    "serverTime": now.strftime("%H:%M:%S"),
                    "timezone": "Asia/Yangon",
                    "marketOpen": status["marketOpen"],
                    "session": status["session"],
                    "mode": mode,
                    "result": result,
                    "setIndex": set_index,
                    "setValue": set_value,
                    "isLive": not status["isFinal"],
                    "isFinal": status["isFinal"],
                    "source": "playwright_rendered_page",
                }

                save_live_result(payload)

                if status["isFinal"]:
                    save_today_result(payload)
                    save_history_result(payload)

            except Exception as e:
                print("Fetch Loop Iteration Error:", e)

            # ၅ စက္ကန့် ပုံမှန် ပတ်စေရန် Calculation
            elapsed = asyncio.get_event_loop().time() - loop_start
            sleep_time = max(0.2, 2.0 - elapsed)
            await asyncio.sleep(sleep_time)


# ===========================================
# FastAPI Lifespan & Routes
# ===========================================


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(background_fetch_loop())
    yield
    task.cancel()


app = FastAPI(title="Myanmar 2D API Server", version="4.0.0", lifespan=lifespan)


@app.get("/")
def root():
    return {"status": "ok", "message": "Myanmar 2D API Server"}


@app.get("/api/health")
def health():
    return {"status": "healthy"}


@app.get("/api/2d-live")
async def live():
    try:
        doc = db.collection("live").document("current").get()
        if doc.exists:
            return doc.to_dict()
        else:
            return {"status": "error", "message": "No live data available yet."}
    except Exception as e:
        return {"status": "error", "message": str(e)}