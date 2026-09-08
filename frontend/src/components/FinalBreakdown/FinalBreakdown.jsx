/**
 * FinalBreakdown.jsx — Per-person result cards with full charge breakdown.
 */
import { Alert, Button, Card } from '../ui/index.jsx';
import { formatINR } from '../../utils/formatCurrency.js';
import './FinalBreakdown.css';

export function FinalBreakdown({ calculationResult, reset }) {
  if (!calculationResult) return null;

  const { people, calculated_total, printed_total, balanced, mismatch_amount } = calculationResult;

  return (
    <div className="breakdown">
      {/* ── Mismatch warning ── */}
      {!balanced && mismatch_amount != null && (
        <Alert variant="warning">
          <strong>Total mismatch detected.</strong> Calculated total is{' '}
          <strong>{formatINR(calculated_total)}</strong> but the printed bill shows{' '}
          <strong>{formatINR(printed_total)}</strong> (difference:{' '}
          {formatINR(Math.abs(parseFloat(mismatch_amount)))}). This may be due to a rounding
          difference or an OCR error — please verify the original bill.
        </Alert>
      )}

      {/* ── Total ── */}
      <div className="breakdown__total-banner">
        <span className="breakdown__total-label">Grand Total</span>
        <span className="breakdown__total-amount">{formatINR(calculated_total)}</span>
        {balanced && <span className="breakdown__total-badge">✓ Balanced</span>}
      </div>

      {/* ── Person cards ── */}
      <div className="breakdown__cards">
        {people.map((pb) => (
          <Card key={pb.person.id} className="breakdown__card">
            <div className="breakdown__card-header">
              <div className="breakdown__person-avatar">
                {pb.person.name[0]?.toUpperCase() || '?'}
              </div>
              <div>
                <p className="breakdown__person-name">{pb.person.name}</p>
                <p className="breakdown__person-subtitle">
                  {pb.items.length} {pb.items.length === 1 ? 'item' : 'items'}
                </p>
              </div>
              <div className="breakdown__person-total">{formatINR(pb.final_amount)}</div>
            </div>

            <div className="breakdown__line-items">
              {pb.items.map((item, idx) => (
                <div key={idx} className="breakdown__line-item">
                  <span className="breakdown__line-item-name">
                    {item.item_name}
                    {parseFloat(item.proportion) < 1 && (
                      <span className="breakdown__line-item-proportion">
                        {' '}({Math.round(parseFloat(item.proportion) * 100)}%)
                      </span>
                    )}
                  </span>
                  <span>{formatINR(item.amount)}</span>
                </div>
              ))}
            </div>

            <div className="breakdown__charges">
              <div className="breakdown__charge-row">
                <span>Food subtotal</span>
                <span>{formatINR(pb.food_subtotal)}</span>
              </div>
              {parseFloat(pb.gst) > 0 && (
                <div className="breakdown__charge-row">
                  <span>GST (proportional)</span>
                  <span>{formatINR(pb.gst)}</span>
                </div>
              )}
              {parseFloat(pb.service_charge) > 0 && (
                <div className="breakdown__charge-row">
                  <span>Service charge</span>
                  <span>{formatINR(pb.service_charge)}</span>
                </div>
              )}
              {parseFloat(pb.discount) > 0 && (
                <div className="breakdown__charge-row breakdown__charge-row--discount">
                  <span>Discount</span>
                  <span>−{formatINR(pb.discount)}</span>
                </div>
              )}
              <div className="breakdown__charge-row breakdown__charge-row--total">
                <span>You pay</span>
                <span>{formatINR(pb.final_amount)}</span>
              </div>
            </div>
          </Card>
        ))}
      </div>

      <Button id="btn-start-over" variant="secondary" size="lg" full onClick={reset}>
        ↩ Split Another Bill
      </Button>
    </div>
  );
}
