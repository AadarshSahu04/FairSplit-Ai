"""
Total Calculator: Orchestrates all sub-calculation modules to produce SplitResult.

Pipeline:
  ValidatedBill + People + Assignments
    → item_split      → person_subtotals
    → tax_split       → consumption_shares, person_gst
    → service_split   → person_service_charge
    → discount_split  → person_discount
    → Step 6 formula  → person_finals (exact)
    → rounding        → person_finals (rounded, sum == calculated_total)
    → reconciliation  → compare vs printed total
    → SplitResult
"""
from __future__ import annotations

from decimal import Decimal
from typing import Any

from app.calculations.discount_split import allocate_discount
from app.calculations.item_split import AssignmentTuple, calculate_person_item_subtotals
from app.calculations.rounding import apply_largest_remainder_rounding
from app.calculations.service_split import allocate_service_charge
from app.calculations.tax_split import allocate_gst, calculate_consumption_shares
from app.models.bill import ExtractedBill
from app.models.person import Person
from app.models.split import Assignment, ItemShare, PersonBreakdown, SplitResult
from app.utils.decimal_utils import ZERO

MISMATCH_TOLERANCE = Decimal("0.01")


def calculate_split(
    bill: ExtractedBill,
    people: list[Person],
    assignments: list[Assignment],
) -> SplitResult:
    """
    Main entry point: compute a full SplitResult from a validated bill + assignments.

    Args:
        bill: Human-confirmed ExtractedBill.
        people: List of Person objects (at least one).
        assignments: Per-item consumption assignments.

    Returns:
        SplitResult with per-person breakdown and total reconciliation.

    Raises:
        ValueError: If assignments reference unknown item or person IDs.
        AssertionError: If internal rounding fails (should never happen in practice).
    """
    person_map: dict[str, Person] = {p.id: p for p in people}
    item_price_map: dict[str, Decimal] = {item.id: item.total_price for item in bill.items}
    item_name_map: dict[str, str] = {item.id: item.name for item in bill.items}

    # Validate person IDs in assignments
    for a in assignments:
        if a.person_id not in person_map:
            raise ValueError(f"Assignment references unknown person_id: {a.person_id!r}")

    # ── Step 1: Person item subtotals ──────────────────────────────────────────
    assignment_tuples = [
        AssignmentTuple(
            item_id=a.item_id,
            person_id=a.person_id,
            proportion=a.proportion,
        )
        for a in assignments
    ]
    person_subtotals = calculate_person_item_subtotals(assignment_tuples, item_price_map)

    # Ensure all persons have an entry (even unassigned persons get 0)
    for pid in person_map:
        person_subtotals.setdefault(pid, ZERO)

    # ── Step 2: Consumption shares ─────────────────────────────────────────────
    consumption_shares = calculate_consumption_shares(person_subtotals)

    # ── Step 3: GST ────────────────────────────────────────────────────────────
    person_gst = allocate_gst(consumption_shares, bill.gst)

    # ── Step 4: Service charge ─────────────────────────────────────────────────
    person_service = allocate_service_charge(consumption_shares, bill.service_charge)

    # ── Step 5: Discount ───────────────────────────────────────────────────────
    person_discount = allocate_discount(consumption_shares, bill.discount)

    # ── Step 6: Exact person finals ────────────────────────────────────────────
    person_finals_exact: dict[str, Decimal] = {
        pid: (
            person_subtotals[pid]
            + person_gst.get(pid, ZERO)
            + person_service.get(pid, ZERO)
            - person_discount.get(pid, ZERO)
        )
        for pid in person_map
    }

    # ── Step 7: Calculated total ───────────────────────────────────────────────
    calculated_total = sum(person_subtotals.values(), ZERO) + bill.gst + bill.service_charge - bill.discount

    # ── Step 8: Rounding (Largest Remainder Method) ────────────────────────────
    person_finals_rounded = apply_largest_remainder_rounding(person_finals_exact, calculated_total)

    # ── Step 9: Total reconciliation ───────────────────────────────────────────
    printed_total = bill.total
    balanced: bool
    mismatch_amount: Decimal | None = None

    if printed_total is not None:
        diff = abs(calculated_total - printed_total)
        balanced = diff <= MISMATCH_TOLERANCE
        if not balanced:
            mismatch_amount = calculated_total - printed_total
    else:
        balanced = True  # Cannot check without a printed total

    # ── Assemble per-person item shares for the breakdown UI ──────────────────
    person_item_shares: dict[str, list[ItemShare]] = {pid: [] for pid in person_map}
    for a in assignments:
        if a.proportion > ZERO:
            person_item_shares[a.person_id].append(
                ItemShare(
                    item_id=a.item_id,
                    item_name=item_name_map.get(a.item_id, "Unknown"),
                    proportion=a.proportion,
                    amount=item_price_map[a.item_id] * a.proportion,
                )
            )

    # ── Build PersonBreakdown list ─────────────────────────────────────────────
    breakdowns: list[PersonBreakdown] = []
    for pid, person in person_map.items():
        final = person_finals_rounded[pid]
        breakdowns.append(
            PersonBreakdown(
                person=person,
                items=person_item_shares.get(pid, []),
                food_subtotal=person_subtotals[pid],
                gst=person_gst.get(pid, ZERO),
                service_charge=person_service.get(pid, ZERO),
                discount=person_discount.get(pid, ZERO),
                final_amount=final,
            )
        )

    return SplitResult(
        people=breakdowns,
        calculated_total=calculated_total,
        printed_total=printed_total,
        balanced=balanced,
        mismatch_amount=mismatch_amount,
    )
