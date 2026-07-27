from history_firestore import get_db

# ==================================================
# Firestore
# ==================================================

db = get_db()
collection = db.collection("history")

print("=" * 60)
print("Delete History Collection")
print("=" * 60)

count = 0

while True:

    docs = list(collection.limit(500).stream())

    if not docs:
        break

    for doc in docs:
        doc.reference.delete()
        count += 1

        if count % 50 == 0:
            print(f"Deleted : {count}")

print()
print("=" * 60)
print("Delete Finished")
print("=" * 60)
print("Deleted :", count)
print("=" * 60)