import admin from "firebase-admin";
import csv from "csv-parser";
import fs from "fs";

// =========================================
// Firebase Initialization
// =========================================

const serviceAccount = JSON.parse(
  fs.readFileSync("./serviceAccountKey.json", "utf8")
);

admin.initializeApp({
  credential: admin.credential.cert(serviceAccount),
});

const db = admin.firestore();

console.log("================================");
console.log("Firebase Connected");
console.log("================================");

// =========================================
// Settings
// =========================================

const CSV_FILE = "./csv/history.csv";
const COLLECTION = "history";

// =========================================
// Helpers
// =========================================

function getWeekday(dateString) {
  const weekdays = [
    "Sunday",
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
  ];

  const date = new Date(dateString);

  return weekdays[date.getDay()];
}

function safeNumber(value) {
  const n = Number(value);

  return Number.isNaN(n) ? 0 : n;
}

function normalizeResult(value) {
  if (!value) return "";

  return String(value).padStart(2, "0");
}

// =========================================
// Read CSV
// =========================================

const rows = [];

async function loadCSV() {
  return new Promise((resolve, reject) => {
    fs.createReadStream(CSV_FILE)
      .pipe(csv())
      .on("data", (row) => {
        rows.push(row);
      })
      .on("end", () => {
        console.log(`CSV Loaded : ${rows.length} rows`);
        resolve();
      })
      .on("error", reject);
  });
}