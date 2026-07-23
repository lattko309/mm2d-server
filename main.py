import re
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from datetime import datetime
import pytz
from fastapi import FastAPI
from playwright.async_api import async_playwright
from pathlib import Path

# ===========================================
# FastAPI Config
# ===========================================

app = FastAPI(
    title="Myanmar 2D API Server",
    version="4.0.0"
)

# ===========================================
# Firebase
# ===========================================

# ===========================================
# Firebase
# ===========================================

BASE_DIR = Path(__file__).resolve().parent
KEY_PATH = BASE_DIR.parent / "tools" / "serviceAccountKey.json"

cred = credentials.Certificate(str(KEY_PATH))
firebase_admin.initialize_app(cred)

db = firestore.client()

TIMEZONE = pytz.timezone("Asia/Bangkok")
SET_URL = "https://www.set.or.th/en/market/index/set/overview"

# ===========================================
# Helper Functions
# ===========================================

def calculate_2d(index: float, value: float) -> str:
    index_last = f"{index:.2f}"[-1]
    value_last = f"{value:.2f}"[-1]
    return f"{index_last}{value_last}"


def market_status(now: datetime):
    # Saturday / Sunday
    if now.weekday() >= 5:
        return {
            "marketOpen": False,
            "session": None,
            "isFinal": False
        }

        # ===========================================
        # Firestore
        # ===========================================

        def save_live_result(data):

            db.collection("live").document("current").set(data)

            print("Firestore Updated")

    minutes = now.hour * 60 + now.minute

    # Morning Session
    if 570 <= minutes < 721:
        return {
            "marketOpen": True,
            "session": "12:01",
            "isFinal": False
        }

    # Morning Final
    if 721 <= minutes <= 725:
        return {
            "marketOpen": True,
            "session": "12:01",
            "isFinal": True
        }

    # Afternoon Session
    if 840 <= minutes < 990:
        return {
            "marketOpen": True,
            "session": "16:30",
            "isFinal": False
        }

    # Afternoon Final
    if 990 <= minutes <= 995:
        return {
            "marketOpen": True,
            "session": "16:30",
            "isFinal": True
        }

    return {
        "marketOpen": False,
        "session": None,
        "isFinal": False
    }

# ===========================================
# Firestore
# ===========================================

def save_live_result(data):

    db.collection("live").document("current").set(data)

    print("Firestore Updated")
# ===========================================
# Fetch SET Data
# ===========================================

async def fetch_set_data():
    async with async_playwright() as p:
        # Production Environment သို့ တင်သည့်အခါ headless=True ပြောင်းပေးပါ
        browser = await p.chromium.launch(headless=False)

        context = await browser.new_context(
            viewport={"width": 1600, "height": 900},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

        page = await context.new_page()

        try:
            await page.goto(
                SET_URL,
                wait_until="domcontentloaded",
                timeout=60000
            )

            # JavaScript Render စောင့်ခြင်း
            await page.wait_for_timeout(8000)

            # HTML & Screenshot သိမ်းဆည်းခြင်း
            content = await page.content()
            with open("set_page_live.html", "w", encoding="utf-8") as f:
                f.write(content)

            await page.screenshot(path="set_page_live.png", full_page=True)

            print("HTML Saved")
            print("Screenshot Saved")

            body = await page.locator("body").inner_text()

            # ===========================================
            # Parse SET Index & SET Trading Value
            # ===========================================

            set_index = 0.0
            set_value = 0.0

            # "SET Index" စတဲ့နေရာကစပြီး ရှာမယ်
            start = body.find("SET\nIndex")

            if start != -1:

                set_section = body[start:]

                # SET Index
                index_match = re.search(
                    r"SET\s+Index\s+([\d,]+\.\d{2})",
                    set_section,
                    re.MULTILINE
                )

                # Trading Value
                value_match = re.search(
                    r"Value\s+\(M\.Baht\)\s+([\d,]+\.\d{2})",
                    set_section,
                    re.MULTILINE
                )

                if index_match:
                    set_index = float(
                        index_match.group(1).replace(",", "")
                    )

                if value_match:
                    set_value = float(
                        value_match.group(1).replace(",", "")
                    )

            print("=================================")
            print("SET Index :", set_index)
            print("SET Value :", set_value)
            print("=================================")




            with open("body.txt", "w", encoding="utf-8") as f:
                f.write(body)

            print("body.txt saved")

            print("RETURNING:")
            print(set_index)
            print(set_value)

            return {
                "setIndex": set_index,
                "setValue": set_value,
                "source": "playwright_rendered_page"
            }

#             return {
#                 "setIndex": set_index,
#                 "setValue": set_value,
#                 "source": "playwright_rendered_page"
#             }

#             with open("body.txt", "w", encoding="utf-8") as f:
#                 f.write(body)
#
#             print("body.txt saved")
#
#             # SET Index နှင့် Value ကို Body Text မှ Regex ဖြင့် ရှာဖွေခြင်း (ဥပမာ Parsing)
#             # SET Text Structure ထဲမှ ကိန်းဂဏန်းထုတ်ယူသည့် Pattern
#             set_index = 0.0
#             set_value = 0.0
#
#             # "SET" စာသားနောက်မှ Value များကို ဖမ်းယူခြင်း
#             match = re.search(r"SET\s+([\d,]+\.\d{2})\s+.*?\s+([\d,]+\.\d{2})", body)
#             if match:
#                 set_index = float(match.group(1).replace(",", ""))
#                 set_value = float(match.group(2).replace(",", ""))
#
#             return {
#                 "setIndex": set_index,
#                 "setValue": set_value,
#                 "source": "playwright_rendered_page"
#             }

        finally:
            await context.close()
            await browser.close()

# ===========================================
# Routes
# ===========================================

@app.get("/")
def root():
    return {
        "status": "ok",
        "message": "Myanmar 2D API Server"
    }


@app.get("/api/health")
def health():
    return {
        "status": "healthy"
    }


@app.get("/api/2d-live")
async def live():
    now = datetime.now(TIMEZONE)
    status = market_status(now)

#     if not status["marketOpen"]:
#         return {
#             "status": "closed",
#             "message": "Market is currently closed",
#             "date": now.strftime("%Y-%m-%d"),
#             "serverTime": now.strftime("%H:%M:%S"),
#             "timezone": "Asia/Bangkok",
#             "marketOpen": False,
#             "session": None,
#             "result": "--",
#             "setIndex": 0.0,
#             "setValue": 0.0,
#             "isLive": False,
#             "isFinal": False,
#             "source": "none"
#         }

    try:
        market = await fetch_set_data()

        print(market)

        result = calculate_2d(
            market["setIndex"],
            market["setValue"]
        )

        response = {
            "status": "success",
            "date": now.strftime("%Y-%m-%d"),
            "serverTime": now.strftime("%H:%M:%S"),
            "timezone": "Asia/Bangkok",
            "marketOpen": True,
            "session": status["session"],
            "result": result,
            "setIndex": market["setIndex"],
            "setValue": market["setValue"],
            "isLive": not status["isFinal"],
            "isFinal": status["isFinal"],
            "source": market["source"]
        }

        save_live_result(response)

        return response

    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "date": now.strftime("%Y-%m-%d"),
            "serverTime": now.strftime("%H:%M:%S"),
            "timezone": "Asia/Bangkok",
            "marketOpen": status["marketOpen"],
            "session": status["session"],
            "result": "--",
            "setIndex": 0.0,
            "setValue": 0.0,
            "isLive": False,
            "isFinal": False,
            "source": "error"
        }