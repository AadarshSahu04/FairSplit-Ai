/**
 * PeopleSelector + PersonList — combined people setup component.
 * Phase 6 will enhance the number selector with animation.
 */
import { useCallback } from 'react';
import { Button, Card } from '../ui/index.jsx';
import './PeopleSelector.css';

const MIN_PEOPLE = 1;
const MAX_PEOPLE = 15;

function generateId() {
  return `person-${Math.random().toString(36).slice(2, 9)}`;
}

export function PeopleSelector({ people, setPeopleList, confirmPeople }) {
  const count = people.length;

  const setCount = useCallback((n) => {
    const newCount = Math.max(MIN_PEOPLE, Math.min(MAX_PEOPLE, n));
    const current  = people.slice(0, newCount);
    const extras   = Array.from({ length: newCount - current.length }, (_, i) => ({
      id:   generateId(),
      name: `Person ${current.length + i + 1}`,
    }));
    setPeopleList([...current, ...extras]);
  }, [people, setPeopleList]);

  const updateName = useCallback((id, name) => {
    setPeopleList(people.map((p) => (p.id === id ? { ...p, name } : p)));
  }, [people, setPeopleList]);

  const allNamed = people.every((p) => p.name.trim().length > 0);

  return (
    <div className="people-selector">
      {/* ── Count Picker ── */}
      <div className="people-selector__picker">
        <button
          className="people-selector__stepper"
          onClick={() => setCount(count - 1)}
          disabled={count <= MIN_PEOPLE}
          aria-label="Remove person"
          type="button"
        >
          −
        </button>

        <div className="people-selector__count" aria-live="polite">
          <span className="people-selector__count-number">{count}</span>
          <span className="people-selector__count-label">
            {count === 1 ? 'person' : 'people'}
          </span>
        </div>

        <button
          className="people-selector__stepper"
          onClick={() => setCount(count + 1)}
          disabled={count >= MAX_PEOPLE}
          aria-label="Add person"
          type="button"
        >
          +
        </button>
      </div>

      {/* ── Name Inputs ── */}
      <div className="people-selector__names">
        {people.map((person, idx) => (
          <div key={person.id} className="people-selector__name-row">
            <div className="people-selector__avatar" aria-hidden="true">
              {person.name.trim()[0]?.toUpperCase() || '?'}
            </div>
            <input
              id={`person-name-${idx}`}
              className="input"
              type="text"
              value={person.name}
              onChange={(e) => updateName(person.id, e.target.value)}
              placeholder={`Person ${idx + 1}`}
              maxLength={32}
              aria-label={`Name for person ${idx + 1}`}
            />
          </div>
        ))}
      </div>

      <Button
        id="btn-confirm-people"
        variant="primary"
        size="lg"
        full
        onClick={confirmPeople}
        disabled={!allNamed || count === 0}
      >
        👥 Set Up Assignments →
      </Button>
    </div>
  );
}
