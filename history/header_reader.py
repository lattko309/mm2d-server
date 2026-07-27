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
EXTRACT_DIR = BASE_DIR / "extracted"

# ------------------------
# First Image
# ------------------------

images = sorted(EXTRACT_DIR.rglob("*.PNG"))

if not images:
    print("No Images")
    exit()

image = images[0]

print("Image :", image.name)

# ------------------------
# Read Image
# ------------------------

img = cv2.imread(str(image))

# Header Area (Top 20%)
h, w = img.shape[:2]

header = img[0:int(h*0.20), 0:w]

gray = cv2.cvtColor(header, cv2.COLOR_BGR2GRAY)

text = pytesseract.image_to_string(
    gray,
    lang="eng",
    config="--psm 6"
)

print("="*40)
print(text)
print("="*40)

# ------------------------
# Month
# ------------------------

months = {
    "January":1,
    "February":2,
    "March":3,
    "April":4,
    "May":5,
    "June":6,
    "July":7,
    "August":8,
    "September":9,
    "October":10,
    "November":11,
    "December":12
}

month = None

for m in months:
    if m.lower() in text.lower():
        month = months[m]
        break

year = None

m = re.search(r"20\d\d", text)

if m:
    year = int(m.group())

print("Year :", year)
print("Month:", month)