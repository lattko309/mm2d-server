from datetime import datetime
from pathlib import Path
import firebase_admin
from firebase_admin import credentials, firestore
import pandas as pd
import yfinance as yf

# Firebase Config
BASE_DIR = Path(__file__).resolve().parent
KEY_PATH = BASE_DIR.parent / "tools" / "serviceAccountKey.json"

if not firebase_admin._apps:
    if KEY_PATH.exists():
        cred = credentials.Certificate(str(KEY_PATH))
        firebase_admin.initialize_app(cred)
        db = firestore.client()
    else:
        db = None
else:
    db = firestore.client()


def calculate_2d(index: float, value: float) -> str:
    """SET Index နှင့် Value မှ 2D ကို မှန်ကန်စွာ တွက်ချက်ခြင်း"""
    if index <= 0 or value <= 0:
        return "--"
    index_str = f"{index:.2f}"
    index_digit = index_str.split(".")[1][-1]

    value_str = f"{value:.2f}"
    value_digit = str(int(value))[-1]

    return f"{index_digit}{value_digit}"


def get_real_data():
    print(
        "🚀 Thailand SET (^SET.BK) ၏ 2010 မှ ယနေ့အထိ Real Data များ ဆွဲယူနေပါသည်..."
    )

    # Yahoo Finance ၏ Official API မှ Real Market Data ရယူခြင်း
    ticker = yf.Ticker("^SET.BK")
    df_raw = ticker.history(
        start="2010-01-01", end=datetime.now().strftime("%Y-%m-%d")
    )

    if df_raw.empty:
        print("❌ Data မရရှိပါ။ Internet connection ကို စစ်ဆေးပါ။")
        return

    records = []
    saved_count = 0

    for date_idx, row in df_raw.iterrows():
        try:
            date_str = date_idx.strftime("%Y-%m-%d")
            set_index = round(float(row["Close"]), 2)
            set_value = round(float(row["Volume"]) * set_index / 1000, 2)

            if set_index <= 0 or set_value <= 0:
                continue

            result_2d = calculate_2d(set_index, set_value)

            record = {
                "date": date_str,
                "session": "16:30",
                "result": result_2d,
                "setIndex": set_index,
                "setValue": set_value,
                "year": date_idx.year,
                "month": date_idx.month,
                "dayNumber": date_idx.day,
            }
            records.append(record)

            # Firestore ထဲသို့ သွင်းယူခြင်း
            if db:
                doc_id = f"{date_str}-1630"
                db.collection("history").document(doc_id).set(
                    record, merge=True
                )

            saved_count += 1
        except Exception:
            continue

    # Excel ဖိုင်ထုတ်ပေးခြင်း
    df_res = pd.DataFrame(records)
    df_res.to_excel("Myanmar_2D_REAL_2010_2026.xlsx", index=False)
    print(
        f"🎉 စုစုပေါင်း Real Data ({saved_count}) ခုကို Firestore နှင့် Excel ထဲသို့ အောင်မြင်စွာ သိမ်းဆည်းပြီးပါပြီ!"
    )


if __name__ == "__main__":
    get_real_data()