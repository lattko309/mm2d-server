import os
import re
import tempfile
import zipfile
import cv2
import firebase_admin
from firebase_admin import credentials, firestore
import numpy as np
import pytesseract

# ==========================================
# 1. CONFIG & FLAGS
# ==========================================
pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)
DEBUG_GRID = True  # Set True to output debug_grid.png

# ==========================================
# 2. FIREBASE INIT
# ==========================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
KEY_PATH = os.path.join(BASE_DIR, "serviceAccountKey.json")

if not firebase_admin._apps:
    cred = credentials.Certificate(KEY_PATH)
    firebase_admin.initialize_app(cred)

db = firestore.client()

DEBUG_DIR = os.path.join(BASE_DIR, "debug_crops")
os.makedirs(DEBUG_DIR, exist_ok=True)


# ==========================================
# 3. HELPER FUNCTIONS
# ==========================================
def clean_2digit(text):
    nums = re.findall(r"\d+", text)
    if not nums:
        return None
    combined = "".join(nums)
    if len(combined) >= 2:
        return combined[:2]
    elif len(combined) == 1:
        return combined.zfill(2)
    return None


def is_red_off(cell_img):
    hsv = cv2.cvtColor(cell_img, cv2.COLOR_BGR2HSV)
    lower_red1 = np.array([0, 70, 70])
    upper_red1 = np.array([12, 255, 255])
    lower_red2 = np.array([165, 70, 70])
    upper_red2 = np.array([180, 255, 255])

    mask = cv2.inRange(hsv, lower_red1, upper_red1) | cv2.inRange(
        hsv, lower_red2, upper_red2
    )
    ratio = cv2.countNonZero(mask) / (cell_img.shape[0] * cell_img.shape[1])
    return ratio > 0.025


def preprocess_and_ocr(crop_img, tag=""):
    if crop_img is None or crop_img.size == 0:
        return "--"

    if tag:
        cv2.imwrite(os.path.join(DEBUG_DIR, f"{tag}.png"), crop_img)

    resized = cv2.resize(
        crop_img, (0, 0), fx=4.0, fy=4.0, interpolation=cv2.INTER_CUBIC
    )
    gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)

    config_psm8 = "--psm 8 -c tessedit_char_whitelist=0123456789"
    config_psm7 = "--psm 7 -c tessedit_char_whitelist=0123456789"

    # Pass 1: Otsu
    _, thresh = cv2.threshold(
        gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )
    padded1 = cv2.copyMakeBorder(
        thresh, 20, 20, 20, 20, cv2.BORDER_CONSTANT, value=[255, 255, 255]
    )
    text = pytesseract.image_to_string(padded1, config=config_psm8)
    num = clean_2digit(text)
    if num:
        return num

    # Pass 2: Morph Clean
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    cleaned = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
    padded2 = cv2.copyMakeBorder(
        cleaned, 20, 20, 20, 20, cv2.BORDER_CONSTANT, value=[255, 255, 255]
    )
    text = pytesseract.image_to_string(padded2, config=config_psm7)
    num = clean_2digit(text)

    return num if num else "--"


def parse_cell(cell_img, r=0, c=0, date_str=""):
    if is_red_off(cell_img):
        return {"status": "OFF"}

    h, w, _ = cell_img.shape

    if r == 0:
        m_start, m_end = 0.15, 0.58
        e_start, e_end = 0.52, 0.88
    elif r in [3, 4]:
        m_start, m_end = 0.15, 0.50
        e_start, e_end = 0.48, 0.85
    else:
        m_start, m_end = 0.18, 0.52
        e_start, e_end = 0.50, 0.86

    x_start = 0.02 if c in [3, 4] else 0.05
    x_end = 0.98 if c in [3, 4] else 0.95

    morn_crop = cell_img[
        int(h * m_start) : int(h * m_end), int(w * x_start) : int(w * x_end)
    ]
    eve_crop = cell_img[
        int(h * e_start) : int(h * e_end), int(w * x_start) : int(w * x_end)
    ]

    morning = preprocess_and_ocr(morn_crop, tag=f"{date_str}_morn")
    evening = preprocess_and_ocr(eve_crop, tag=f"{date_str}_eve")

    return {
        "status": "OPEN",
        "morning": morning,
        "evening": evening,
    }


