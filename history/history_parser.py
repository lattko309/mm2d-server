from pathlib import Path
import re

import cv2
import pandas as pd
import pytesseract

# ==================================================
# Tesseract
# ==================================================

pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)

# ==================================================
# Folder
# ==================================================

BASE_DIR = Path(__file__).parent

CELL_DIR = BASE_DIR / "cells"
CSV_DIR = BASE_DIR / "csv"

CSV_DIR.mkdir(exist_ok=True)

# ==================================================
# OCR
# ==================================================

def read_region(region, whitelist):

    gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)

    gray = cv2.GaussianBlur(gray, (3, 3), 0)

    _, gray = cv2.threshold(
        gray,
        0,
        255,
        cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )

    gray = cv2.resize(
        gray,
        None,
        fx=4,
        fy=4,
        interpolation=cv2.INTER_CUBIC
    )

    text = pytesseract.image_to_string(
        gray,
        config=f"--psm 8 -c tessedit_char_whitelist={whitelist}"
    )

    return text.strip()

# ==================================================
# Normalize Number
# ==================================================

def normalize_number(text):

    nums = re.findall(r"\d+", text)

    if not nums:
        return ""

    value = nums[0]

    # OCR: 220 -> 22
    if len(value) == 3 and value.endswith("0"):
        value = value[:2]

    elif len(value) > 2:
        value = value[-2:]

    return value.zfill(2)

# ==================================================
# Parse One Image
# ==================================================

def parse_image(image_path):

    img = cv2.imread(str(image_path))

    if img is None:
        return None

    h, w = img.shape[:2]

    morning = img[int(h * 0.18):int(h * 0.58), :]
    evening = img[int(h * 0.52):int(h * 0.90), :]

    am_raw = read_region(
        morning,
        "0123456789Off"
    )

    pm_raw = read_region(
        evening,
        "0123456789"
    )

    if am_raw == "" and pm_raw == "":
        return {
            "date": image_path.stem,
            "status": "OFF",
            "am": "",
            "pm": ""
        }

    return {
        "date": image_path.stem,
        "status": "OPEN",
        "am": normalize_number(am_raw),
        "pm": normalize_number(pm_raw),
    }
# ==================================================
# Load Images
# ==================================================

images = []

for year_dir in sorted(CELL_DIR.iterdir()):

    if not year_dir.is_dir():
        continue

    # Skip detected/, preview.png, etc.
    if not year_dir.name.isdigit():
        continue

    images.extend(sorted(year_dir.rglob("*.png")))

print("=" * 60)
print("History Parser")
print("=" * 60)
print("Images :", len(images))
print("=" * 60)

# ==================================================
# Parse Images
# ==================================================

rows = []

for image_path in images:

    print("Reading :", image_path.name)

    result = parse_image(image_path)

    if result is None:
        continue

    rows.append(result)

print()
print("=" * 60)
print("Parsed :", len(rows))
print("=" * 60)

# ==================================================
# DataFrame
# ==================================================

df = pd.DataFrame(rows)

# Sort by Date
df = df.sort_values("date")

# Remove Duplicate Date (Keep First)
df = df.drop_duplicates(
    subset=["date"],
    keep="first"
)

print()
print("Unique Dates :", len(df))
print("=" * 60)

# ==================================================
# Save CSV
# ==================================================

csv_file = CSV_DIR / "history.csv"

df.to_csv(
    csv_file,
    index=False,
    encoding="utf-8-sig"
)

# ==================================================
# Summary
# ==================================================

open_count = (df["status"] == "OPEN").sum()
off_count = (df["status"] == "OFF").sum()

print()
print("=" * 60)
print("History Parser Finished")
print("=" * 60)
print("CSV File :", csv_file)
print("Total    :", len(df))
print("OPEN     :", open_count)
print("OFF      :", off_count)
print("=" * 60)

print()
print("First 10 Rows")
print("=" * 60)
print(df.head(10))

print()
print("Last 10 Rows")
print("=" * 60)
print(df.tail(10))

print()
print("Done.")