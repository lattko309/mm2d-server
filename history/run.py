"""
Myanmar 2D History Builder
Version : 1.0
Part 1
"""

from pathlib import Path
import zipfile
import shutil
import json
import re

import cv2
import pytesseract
import pandas as pd
import numpy as np

# ----------------------------------------
# Tesseract
# ----------------------------------------

pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)

# ----------------------------------------
# Folder
# ----------------------------------------

BASE_DIR = Path(__file__).parent

ZIP_DIR = BASE_DIR / "zips"
EXTRACT_DIR = BASE_DIR / "extracted"
CELL_DIR = BASE_DIR / "cells"
CSV_DIR = BASE_DIR / "csv"

EXTRACT_DIR.mkdir(exist_ok=True)
CELL_DIR.mkdir(exist_ok=True)
CSV_DIR.mkdir(exist_ok=True)

# ----------------------------------------
# Month
# ----------------------------------------

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

# ----------------------------------------
# Clean Folder
# ----------------------------------------

def clean_output():

    if EXTRACT_DIR.exists():
        shutil.rmtree(EXTRACT_DIR)

    if CELL_DIR.exists():
        shutil.rmtree(CELL_DIR)

    EXTRACT_DIR.mkdir(exist_ok=True)
    CELL_DIR.mkdir(exist_ok=True)

# ----------------------------------------
# Extract ZIP
# ----------------------------------------

def extract_all():

    print("=" * 60)
    print("Extract ZIP")
    print("=" * 60)

    total = 0

    for zip_file in sorted(ZIP_DIR.glob("*.zip")):

        year = zip_file.stem

        output = EXTRACT_DIR / year

        output.mkdir(exist_ok=True)

        print("Extract :", zip_file.name)

        with zipfile.ZipFile(zip_file, "r") as z:
            z.extractall(output)

    images = []

    for ext in ("*.png", "*.PNG", "*.jpg", "*.JPG"):

        images.extend(EXTRACT_DIR.rglob(ext))

    images = sorted(images)

    total = len(images)

    print()
    print("Images :", total)
    print()

    return images

# ----------------------------------------
# Header Reader
# ----------------------------------------

def read_header(image_path):

    img = cv2.imread(str(image_path))

    h, w = img.shape[:2]

    header = img[0:int(h * 0.20), 0:w]

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

    for name in MONTHS:

        if name.lower() in text.lower():

            month = MONTHS[name]
            break

    return year, month, text

# ----------------------------------------
# Create Month Folder
# ----------------------------------------

def month_folder(year, month):

    folder = CELL_DIR / str(year) / f"{month:02d}"

    folder.mkdir(
        parents=True,
        exist_ok=True
    )

    return folder

# ----------------------------------------
# Print Header
# ----------------------------------------

def print_header():

    print("=" * 60)
    print("Myanmar 2D History Builder")
    print("Version 1.0")
    print("=" * 60)