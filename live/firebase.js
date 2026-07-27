import { readFileSync } from "fs";
import { initializeApp, cert } from "firebase-admin/app";
import { getFirestore } from "firebase-admin/firestore";

// ========================================
// Service Account
// ========================================

const serviceAccount = JSON.parse(
  readFileSync("../../tools/serviceAccountKey.json", "utf8")
);

// ========================================
// Firebase Initialize
// ========================================

const app = initializeApp({
  credential: cert(serviceAccount),
});

const db = getFirestore(app);

// ========================================
// Export
// ========================================

export default db;