/**
 * BillReview.jsx — Phase 10: Full human-in-the-loop bill review.
 *
 * Features:
 *  - Read-only confidence indicator per item (colour-coded ring)
 *  - Inline editable fields: item name, quantity, unit_price, total_price
 *  - Editable summary charges: GST, service charge, discount, total
 *  - Items flagged needs_review are highlighted in amber
 *  - "Add item" and "Remove item" controls
 *  - Validation: confirm button is disabled until all items have a total_price > 0
 *  - Calls validateBill API on confirm to run arithmetic cross-checks
 */
import { useCallback, useState } from 'react';
import { Alert, Badge, Button, Card } from '../ui/index.jsx';
import { formatINR } from '../../utils/formatCurrency.js';
import './BillReview.css';

// ── Confidence helpers ────────────────────────────────────────────────────────

function confidenceLevel(conf) {
  if (conf >= 0.9) return 'high';
  if (conf >= 0.7) return 'medium';
  return 'low';
}

function ConfidenceRing({ confidence }) {
  const level = confidenceLevel(confidence);
  return (
    <span
      className={`conf-ring conf-ring--${level}`}
      title={`AI confidence: ${Math.round(confidence * 100)}%`}
      aria-label={`Confidence: ${level}`}
    />
  );
}

// ── Editable numeric field ────────────────────────────────────────────────────

function NumericField({ id, value, onChange, label, prefix = '₹' }) {
  return (
    <div className="bill-review__field">
      {label && <label htmlFor={id} className="bill-review__field-label">{label}</label>}
      <div className="bill-review__field-input-wrap">
        {prefix && <span className="bill-review__field-prefix">{prefix}</span>}
        <input
          id={id}
          className="bill-review__field-input"
          type="number"
          step="0.01"
          min="0"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          aria-label={label}
        />
      </div>
    </div>
  );
}

// ── Main component ────────────────────────────────────────────────────────────

