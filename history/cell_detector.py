from pathlib import Path
import cv2
import numpy as np
import pytesseract
import re
import calendar

# --------------------------------------------------
# Tesseract
# --------------------------------------------------

pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)

# --------------------------------------------------
# Folder
# --------------------------------------------------

BASE_DIR = Path(__file__).parent

EXTRACT_DIR = BASE_DIR / "extracted"
CELL_DIR = BASE_DIR / "cells"

CELL_DIR.mkdir(exist_ok=True)

# --------------------------------------------------
# Month Dictionary
# --------------------------------------------------

MONTHS = {
    "January": 1,
    "February": 2,
    "March": 3,
    "April": 4,
    "May": 5,
    "June": 6,
    "July": 7,
    "August": 8,
    "September": 9,
    "October": 10,
    "November": 11,
    "December": 12,
}

# --------------------------------------------------
# Read Header
# --------------------------------------------------

def read_header(image):

    h, w = image.shape[:2]

    header = image[0:int(h * 0.20), :]

    gray = cv2.cvtColor(header, cv2.COLOR_BGR2GRAY)

    text = pytesseract.image_to_string(
        gray,
        lang="eng",
        config="--psm 6"
    )

    year = None
    month = None

    m = re.search(r"20\d\d", text)

    if m:
        year = int(m.group())

    for name, value in MONTHS.items():

        if name.lower() in text.lower():
            month = value
            break

    return year, month

# --------------------------------------------------
# Get Images
# --------------------------------------------------

images = []

for ext in ("*.PNG", "*.png", "*.JPG", "*.jpg"):
    images.extend(EXTRACT_DIR.rglob(ext))

images = sorted(images)
# Remove Apple metadata files
images = [
    img for img in images
    if not img.name.startswith("._")
]

print("=" * 60)
print("Total Images :", len(images))
print("=" * 60)

# --------------------------------------------------
# Process Each Screenshot
# --------------------------------------------------

for image_path in images:

    print()
    print("Reading :", image_path.name)

    img = cv2.imread(str(image_path))

    year, month = read_header(img)

    print("Year :", year)
    print("Month:", month)

    if year is None or month is None:
        print("Skip")
        continue

    # Save Folder

    out_dir = CELL_DIR / str(year) / f"{month:02d}"

    out_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    # HSV

    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    lower = np.array([15, 80, 150])
    upper = np.array([40, 255, 255])

    mask = cv2.inRange(hsv, lower, upper)

    contours, _ = cv2.findContours(
        mask,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    # Sort

    boxes = []

    for c in contours:

        x, y, w, h = cv2.boundingRect(c)

        if w < 80 or h < 120:
            continue

        boxes.append((x, y, w, h))

    boxes.sort(key=lambda b: (b[1], b[0]))

    print("Cells :", len(boxes))
    # ------------------------------------------
    # Create Date List
    # ------------------------------------------

    weeks = calendar.monthcalendar(year, month)

    dates = []

    for week in weeks:
        for day in week:
            if day != 0:
                dates.append(day)

    # Check

    if len(dates) != len(boxes):
        print(
            f"Warning : dates={len(dates)} cells={len(boxes)}"
        )

    # ------------------------------------------
    # Save Cell
    # ------------------------------------------

    for i, (x, y, w, h) in enumerate(boxes):

        if i >= len(dates):
            break

        day = dates[i]

        roi = img[y:y+h, x:x+w]

        filename = (
            f"{year}-"
            f"{month:02d}-"
            f"{day:02d}.png"
        )

        cv2.imwrite(
            str(out_dir / filename),
            roi
        )

        print("Save :", filename)

print()
print("=" * 60)
print("Finished")
print("=" * 60)
