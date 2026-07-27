// ========================================
// Thailand / Myanmar Market Time
// ========================================

function getThaiTime() {
  return new Date(
    new Date().toLocaleString("en-US", {
      timeZone: "Asia/Bangkok",
    })
  );
}

// ========================================
// Market Open Check
// ========================================

export function isMarketOpen() {
  const thai = getThaiTime();

  const day = thai.getDay();

  // Sunday
  if (day === 0) {
    return false;
  }

  // Saturday
  if (day === 6) {
    return false;
  }

  const minutes =
    thai.getHours() * 60 + thai.getMinutes();

  const morning =
    minutes >= 570 && minutes <= 725;

  const afternoon =
    minutes >= 840 && minutes <= 995;

  return morning || afternoon;
}

// ========================================
// Current Session
// ========================================

export function currentSession() {

  const thai = getThaiTime();

  const minutes =
    thai.getHours() * 60 + thai.getMinutes();

  if (minutes <= 725) {
    return "12:01";
  }

  return "16:30";
}