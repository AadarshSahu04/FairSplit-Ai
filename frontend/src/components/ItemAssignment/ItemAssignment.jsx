/**
 * ItemAssignment.jsx — Phase 7 placeholder.
 * Assign each bill item to one or more persons with proportion controls.
 */
import { useCallback } from 'react';
import { Button, Card } from '../ui/index.jsx';
import { formatINR } from '../../utils/formatCurrency.js';
import './ItemAssignment.css';

export function ItemAssignment({ reviewedBill, people, assignments, upsertAssignment, runCalculation, calculationStatus, calculationError }) {
  const items  = reviewedBill?.items ?? [];
  const isLoading = calculationStatus === 'loading';

  const getAssignment = useCallback((itemId, personId) => {
    return assignments.find((a) => a.item_id === itemId && a.person_id === personId);
  }, [assignments]);

  const togglePerson = useCallback((itemId, personId) => {
    const existing = getAssignment(itemId, personId);
    if (existing) {
      upsertAssignment(itemId, personId, 0); // remove
    } else {
      // Auto-assign equal share: 1 / (current assigned + 1)
      const currentlyAssigned = assignments.filter((a) => a.item_id === itemId && a.proportion > 0);
      const newTotal = currentlyAssigned.length + 1;
      const equalShare = 1 / newTotal;
      // Update all existing proportions
      currentlyAssigned.forEach((a) => upsertAssignment(a.item_id, a.person_id, equalShare));
      upsertAssignment(itemId, personId, equalShare);
    }
  }, [assignments, getAssignment, upsertAssignment]);

  // Validate: every item must have at least one assignment summing to ~1
  const allAssigned = items.every((item) => {
    const itemAssignments = assignments.filter((a) => a.item_id === item.id && a.proportion > 0);
    const total = itemAssignments.reduce((s, a) => s + a.proportion, 0);
    return itemAssignments.length > 0 && Math.abs(total - 1) < 0.01;
  });

  return (
    <div className="item-assignment">
      <div className="item-assignment__list">
        {items.map((item) => {
          const itemAssignments = assignments.filter((a) => a.item_id === item.id && a.proportion > 0);
          const assignedTotal = itemAssignments.reduce((s, a) => s + a.proportion, 0);
          const isFullyAssigned = itemAssignments.length > 0 && Math.abs(assignedTotal - 1) < 0.01;

          return (
            <Card key={item.id} className={`item-assignment__item ${isFullyAssigned ? 'item-assignment__item--done' : ''}`}>
              <div className="item-assignment__item-header">
                <div>
                  <span className="item-assignment__item-name">{item.name}</span>
                  <span className="item-assignment__item-price">{formatINR(item.total_price)}</span>
                </div>
                <div className="item-assignment__status">
                  {isFullyAssigned
                    ? <span className="item-assignment__status--done">✓ Assigned</span>
                    : <span className="item-assignment__status--pending">Unassigned</span>
                  }
                </div>
              </div>

              <div className="item-assignment__persons">
                {people.map((person) => {
                  const assignment = getAssignment(item.id, person.id);
                  const isActive   = assignment && assignment.proportion > 0;
                  return (
                    <button
                      key={person.id}
                      type="button"
                      className={`item-assignment__person-chip ${isActive ? 'item-assignment__person-chip--active' : ''}`}
                      onClick={() => togglePerson(item.id, person.id)}
                      aria-pressed={!!isActive}
                    >
                      {person.name}
                      {isActive && (
                        <span className="item-assignment__proportion">
                          {Math.round(assignment.proportion * 100)}%
                        </span>
                      )}
                    </button>
                  );
                })}
              </div>
            </Card>
          );
        })}
      </div>

      {calculationError && (
        <p className="item-assignment__error">{calculationError}</p>
      )}

      <Button
        id="btn-calculate-split"
        variant="primary"
        size="lg"
        full
        onClick={runCalculation}
        disabled={!allAssigned || isLoading}
      >
        {isLoading ? '⏳ Calculating…' : '🧮 Calculate Split'}
      </Button>

      {!allAssigned && items.length > 0 && (
        <p className="item-assignment__hint">Assign all items to at least one person to continue.</p>
      )}
    </div>
  );
}