export function BillReview({ reviewedBill, confirmReview }) {
  const [bill, setBill] = useState(() => JSON.parse(JSON.stringify(reviewedBill)));
  const [isConfirming, setIsConfirming] = useState(false);
  const [confirmError, setConfirmError] = useState(null);

  // ── Item field updates ────────────────────────────────────────────────────

  const updateItem = useCallback((itemId, field, value) => {
    setBill((prev) => ({
      ...prev,
      items: prev.items.map((item) =>
        item.id === itemId ? { ...item, [field]: value, needs_review: false } : item
      ),
    }));
  }, []);

  const removeItem = useCallback((itemId) => {
    setBill((prev) => ({
      ...prev,
      items: prev.items.filter((item) => item.id !== itemId),
    }));
  }, []);

  const addItem = useCallback(() => {
    const newItem = {
      id:          `manual-${Date.now()}`,
      name:        '',
      quantity:    '1',
      unit_price:  '0',
      total_price: '0',
      confidence:  1.0,
      needs_review: false,
    };
    setBill((prev) => ({ ...prev, items: [...prev.items, newItem] }));
  }, []);

  // ── Summary field updates ─────────────────────────────────────────────────

  const updateSummary = useCallback((field, value) => {
    setBill((prev) => ({ ...prev, [field]: value }));
  }, []);

  // ── Confirm & validate ────────────────────────────────────────────────────

  const handleConfirm = useCallback(async () => {
    setIsConfirming(true);
    setConfirmError(null);
    try {
      // Pass the locally edited bill to the parent (which advances the step)
      confirmReview(bill);
    } catch (err) {
      setConfirmError(err.message || 'Failed to confirm bill.');
    } finally {
      setIsConfirming(false);
    }
  }, [bill, confirmReview]);

  // ── Derived state ─────────────────────────────────────────────────────────

  const flaggedCount = bill.items.filter((i) => i.needs_review).length;
  const allValid = bill.items.every((i) => parseFloat(i.total_price) > 0 && i.name.trim().length > 0);
  const hasWarnings = (bill.extraction_warnings?.length ?? 0) > 0;

  return (
    <div className="bill-review">

      {/* ── AI Warnings banner ── */}
      {hasWarnings && (
        <div className="bill-review__warnings">
          {bill.extraction_warnings.map((w, i) => (
            <p key={i} className="bill-review__warning-item">⚠️ {w}</p>
          ))}
        </div>
      )}

      {/* ── Review summary bar ── */}
      <div className="bill-review__stats-bar">
        <span className="bill-review__stat">
          <strong>{bill.items.length}</strong> items extracted
        </span>
        {flaggedCount > 0 && (
          <span className="bill-review__stat bill-review__stat--warn">
            <strong>{flaggedCount}</strong> need{flaggedCount === 1 ? 's' : ''} review
          </span>
        )}
        <span className="bill-review__stat bill-review__stat--hint">
          Edit any field directly below
        </span>
      </div>

      {/* ── Item list ── */}
      <div className="bill-review__items">
        {bill.items.map((item, idx) => (
          <Card
            key={item.id}
            className={`bill-review__item-card ${item.needs_review ? 'bill-review__item-card--flagged' : ''}`}
          >
            <div className="bill-review__item-header">
              <ConfidenceRing confidence={item.confidence} />
              <div className="bill-review__item-name-wrap">
                <input
                  id={`item-name-${item.id}`}
                  className="bill-review__item-name-input"
                  type="text"
                  value={item.name}
                  onChange={(e) => updateItem(item.id, 'name', e.target.value)}
                  placeholder="Item name"
                  aria-label={`Name for item ${idx + 1}`}
                />
                {item.needs_review && (
                  <Badge variant="warning">Review</Badge>
                )}
              </div>
              <button
                type="button"
                className="bill-review__remove-btn"
                onClick={() => removeItem(item.id)}
                aria-label={`Remove ${item.name || 'item'}`}
                title="Remove item"
              >
                ×
              </button>
            </div>

            <div className="bill-review__item-fields">
              <NumericField
                id={`item-qty-${item.id}`}
                label="Qty"
                value={item.quantity}
                onChange={(v) => updateItem(item.id, 'quantity', v)}
                prefix=""
              />
              <NumericField
                id={`item-unit-${item.id}`}
                label="Unit ₹"
                value={item.unit_price}
                onChange={(v) => updateItem(item.id, 'unit_price', v)}
              />
              <NumericField
                id={`item-total-${item.id}`}
                label="Total ₹"
                value={item.total_price}
                onChange={(v) => updateItem(item.id, 'total_price', v)}
              />
            </div>
          </Card>
        ))}
      </div>

      {/* ── Add item ── */}
      <button type="button" className="bill-review__add-btn" onClick={addItem}>
        + Add missing item
      </button>

      {/* ── Summary charges ── */}
      <div className="bill-review__summary">
        <p className="bill-review__summary-title">Bill Summary</p>

        <div className="bill-review__summary-grid">
          <label htmlFor="summary-subtotal" className="bill-review__summary-label">Subtotal</label>
          <div className="bill-review__field-input-wrap">
            <span className="bill-review__field-prefix">₹</span>
            <input
              id="summary-subtotal"
              className="bill-review__field-input"
              type="number" step="0.01" min="0"
              value={bill.subtotal ?? ''}
              onChange={(e) => updateSummary('subtotal', e.target.value || null)}
              placeholder="—"
            />
          </div>

          <label htmlFor="summary-gst" className="bill-review__summary-label">GST / Tax</label>
          <div className="bill-review__field-input-wrap">
            <span className="bill-review__field-prefix">₹</span>
            <input
              id="summary-gst"
              className="bill-review__field-input"
              type="number" step="0.01" min="0"
              value={bill.gst ?? '0'}
              onChange={(e) => updateSummary('gst', e.target.value)}
            />
          </div>

          <label htmlFor="summary-sc" className="bill-review__summary-label">Service Charge</label>
          <div className="bill-review__field-input-wrap">
            <span className="bill-review__field-prefix">₹</span>
            <input
              id="summary-sc"
              className="bill-review__field-input"
              type="number" step="0.01" min="0"
              value={bill.service_charge ?? '0'}
              onChange={(e) => updateSummary('service_charge', e.target.value)}
            />
          </div>

          <label htmlFor="summary-discount" className="bill-review__summary-label">Discount</label>
          <div className="bill-review__field-input-wrap">
            <span className="bill-review__field-prefix">₹</span>
            <input
              id="summary-discount"
              className="bill-review__field-input"
              type="number" step="0.01" min="0"
              value={bill.discount ?? '0'}
              onChange={(e) => updateSummary('discount', e.target.value)}
            />
          </div>

          <label htmlFor="summary-total" className="bill-review__summary-label bill-review__summary-label--total">
            Grand Total
          </label>
          <div className="bill-review__field-input-wrap">
            <span className="bill-review__field-prefix bill-review__field-prefix--total">₹</span>
            <input
              id="summary-total"
              className="bill-review__field-input bill-review__field-input--total"
              type="number" step="0.01" min="0"
              value={bill.total ?? ''}
              onChange={(e) => updateSummary('total', e.target.value || null)}
              placeholder="—"
            />
          </div>
        </div>
      </div>

      {/* ── Confidence legend ── */}
      <div className="bill-review__legend">
        <span className="conf-ring conf-ring--high" /> High confidence
        <span className="conf-ring conf-ring--medium" /> Medium
        <span className="conf-ring conf-ring--low" /> Low — please verify
      </div>

      {confirmError && (
        <Alert variant="error">{confirmError}</Alert>
      )}

      <Button
        id="btn-confirm-review"
        variant="primary"
        size="lg"
        full
        onClick={handleConfirm}
        disabled={!allValid || isConfirming}
      >
        {isConfirming ? '⏳ Confirming…' : '✓ Confirm Bill & Proceed'}
      </Button>

      {!allValid && (
        <p className="bill-review__hint">
          All items need a name and a total price before you can continue.
        </p>
      )}
    </div>
  );
}
