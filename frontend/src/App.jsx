/**
 * App.jsx — FairSplit AI application shell.
 *
 * Orchestrates all sections via useBillState.
 * No financial logic here — all calculations are backend-derived.
 */
import './styles/global.css';
import './App.css';
import './components/ui/ui.css';
import { useBillState, STEP } from './hooks/useBillState.js';
import { BillUploader }    from './components/BillUploader/BillUploader.jsx';
import { BillReview }      from './components/BillReview/BillReview.jsx';
import { PeopleSelector }  from './components/PeopleSelector/PeopleSelector.jsx';
import { ItemAssignment }  from './components/ItemAssignment/ItemAssignment.jsx';
import { FinalBreakdown }  from './components/FinalBreakdown/FinalBreakdown.jsx';

// ── Stepper config ──────────────────────────────────────────────
const STEPS = [
  { id: STEP.UPLOAD, label: 'Upload',  icon: '📤' },
  { id: STEP.REVIEW, label: 'Review',  icon: '🔍' },
  { id: STEP.PEOPLE, label: 'People',  icon: '👥' },
  { id: STEP.ASSIGN, label: 'Assign',  icon: '🍽️' },
  { id: STEP.RESULT, label: 'Result',  icon: '💰' },
];

function Stepper({ currentStep, goToStep, maxReachable }) {
  return (
    <nav className="stepper" aria-label="Progress steps">
      {STEPS.map((step, idx) => {
        const isActive    = step.id === currentStep;
        const isCompleted = step.id < currentStep;
        const isReachable = step.id <= maxReachable;

        return (
          <div key={step.id} className="stepper__step-wrapper">
            <button
              type="button"
              className={[
                'stepper__step',
                isActive    ? 'stepper__step--active'    : '',
                isCompleted ? 'stepper__step--completed' : '',
              ].filter(Boolean).join(' ')}
              onClick={() => isReachable && goToStep(step.id)}
              disabled={!isReachable}
              aria-current={isActive ? 'step' : undefined}
            >
              <span className="stepper__icon">
                {isCompleted ? '✓' : step.icon}
              </span>
              <span className="stepper__label">{step.label}</span>
            </button>
            {idx < STEPS.length - 1 && (
              <div className={`stepper__connector ${isCompleted ? 'stepper__connector--done' : ''}`} />
            )}
          </div>
        );
      })}
    </nav>
  );
}

function SectionHeader({ stepNum, total, title, subtitle }) {
  return (
    <header className="section-header">
      <div className="section-header__counter">Step {stepNum}/{total}</div>
      <h2 className="section-header__title">{title}</h2>
      {subtitle && <p className="section-header__subtitle">{subtitle}</p>}
    </header>
  );
}

export default function App() {
  const state = useBillState();
  const {
    billImages,
    billData,
    reviewedBill,
    extractionStatus,
    extractionError,
    people,
    assignments,
    calculationResult,
    calculationStatus,
    calculationError,
    currentStep,
    addImages, removeImage, clearImages,
    runExtraction,
    updateReviewedBill, confirmReview,
    setPeopleList, confirmPeople,
    upsertAssignment,
    runCalculation,
    goToStep,
    reset,
  } = state;

  // How far the user has gotten (controls which stepper steps are clickable)
  const maxReachable = currentStep;

  return (
    <div className="app">
      {/* ── Header ── */}
      <header className="app__header">
        <div className="app__header-inner">
          <button className="app__logo" onClick={reset} type="button" aria-label="FairSplit AI — start over">
            <span className="app__logo-icon">⚖️</span>
            <span className="app__logo-text">FairSplit <span className="app__logo-ai">AI</span></span>
          </button>
          <p className="app__tagline">Split restaurant bills fairly, powered by AI</p>
        </div>
      </header>

      {/* ── Main content ── */}
      <main className="app__main">
        <div className="app__container">

          {/* ── Stepper ── */}
          <Stepper currentStep={currentStep} goToStep={goToStep} maxReachable={maxReachable} />

          {/* ── Sections ── */}
          <div className="app__section">

            {/* ── Step 0: Upload ── */}
            {currentStep === STEP.UPLOAD && (
              <>
                <SectionHeader
                  stepNum={1} total={5}
                  title="Upload Your Bill"
                  subtitle="Photograph your restaurant bill — we'll extract all the items automatically."
                />
                <BillUploader
                  billImages={billImages}
                  addImages={addImages}
                  removeImage={removeImage}
                  runExtraction={runExtraction}
                  extractionStatus={extractionStatus}
                  extractionError={extractionError}
                />
              </>
            )}

            {/* ── Step 1: Review ── */}
            {currentStep === STEP.REVIEW && reviewedBill && (
              <>
                <SectionHeader
                  stepNum={2} total={5}
                  title="Review Extracted Bill"
                  subtitle="Verify the AI-extracted items are correct before splitting."
                />
                <BillReview
                  reviewedBill={reviewedBill}
                  confirmReview={confirmReview}
                />
              </>
            )}

            {/* ── Step 2: People ── */}
            {currentStep === STEP.PEOPLE && (
              <>
                <SectionHeader
                  stepNum={3} total={5}
                  title="Who's at the Table?"
                  subtitle="Select the number of diners and enter their names."
                />
                <PeopleSelector
                  people={people}
                  setPeopleList={setPeopleList}
                  confirmPeople={confirmPeople}
                />
              </>
            )}

            {/* ── Step 3: Assign ── */}
            {currentStep === STEP.ASSIGN && reviewedBill && (
              <>
                <SectionHeader
                  stepNum={4} total={5}
                  title="Assign Items"
                  subtitle="Tap the people who shared each item. Equal shares are set automatically."
                />
                <ItemAssignment
                  reviewedBill={reviewedBill}
                  people={people}
                  assignments={assignments}
                  upsertAssignment={upsertAssignment}
                  runCalculation={runCalculation}
                  calculationStatus={calculationStatus}
                  calculationError={calculationError}
                />
              </>
            )}

            {/* ── Step 4: Result ── */}
            {currentStep === STEP.RESULT && calculationResult && (
              <>
                <SectionHeader
                  stepNum={5} total={5}
                  title="Your Fair Split"
                  subtitle="Here's exactly what each person owes — with taxes split proportionally."
                />
                <FinalBreakdown
                  calculationResult={calculationResult}
                  reset={reset}
                />
              </>
            )}

          </div>
        </div>
      </main>

      {/* ── Footer ── */}
      <footer className="app__footer">
        <p>
          FairSplit AI — AI reads the bill.{' '}
          <span className="text-accent">Python calculates the money.</span>
        </p>
      </footer>
    </div>
  );
}
