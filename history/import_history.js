import { initializeApp, cert } from "firebase-admin/app";
import { getFirestore, FieldValue } from "firebase-admin/firestore";
import csv from "csv-parser";
import fs from "fs";

// =========================================
// Firebase Initialization
// =========================================

const serviceAccount = JSON.parse(
  fs.readFileSync("../../tools/serviceAccountKey.json", "utf8")
);

initializeApp({
  credential: cert(serviceAccount),
});

const db = getFirestore();

// =========================================
// Settings
// =========================================

const CSV_FILE = "./csv/history.csv";
const COLLECTION = "history";
const BATCH_LIMIT = 400;

// =========================================
// Helpers
// =========================================

function weekday(dateString) {

  const days = [
    "Sunday",
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
  ];

  return days[new Date(dateString).getDay()];
}

function normalize(value) {

  if (value === undefined || value === null) {
    return "";
  }

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

          if (rows.length === 0) {
              console.log(row);
          }

          const cleanRow = {};

          for (const key in row) {
            cleanRow[key.replace(/^\uFEFF/, "")] = row[key];
          }

          rows.push(cleanRow);
      })

      .on("end", () => {

        console.log("================================");
        console.log("CSV Loaded");
        console.log("Rows :", rows.length);
        console.log("================================");

        resolve();

      })

      .on("error", reject);

  });

}

// =========================================
// Import History
// =========================================

async function importHistory() {

  await loadCSV();

  let imported = 0;

  let batch = db.batch();

  for (const row of rows) {

    const date = row.date?.trim();

    if (!date) {
      continue;
    }

    const status = row.status?.trim();

    const [year, month, dayNumber] =
      date.split("-").map(Number);

    const day = weekday(date);

    //------------------------------------------------
    // Morning (12:01)
    //------------------------------------------------

    if (
      status === "OPEN" &&
      row.am !== undefined &&
      row.am !== ""
    ) {

      const ref = db
        .collection(COLLECTION)
        .doc(`${date}-1201`);

      batch.set(ref, {
        date,
        weekday: day,
        session: "12:01",
        result: normalize(row.am),
        setIndex: 0,
        setValue: 0,
        year,
        month,
        dayNumber,
        createdAt:
          FieldValue.serverTimestamp()
      });

      imported++;
    }

    //------------------------------------------------
    // Evening (16:30)
    //------------------------------------------------

    if (
      status === "OPEN" &&
      row.pm !== undefined &&
      row.pm !== ""
    ) {

      const ref = db
        .collection(COLLECTION)
        .doc(`${date}-1630`);

      batch.set(ref, {
        date,
        weekday: day,
        session: "16:30",
        result: normalize(row.pm),
        setIndex: 0,
        setValue: 0,
        year,
        month,
        dayNumber,
        createdAt: FieldValue.serverTimestamp(),
      });

      imported++;
    }

    //------------------------------------------------
    // Commit Every 400 Writes
    //------------------------------------------------

    if (imported > 0 && imported % BATCH_LIMIT === 0) {

      await batch.commit();

      console.log(
        `Imported : ${imported}`
      );

      batch = db.batch();
    }

  }

  // Commit Remaining Documents
  await batch.commit();

  return imported;
}

// =========================================
// Main
// =========================================

async function main() {

  try {

    console.log("================================");
    console.log("History Import Started");
    console.log("================================");

    const total = await importHistory();

    console.log();
    console.log("================================");
    console.log("History Import Finished");
    console.log("================================");
    console.log("Collection :", COLLECTION);
    console.log("Imported   :", total);
    console.log("================================");

    //----------------------------------------
    // Verify
    //----------------------------------------

    const snapshot = await db
      .collection(COLLECTION)
      .orderBy("date")
      .limit(6)
      .get();

    console.log();
    console.log("Verify");
    console.log("================================");

    snapshot.forEach((doc) => {

      const data = doc.data();

      console.log(
        `${doc.id} | ${data.session} | ${data.result}`
      );

    });

    console.log("================================");
    console.log("Done.");

    process.exit(0);

  } catch (err) {

    console.error(err);
    process.exit(1);

  }

}

main();