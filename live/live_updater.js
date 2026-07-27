//import axios from "axios";
//import { FieldValue } from "firebase-admin/firestore";
//import db from "./firebase.js";
//
//import { sleep, createHistoryId } from "./helper.js";
//import { log, warn, error } from "./logger.js";
//import { validate } from "./validator.js";
//import { isMarketOpen } from "./market_guard.js";
//
//// ========================================
//// Settings
//// ========================================
//
//const FETCH_INTERVAL = 5000;
//const MAX_RETRY = 3;
//
//const LIVE_DOC = db.collection("live").doc("current");
//const TODAY_COLLECTION = db.collection("today");
//const HISTORY_COLLECTION = db.collection("history");
//
//// ========================================
//// Fetch Live Data
//// ========================================
//
//async function fetchLiveData() {
//
//  for (let retry = 1; retry <= MAX_RETRY; retry++) {
//
//    try {
//
//      const response = await axios.get(
//        "http://127.0.0.1:8000/api/2d-live",
//        {
//          timeout: 5000,
//        }
//      );
//
//      return response.data;
//
//    } catch (e) {
//
//      warn(`Retry ${retry}/${MAX_RETRY}`);
//
//      if (retry === MAX_RETRY) {
//        throw e;
//      }
//
//      await sleep(1000);
//    }
//  }
//
//  return null;
//}
//
//// ========================================
//// Duplicate Check
//// ========================================
//
//async function isDuplicate(data) {
//
//  const doc = await LIVE_DOC.get();
//
//  if (!doc.exists) {
//    return false;
//  }
//
//  const old = doc.data();
//
//  return (
//    old.date === data.date &&
//    old.session === data.session &&
//    old.result === data.result &&
//    old.setIndex === data.setIndex &&
//    old.setValue === data.setValue &&
//    old.isFinal === data.isFinal
//  );
//}
//
//// ========================================
//// Save History
//// ========================================
//
//async function saveHistory(data) {
//
//  const id = createHistoryId(
//    data.date,
//    data.session,
//  );
//
//  const ref = HISTORY_COLLECTION.doc(id);
//
//  const doc = await ref.get();
//
//  if (doc.exists) {
//    return;
//  }
//
//  const [year, month, day] =
//    data.date.split("-").map(Number);
//
//  await ref.set({
//    date: data.date,
//    session: data.session,
//    result: data.result,
//    setIndex: Number(data.setIndex),
//    setValue: Number(data.setValue),
//
//    year,
//    month,
//    dayNumber: day,
//
//    isFinal: data.isFinal ?? false,
//
//    createdAt: FieldValue.serverTimestamp(),
//  });
//
//  log(`History Saved : ${id}`);
//}
//
//// ========================================
//// Update Live
//// ========================================
//
//async function updateLive() {
//
//  //----------------------------------------
//  // Market Check
//  //----------------------------------------
//
////  if (!isMarketOpen()) {
////    log("Market Closed");
////    return;
////  }
//
//  //----------------------------------------
//  // Fetch API
//  //----------------------------------------
//
//  const data = await fetchLiveData();
//
//  if (!validate(data)) {
//    warn("Invalid Live Data");
//    return;
//  }
//
//  //----------------------------------------
//  // Duplicate
//  //----------------------------------------
//
//  if (await isDuplicate(data)) {
//    log("Duplicate -> Skip");
//    return;
//  }
//
//  //----------------------------------------
//  // Live/current
//  //----------------------------------------
//
//  await LIVE_DOC.set(
//    {
//      date: data.date,
//      session: data.session,
//
//      result: data.result,
//
//      setIndex: Number(data.setIndex),
//      setValue: Number(data.setValue),
//
//      isLive: data.isLive ?? true,
//      isFinal: data.isFinal ?? false,
//
//      updatedAt:
//        FieldValue.serverTimestamp(),
//    },
//    {
//      merge: true,
//    }
//  );
//
//  log(
//    `Live Updated : ${data.result}`
//  );
//
//  //----------------------------------------
//  // today
//  //----------------------------------------
//
//  await TODAY_COLLECTION
//    .doc(data.session)
//    .set(
//      {
//        date: data.date,
//        session: data.session,
//
//        result: data.result,
//
//        setIndex: Number(data.setIndex),
//        setValue: Number(data.setValue),
//
//        isLive: data.isLive ?? true,
//        isFinal: data.isFinal ?? false,
//
//        updatedAt:
//          FieldValue.serverTimestamp(),
//      },
//      {
//        merge: true,
//      }
//    );
//
//  log(
//    `Today Updated : ${data.session}`
//  );
//
//  //----------------------------------------
//  // History
//  //----------------------------------------
//
//  if (data.isFinal === true) {
//    await saveHistory(data);
//  }
//}
//
//// ========================================
//// Main Loop
//// ========================================
//
//async function run() {
//
//  try {
//
//    await updateLive();
//
//  } catch (e) {
//
//    error(e.stack ?? e.message);
//
//  } finally {
//
//    setTimeout(run, FETCH_INTERVAL);
//
//  }
//
//}
//
//// ========================================
//// Startup
//// ========================================
//
//async function main() {
//
//  log("================================");
//  log("MM2D Live Updater");
//  log("================================");
//
//  log(`Fetch Interval : ${FETCH_INTERVAL} ms`);
//  log("Waiting for market...");
//
//  await run();
//
//}
//
//// ========================================
//// Start
//// ========================================
//
//main().catch((e) => {
//
//  error("Application Error");
//  error(e.stack ?? e.message);
//
//});