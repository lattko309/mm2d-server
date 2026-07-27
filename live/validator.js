// ========================================
// Live Data Validation
// ========================================

export function validate(data) {
  if (!data) {
    return false;
  }

  if (!data.date) {
    return false;
  }

  if (!data.session) {
    return false;
  }

  if (!data.result) {
    return false;
  }

  const result = String(data.result).trim();

  // 2 digits only
  if (!/^\d{2}$/.test(result)) {
    return false;
  }

  if (isNaN(Number(data.setIndex))) {
    return false;
  }

  if (isNaN(Number(data.setValue))) {
    return false;
  }

  return true;
}