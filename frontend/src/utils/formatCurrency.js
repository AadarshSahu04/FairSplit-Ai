/**
 * formatCurrency.js — Display-only currency formatting for FairSplit AI.
 * No arithmetic is performed here.
 */

/**
 * Format a number/string as Indian Rupees.
 * @param {number|string} amount
 * @param {object} [options]
 * @param {boolean} [options.showSymbol=true]
 * @param {number} [options.decimals=2]
 * @returns {string}
 */
export function formatINR(amount, { showSymbol = true, decimals = 2 } = {}) {
  const num = typeof amount === 'string' ? parseFloat(amount) : amount;
  if (isNaN(num)) return showSymbol ? '₹—' : '—';

  const formatted = num.toFixed(decimals);
  return showSymbol ? `₹${formatted}` : formatted;
}

/**
 * Format a proportion (0–1) as a percentage string.
 * @param {number} proportion — 0 to 1
 * @param {number} [decimals=0]
 */
export function formatPercent(proportion, decimals = 0) {
  return `${(proportion * 100).toFixed(decimals)}%`;
}