# ==========================================
# 4. MAIN PROCESSOR WITH DEBUG GRID
# ==========================================
def test_process_january_2023(img_path):
    img = cv2.imread(img_path)
    if img is None:
        print("Image Loading Failed")
        return

    # Clone image for debug grid visualization
    debug_img = img.copy()

    height, width, _ = img.shape
    year, month = 2023, 1

    print(f"Testing: {os.path.basename(img_path)} ({year}-{month})")

    # Current Coordinates Percentages
    grid_top = int(height * 0.33)
    grid_bottom = int(height * 0.96)
    grid_left = int(width * 0.01)
    grid_right = int(width * 0.99)

    rows, cols = 5, 5
    cell_h = (grid_bottom - grid_top) / rows
    cell_w = (grid_right - grid_left) / cols

    days_grid = [
        [2, 3, 4, 5, 6],
        [9, 10, 11, 12, 13],
        [16, 17, 18, 19, 20],
        [23, 24, 25, 26, 27],
        [30, 31, None, None, None],
    ]

    success_count = 0

    for r in range(rows):
        for c in range(cols):
            day = days_grid[r][c]
            if day is None:
                continue

            y1 = int(grid_top + (r * cell_h))
            y2 = int(grid_top + ((r + 1) * cell_h))
            x1 = int(grid_left + (c * cell_w))
            x2 = int(grid_left + ((c + 1) * cell_w))

            # 🎯 Draw Green Grid Box & Red Day Text for Visual Verification
            if DEBUG_GRID:
                cv2.rectangle(debug_img, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(
                    debug_img,
                    f"D{day}",
                    (x1 + 10, y1 + 35),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.9,
                    (0, 0, 255),
                    2,
                )

            cell_img = img[y1:y2, x1:x2]
            date_str = f"{year}-{month:02d}-{day:02d}"
            res = parse_cell(cell_img, r=r, c=c, date_str=date_str)

            if res and res["status"] == "OFF":
                data = {
                    "date": date_str,
                    "status": "OFF",
                    "is_open": False,
                    "morning": None,
                    "evening": None,
                    "updated_at": firestore.SERVER_TIMESTAMP,
                }
                print(f"  ➜ [{date_str}] Status: OFF")
                db.collection("test_2d_results").document(date_str).set(data)
                success_count += 1

            elif res and res["status"] == "OPEN":
                data = {
                    "date": date_str,
                    "status": "OPEN",
                    "is_open": True,
                    "morning": res["morning"],
                    "evening": res["evening"],
                    "updated_at": firestore.SERVER_TIMESTAMP,
                }
                print(
                    f"  ➜ [{date_str}] Morning: {res['morning']}, Evening: {res['evening']}"
                )
                db.collection("test_2d_results").document(date_str).set(data)
                success_count += 1

    # Save output image with Grid lines
    if DEBUG_GRID:
        out_debug_path = os.path.join(BASE_DIR, "debug_grid.png")
        cv2.imwrite(out_debug_path, debug_img)
        print(f"\n📸 Debug Grid Saved at: {out_debug_path}")

    print(f"Completed Processing: {success_count} / 21 items processed.")


# ==========================================
# 5. EXECUTION
# ==========================================
if __name__ == "__main__":
    zip_path = os.path.join(BASE_DIR, "history", "zips", "2023.zip")
    if not os.path.exists(zip_path):
        zip_path = os.path.join(BASE_DIR, "history", "2023.zip")

    if os.path.exists(zip_path):
        with tempfile.TemporaryDirectory() as temp_dir:
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall(temp_dir)

            target_img = None
            for root, _, files in os.walk(temp_dir):
                if "__MACOSX" in root:
                    continue
                for f in files:
                    if f.upper().endswith(".PNG") and "IMG_4471" in f.upper():
                        target_img = os.path.join(root, f)
                        break

            if target_img:
                test_process_january_2023(target_img)
            else:
                print("IMG_4471.PNG not found")