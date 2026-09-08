"""
Tax Split: Proportional GST allocation.

Rule: person_gst[person_id] = share[person_id] × bill.gst
where share[person_id] = person_subtotal[person_id] / total_food
"""
from decimal import Decimal

from app.utils.decimal_utils import ZERO


def calculate_consumption_shares(
    person_subtotals: dict[str, Decimal],
) -> dict[str, Decimal]:
    """
    Compute each person's share of total food spend.

    Returns {person_id: share} where share is in [0, 1] and all shares sum to 1.
    Returns equal shares if total_food == 0 (edge case).
    """
    total_food = sum(person_subtotals.values(), ZERO)
    if total_food == ZERO:
        # No food assigned — equal shares (prevents division by zero)
        n = len(person_subtotals)
        if n == 0:
            return {}
        equal = Decimal("1") / Decimal(n)
        return {pid: equal for pid in person_subtotals}

    return {pid: subtotal / total_food for pid, subtotal in person_subtotals.items()}


def allocate_gst(
    consumption_shares: dict[str, Decimal],
    gst_total: Decimal,
) -> dict[str, Decimal]:
    """
    Distribute GST proportionally by consumption share.

    Args:
        consumption_shares: {person_id: share} — fractions summing to ~1.
        gst_total: Total GST from the bill.

    Returns:
        {person_id: gst_amount} — exact (unrounded) Decimal amounts.
    """
    if gst_total == ZERO:
        return {pid: ZERO for pid in consumption_shares}

    return {pid: share * gst_total for pid, share in consumption_shares.items()}
