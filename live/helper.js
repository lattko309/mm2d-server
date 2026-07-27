// ========================================
// Sleep
// ========================================

export function sleep(ms) {
  return new Promise((resolve) => {
    setTimeout(resolve, ms);
  });
}

// ========================================
// Number Formatter
// ========================================

export function normalizeResult(value) {
  if (value === undefined || value === null) {
    return "--";
  }

  const text = String(value).trim();

  if (text === "") {
    return "--";
  }

  return text.padStart(2, "0");
}

// ========================================
// Date Formatter
// ========================================

export function getToday() {
  const now = new Date(
    new Date().toLocaleString("en-US", {
      timeZone: "Asia/Bangkok",
    })
  );

  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  const day = String(now.getDate()).padStart(2, "0");

  return `${year}-${month}-${day}`;
}

// ========================================
// Document ID
// ========================================

export function createHistoryId(date, session) {
  return `${date}-${session.replace(":", "")}`;
}