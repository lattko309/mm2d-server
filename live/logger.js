// ========================================
// Logger
// ========================================

function now() {
  return new Date().toLocaleString("en-US", {
    timeZone: "Asia/Bangkok",
  });
}

export function log(message) {
  console.log(`[${now()}] ${message}`);
}

export function info(message) {
  console.log(`[INFO ${now()}] ${message}`);
}

export function warn(message) {
  console.warn(`[WARN ${now()}] ${message}`);
}

export function error(message) {
  console.error(`[ERROR ${now()}] ${message}`);
}