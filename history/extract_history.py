from pathlib import Path
import zipfile

# ==========================
# Folder
# ==========================

BASE_DIR = Path(__file__).parent

ZIP_DIR = BASE_DIR / "zips"
EXTRACT_DIR = BASE_DIR / "extracted"

EXTRACT_DIR.mkdir(exist_ok=True)

# ==========================
# Extract ZIP
# ==========================

zip_files = sorted(ZIP_DIR.glob("*.zip"))

print("=" * 50)

for zip_path in zip_files:

    year = zip_path.stem

    output = EXTRACT_DIR / year
    output.mkdir(exist_ok=True)

    print(f"Extracting {zip_path.name}")

    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(output)

print("\nExtract Finished")

print("=" * 50)

# ==========================
# Scan PNG
# ==========================

total = 0

for year_folder in sorted(EXTRACT_DIR.iterdir()):

    if not year_folder.is_dir():
        continue

    pngs = list(year_folder.rglob("*.png"))

    print(f"{year_folder.name} : {len(pngs)} PNG")

    total += len(pngs)

print("=" * 50)
print(f"TOTAL PNG : {total}")
print("=" * 50)
print("\nFirst 10 PNG Files")
print("=" * 50)

count = 0

for png in sorted(EXTRACT_DIR.rglob("*.png")):

    print(png)

    count += 1

    if count == 10:
        break