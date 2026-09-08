"""
Rounding: Largest Remainder Method for deterministic per-person rounding.

Guarantees: sum(rounded_person_finals) == calculated_total exactly.

Algorithm:
  1. Compute exact Decimal person final amounts.
  2. Floor each to 2 decimal places.
  3. Compute remainders for each person.
  4. Compute total_remainder = calculated_total - sum(floored values).
  5. Sort persons by remainder descending.
  6. Add ₹0.01 to top N persons where N = total_remainder * 100 (integer).
  7. Assert sum equals calculated_total.
"""
from decimal import ROUND_DOWN, Decimal

from app.utils.decimal_utils import ZERO


def apply_largest_remainder_rounding(
    person_finals: dict[str, Decimal],
    calculated_total: Decimal,
) -> dict[str, Decimal]:
    """
    Round per-person final amounts using the Largest Remainder Method.

    Args:
        person_finals: {person_id: exact_final_amount} (unrounded Decimal).
        calculated_total: The exact target total all finals must sum to.

    Returns:
        {person_id: rounded_amount} — guaranteed to sum to calculated_total.

    Raises:
        AssertionError: If post-rounding sum does not equal calculated_total.
    """
    TWO = Decimal("0.01")

    if not person_finals:
        return {}

    # Step 1: Floor each value to 2 decimal places
    floored: dict[str, Decimal] = {}
    remainders: dict[str, Decimal] = {}
    for pid, exact in person_finals.items():
        fl = exact.quantize(TWO, rounding=ROUND_DOWN)
        floored[pid] = fl
        remainders[pid] = exact - fl

    # Step 2: Compute how many pennies need to be distributed
    floored_total = sum(floored.values(), ZERO)
    total_remainder = (calculated_total - floored_total).quantize(TWO)
    num_extra_pennies = int(round(float(total_remainder) * 100))

    # Step 3: Sort by remainder descending, then by person_id for determinism
    sorted_pids = sorted(remainders.keys(), key=lambda p: (-remainders[p], p))

    rounded: dict[str, Decimal] = dict(floored)
    for i in range(num_extra_pennies):
        pid = sorted_pids[i % len(sorted_pids)]
        rounded[pid] += TWO

    # Step 4: Assert correctness
    final_sum = sum(rounded.values(), ZERO)
    assert final_sum == calculated_total, (
        f"Rounding error: sum {final_sum} != calculated_total {calculated_total}"
    )

    return rounded
