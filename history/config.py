from pathlib import Path

# ==========================
# Project
# ==========================
PROJECT_ID = "myanmar2d-739a7"

# ==========================
# Firestore
# ==========================
COLLECTION = "history"

# ==========================
# History Import
# ==========================
START_DATE = "2020-01-01"
END_DATE = "2026-12-31"

# ==========================
# Browser
# ==========================
HEADLESS = True
WAIT_TIMEOUT = 15000

# ==========================
# Paths
# ==========================
BASE_DIR = Path(__file__).resolve().parents[2]

TOOLS_DIR = BASE_DIR / "tools"

SERVICE_ACCOUNT = TOOLS_DIR / "serviceAccountKey.json"