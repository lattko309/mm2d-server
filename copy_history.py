from pathlib import Path
import firebase_admin
from firebase_admin import credentials, firestore

BASE_DIR = Path(__file__).resolve().parent
TOOLS = BASE_DIR.parent / "tools"

# Source Project
source_cred = credentials.Certificate(
    TOOLS / "it252228-serviceAccountKey.json"
)
source_app = firebase_admin.initialize_app(
    source_cred,
    name="source"
)
source_db = firestore.client(source_app)

# Destination Project
dest_cred = credentials.Certificate(
    TOOLS / "serviceAccountKey.json"
)
dest_app = firebase_admin.initialize_app(
    dest_cred,
    name="dest"
)
dest_db = firestore.client(dest_app)

print("Copy history...")

docs = source_db.collection("history").stream()

count = 0

for doc in docs:
    dest_db.collection("history").document(doc.id).set(doc.to_dict())
    count += 1

print(f"Done! {count} documents copied.")