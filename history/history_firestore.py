from pathlib import Path

import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

from config import PROJECT_ID, SERVICE_ACCOUNT

# ==================================================
# Firebase Initialize
# ==================================================

_app = None


def get_db():
    global _app

    if _app is None:

        cred = credentials.Certificate(str(SERVICE_ACCOUNT))

        _app = firebase_admin.initialize_app(
            cred,
            {
                "projectId": PROJECT_ID,
            },
        )

    return firestore.client()


# ==================================================
# Test
# ==================================================

if __name__ == "__main__":

    db = get_db()

    print("=" * 60)
    print("Firestore Connected")
    print("Project :", PROJECT_ID)
    print("=" * 60)