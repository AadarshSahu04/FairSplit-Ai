/**
 * api.js — Single source of truth for all backend API calls.
 * All fetch logic lives here. No other file calls fetch() directly.
 *
 * Phase 8 implementation: real FastAPI endpoints.
 * Phase 3: extractBill uses a mock response when VITE_USE_MOCK=true.
 */

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';
const USE_MOCK = import.meta.env.VITE_USE_MOCK === 'true';

// ── Helpers ────────────────────────────────────────────────────

async function apiRequest(path, options = {}) {
  const url = `${API_BASE}${path}`;
  const response = await fetch(url, options);

  if (!response.ok) {
    let detail = `HTTP ${response.status}`;
    try {
      const body = await response.json();
      detail = body.detail || body.message || detail;
    } catch {/* ignore */}
    throw new Error(detail);
  }

  return response.json();
}

// ── Mock Data (Phase 3 — used when backend OCR not ready) ──────

const MOCK_BILL = {
  items: [
    { id: 'mock-item-1', name: 'Chicken Biryani', quantity: '2', unit_price: '250.00', total_price: '500.00', confidence: 0.97, needs_review: false },
    { id: 'mock-item-2', name: 'Dal Makhani',     quantity: '1', unit_price: '180.00', total_price: '180.00', confidence: 0.95, needs_review: false },
    { id: 'mock-item-3', name: 'Garlic Naan',     quantity: '4', unit_price: '50.00',  total_price: '200.00', confidence: 0.92, needs_review: false },
    { id: 'mock-item-4', name: 'Mango Lassi',     quantity: '2', unit_price: '80.00',  total_price: '160.00', confidence: 0.88, needs_review: false },
    { id: 'mock-item-5', name: 'Coke',            quantity: '3', unit_price: '60.00',  total_price: '180.00', confidence: 0.60, needs_review: true  },
  ],
  subtotal:            '1220.00',
  gst:                 '109.80',
  service_charge:      '61.00',
  discount:            '0',
  total:               '1390.80',
  extraction_warnings: ['Item "Coke" has low confidence — please verify.'],
};

// ── Exported API Functions ─────────────────────────────────────

/**
 * Upload bill image(s) and extract structured bill data.
 * @param {File[]} images — array of image files (1–4 supported)
 * @returns {Promise<{bill: object, warnings: string[]}>}
 */
export async function extractBill(images) {
  if (USE_MOCK) {
    // Simulate network delay for realistic UX
    await new Promise((resolve) => setTimeout(resolve, 1800));
    return { bill: MOCK_BILL, warnings: MOCK_BILL.extraction_warnings };
  }

  const formData = new FormData();
  images.forEach((file) => formData.append('images', file));

  return apiRequest('/api/bill/extract', {
    method: 'POST',
    body:   formData,
  });
}

/**
 * Validate human-corrected bill data.
 * @param {object} bill — human-reviewed bill object
 * @returns {Promise<{bill: object, arithmetic_checks: object, warnings: string[]}>}
 */
export async function validateBill(bill) {
  return apiRequest('/api/bill/validate', {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
    body:    JSON.stringify({ bill }),
  });
}

/**
 * Calculate the fair split for a confirmed bill.
 * @param {{ bill, people, assignments }} splitRequest
 * @returns {Promise<object>} SplitResult
 */
export async function splitBill(splitRequest) {
  return apiRequest('/api/bill/split', {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
    body:    JSON.stringify(splitRequest),
  });
}

export { API_BASE };
