from datetime import datetime
import numpy as np
import pandas as pd

# 2010 မှ 2026 အထိ ရက်စွဲများ သတ်မှတ်ခြင်း (စနေ/တနင်္ဂနွေ မှလွဲ၍)
dates = pd.date_range(start="2010-01-04", end="2026-07-24", freq="B")

records = []
np.random.seed(42)

for d in dates:
    date_str = d.strftime("%Y-%m-%d")
    year = d.year

    # နှစ်အလိုက် SET Index အတက်အကျ ပုံစံတွက်ချက်ခြင်း
    base_index = 700 + (year - 2010) * 58 + np.random.uniform(-25, 25)

    # မနက်ပိုင်း ၁၂:၀၁ Session
    idx_1201 = round(base_index + np.random.uniform(-4, 4), 2)
    val_1201 = round(np.random.uniform(22000, 48000), 2)
    res_1201 = f"{f'{idx_1201:.2f}'[-1]}{f'{val_1201:.2f}'.split('.')[0][-1]}"

    records.append(
        {
            "Date": date_str,
            "Session": "12:01",
            "2D Result": res_1201,
            "SET Index": idx_1201,
            "SET Value": val_1201,
            "Year": year,
        }
    )

    # ညနေပိုင်း ၁၆:၃၀ Session
    idx_1630 = round(base_index + np.random.uniform(-7, 7), 2)
    val_1630 = round(np.random.uniform(50000, 92000), 2)
    res_1630 = f"{f'{idx_1630:.2f}'[-1]}{f'{val_1630:.2f}'.split('.')[0][-1]}"

    records.append(
        {
            "Date": date_str,
            "Session": "16:30",
            "2D Result": res_1630,
            "SET Index": idx_1630,
            "SET Value": val_1630,
            "Year": year,
        }
    )

# Excel သို့ ထုတ်ယူခြင်း
df = pd.DataFrame(records)
filename = "Myanmar_2D_History_2010_2026.xlsx"
df.to_excel(filename, index=False)

print(f"✅ Excel file generated successfully: {filename}")