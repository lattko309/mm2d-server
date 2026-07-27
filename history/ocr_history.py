from pathlib import Path
import cv2

BASE_DIR = Path(__file__).parent

EXTRACT_DIR = BASE_DIR / "extracted"
CELL_DIR = BASE_DIR / "cells"

CELL_DIR.mkdir(exist_ok=True)

# ပထမဆုံး Image ကိုယူ
images = sorted(EXTRACT_DIR.rglob("*.PNG"))

if not images:
    print("No images.")
    exit()

image_path = images[0]

print("Reading:", image_path.name)

img = cv2.imread(str(image_path))

# Resize (Preview အတွက်)
preview = cv2.resize(img, (800, 1600))

# Preview သိမ်း
cv2.imwrite(str(CELL_DIR / "preview.png"), preview)

print("Preview saved.")