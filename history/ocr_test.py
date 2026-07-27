from pathlib import Path
import re
import cv2
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

# Test first 10 images
images = sorted(CELL_DIR.rglob("*.png"))[:10]

print("=" * 60)
print("OCR TEST")
print("=" * 60)

# ==================================================
# OCR Function
# ==================================================

def read_region(region, whitelist):

    gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)

    # Remove Noise
    gray = cv2.GaussianBlur(gray, (3, 3), 0)

    # Auto Threshold
    _, gray = cv2.threshold(
        gray,
        0,
        255,
        cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )

    # Enlarge Image
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

    # OCR: 1234 -> 34
    elif len(value) > 2:
        value = value[-2:]

    return value.zfill(2)

# ==================================================
# OCR TEST
# ==================================================

for image_path in images:

    img = cv2.imread(str(image_path))

    if img is None:
        continue

    h, w = img.shape[:2]

    # Morning Region
    morning = img[int(h * 0.18):int(h * 0.58), :]

    # Evening Region
    evening = img[int(h * 0.52):int(h * 0.90), :]

    # OCR
    am_raw = read_region(
        morning,
        "0123456789Off"
    )

    pm_raw = read_region(
        evening,
        "0123456789"
    )

    # OFF Day
    if am_raw == "" and pm_raw == "":
        status = "OFF"
        am = ""
        pm = ""
    else:
        status = "OPEN"
        am = normalize_number(am_raw)
        pm = normalize_number(pm_raw)

    print(image_path.name)
    print(f"Status  : {status}")
    print(f"Morning : {am}")
    print(f"Evening : {pm}")
    print("-" * 40)

print("=" * 60)
print("Finished")
print("=" * 60)