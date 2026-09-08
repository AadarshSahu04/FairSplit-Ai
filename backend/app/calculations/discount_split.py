"""
Discount Split: Proportional bill-level discount allocation.

Rule: person_discount[person_id] = share[person_id] × bill.discount

Documented choice: Discount distributed proportionally by pre-discount
consumption share (standard for bill-level promotions).
"""
from decimal import Decimal

from app.utils.decimal_utils import ZERO


def allocate_discount(
    consumption_shares: dict[str, Decimal],
    discount_total: Decimal,
) -> dict[str, Decimal]:
    """
    Distribute discount proportionally by consumption share.

    Args:
        consumption_shares: {person_id: share} — fractions summing to ~1.
        discount_total: Total bill-level discount (positive value means reduction).

    Returns:
        {person_id: discount_amount} — each person's discount portion (positive = reduction).
    """
    if discount_total == ZERO:
        return {pid: ZERO for pid in consumption_shares}

    return {pid: share * discount_total for pid, share in consumption_shares.items()}
