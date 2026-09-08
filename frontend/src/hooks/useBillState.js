/**
 * useBillState.js — Central application state for FairSplit AI.
 *
 * Single hook owns all state. No Redux needed at MVP scale.
 * State flows strictly forward through numbered steps.
 */
import { useCallback, useState } from 'react';
import { extractBill, splitBill } from '../services/api';

// ── Step Constants ─────────────────────────────────────────────
export const STEP = {
  UPLOAD:    0,
  REVIEW:    1,
  PEOPLE:    2,
  ASSIGN:    3,
  RESULT:    4,
};

const INITIAL_STATE = {
  // Upload
  billImages:          [],      // File[]
  // Extraction
  billData:            null,    // ExtractedBill from API (raw AI output)
  extractionStatus:    'idle',  // 'idle'|'loading'|'success'|'error'
  extractionError:     null,    // string | null
  // Review
  reviewedBill:        null,    // ConfirmedBill (human-edited copy of billData)
  // People
  people:              [],      // { id, name }[]
  // Assignments
  assignments:         [],      // { item_id, person_id, proportion }[]
  // Calculation
  calculationStatus:   'idle',  // 'idle'|'loading'|'success'|'error'
  calculationError:    null,
  calculationResult:   null,    // SplitResult from API
  // Navigation
  currentStep:         STEP.UPLOAD,
};

export function useBillState() {
  const [state, setState] = useState(INITIAL_STATE);

  // ── Generic setter ───────────────────────────────────────────
  const patch = useCallback((updates) => {
    setState((prev) => ({ ...prev, ...updates }));
  }, []);

  // ── Step navigation ──────────────────────────────────────────
  const goToStep = useCallback((step) => {
    patch({ currentStep: step });
  }, [patch]);

  // ── Upload ───────────────────────────────────────────────────
  const addImages = useCallback((newFiles) => {
    setState((prev) => ({
      ...prev,
      billImages: [...prev.billImages, ...newFiles].slice(0, 4), // max 4 images
    }));
  }, []);

  const removeImage = useCallback((index) => {
    setState((prev) => ({
      ...prev,
      billImages: prev.billImages.filter((_, i) => i !== index),
    }));
  }, []);

  const clearImages = useCallback(() => {
    patch({ billImages: [], billData: null, extractionStatus: 'idle', extractionError: null });
  }, [patch]);

  // ── Extraction ───────────────────────────────────────────────
  const runExtraction = useCallback(async () => {
    if (state.billImages.length === 0) return;

    patch({ extractionStatus: 'loading', extractionError: null });

    try {
      const data = await extractBill(state.billImages);
      patch({
        billData:         data.bill,
        reviewedBill:     JSON.parse(JSON.stringify(data.bill)), // editable copy
        extractionStatus: 'success',
        currentStep:      STEP.REVIEW,
      });
    } catch (err) {
      patch({
        extractionStatus: 'error',
        extractionError:  err.message || 'Extraction failed. Please try again.',
      });
    }
  }, [state.billImages, patch]);

  // ── Review / Bill editing ────────────────────────────────────
  const confirmReview = useCallback((editedBill) => {
    // editedBill may be passed from the review UI (Phase 10) or omitted (uses existing reviewedBill)
    const bill = editedBill ?? state.reviewedBill;
    if (!bill) return;
    patch({ reviewedBill: bill, currentStep: STEP.PEOPLE });
  }, [state.reviewedBill, patch]);

  const updateReviewedBill = useCallback((updatedBill) => {
    patch({ reviewedBill: updatedBill });
  }, [patch]);

  // ── People ───────────────────────────────────────────────────
  const setPeopleList = useCallback((people) => {
    patch({ people, assignments: [] }); // Reset assignments when people change
  }, [patch]);

  const confirmPeople = useCallback(() => {
    if (state.people.length === 0) return;
    patch({ currentStep: STEP.ASSIGN });
  }, [state.people, patch]);

  // ── Assignments ──────────────────────────────────────────────
  const setAssignments = useCallback((assignments) => {
    patch({ assignments });
  }, [patch]);

  const upsertAssignment = useCallback((itemId, personId, proportion) => {
    setState((prev) => {
      const existing = prev.assignments.filter(
        (a) => !(a.item_id === itemId && a.person_id === personId)
      );
      const updated = proportion > 0
        ? [...existing, { item_id: itemId, person_id: personId, proportion }]
        : existing;
      return { ...prev, assignments: updated };
    });
  }, []);

  // ── Calculation ──────────────────────────────────────────────
  const runCalculation = useCallback(async () => {
    if (!state.reviewedBill || state.people.length === 0) return;

    patch({ calculationStatus: 'loading', calculationError: null });

    try {
      const result = await splitBill({
        bill:        state.reviewedBill,
        people:      state.people,
        assignments: state.assignments,
      });
      patch({
        calculationResult:  result,
        calculationStatus:  'success',
        currentStep:        STEP.RESULT,
      });
    } catch (err) {
      patch({
        calculationStatus: 'error',
        calculationError:  err.message || 'Calculation failed. Please try again.',
      });
    }
  }, [state.reviewedBill, state.people, state.assignments, patch]);

  // ── Reset ────────────────────────────────────────────────────
  const reset = useCallback(() => {
    setState(INITIAL_STATE);
  }, []);

  return {
    ...state,
    // Actions
    addImages,
    removeImage,
    clearImages,
    runExtraction,
    updateReviewedBill,
    confirmReview,
    setPeopleList,
    confirmPeople,
    upsertAssignment,
    setAssignments,
    runCalculation,
    goToStep,
    reset,
  };
}
