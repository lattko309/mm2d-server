from pathlib import Path
import cv2
import pytesseract
import re

# ------------------------
# Tesseract
# ------------------------

pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)

# ------------------------
# Folder
# ------------------------

BASE_DIR = Path(__file__).parent

CELL_DIR = BASE_DIR / "cells" / "detected"

# ------------------------
# OCR Function
# ------------------------

def read_cell(image_path):

    img = cv2.imread(str(image_path))

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    _, gray = cv2.threshold(
        gray,
        170,
        255,
        cv2.THRESH_BINARY
    )

    text = pytesseract.image_to_string(
        gray,
        lang="eng",
        config="--psm 6"
    )

    return text


# ------------------------
# Parse
# ------------------------

for cell in sorted(CELL_DIR.glob("*.png")):

    text = read_cell(cell)

    print("=" * 40)
    print(cell.name)
    print(text)

    if "Off" in text or "OFF" in text:

        nums = re.findall(r"\d+", text)

        date = nums[0] if nums else ""

        print({
            "date": date,
            "status": "OFF",
            "am": "",
            "pm": ""
        })

    else:

        nums = re.findall(r"\d+", text)

        if len(nums) >= 3:

            print({
                "date": nums[0],
                "status": "OPEN",
                "am": nums[1],
                "pm": nums[2]
            })