from pathlib import Path

import pandas as pd

from history_firestore import get_db

# ==================================================
# Folder
# ==================================================

BASE_DIR = Path(__file__).parent

CSV_FILE = BASE_DIR / "csv" / "history.csv"

COLLECTION = "history"

# ==================================================
# Load CSV
# ==================================================

if not CSV_FILE.exists():
    print("CSV not found!")
    raise SystemExit

df = pd.read_csv(
    CSV_FILE,
    dtype=str,
).fillna("")

print("=" * 60)
print("History Import")
print("=" * 60)
print("CSV :", CSV_FILE)
print("Rows:", len(df))
print("=" * 60)

# ==================================================
# Firestore
# ==================================================

db = get_db()
collection = db.collection(COLLECTION)

# ==================================================
# Import to Firestore
# ==================================================

count = 0

for _, row in df.iterrows():

    date = row["date"]

    data = {
        "date": row["date"],
        "status": row["status"],
        "am": row["am"],
        "pm": row["pm"],
    }

    collection.document(date).set(data)

    count += 1

    # Progress
    if count % 50 == 0:
        print(f"Imported : {count}/{len(df)}")

print()
print("=" * 60)
print("Import Finished")
print("=" * 60)
print("Imported :", count)
print("=" * 60)

# ==================================================
# Verify Firestore
# ==================================================

print()
print("=" * 60)
print("Verify")
print("=" * 60)

docs = collection.limit(5).stream()

for doc in docs:
    print(doc.id, "OK")

print("=" * 60)

# ==================================================
# Finish
# ==================================================

print()
print("History Import Finished")
print("Collection :", COLLECTION)
print("Imported   :", count)
print("Done.")