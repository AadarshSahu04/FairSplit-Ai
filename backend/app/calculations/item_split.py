"""
Item Split: Calculates per-person food subtotals from item assignments.

Rule: person_subtotal[person_id] += item.total_price × proportion
      for each (item_id, person_id, proportion) assignment tuple.
"""
from decimal import Decimal
from typing import NamedTuple

from app.utils.decimal_utils import ZERO


class AssignmentTuple(NamedTuple):
    """Lightweight input for the calculation engine (no Pydantic dependency)."""

    item_id: str
    person_id: str
    proportion: Decimal  # 0–1


class ItemPriceTuple(NamedTuple):
    item_id: str
    total_price: Decimal


def calculate_person_item_subtotals(
    assignments: list[AssignmentTuple],
    item_prices: dict[str, Decimal],  # {item_id: total_price}
) -> dict[str, Decimal]:
    """
    Return a dict mapping person_id → food subtotal (exact Decimal, not rounded).

    Args:
        assignments: List of (item_id, person_id, proportion) tuples.
        item_prices: Mapping from item_id to item total_price.

    Returns:
        {person_id: Decimal} — sum of (item.total_price × proportion) per person.

    Raises:
        ValueError: If an assignment references an unknown item_id.
        ValueError: If assignments for a single item do not sum to ≤ 1.
    """
    # Validate proportions per item (sum must not exceed 1)
    from collections import defaultdict

    proportion_sums: dict[str, Decimal] = defaultdict(Decimal)
    for a in assignments:
        if a.item_id not in item_prices:
            raise ValueError(f"Assignment references unknown item_id: {a.item_id!r}")
        proportion_sums[a.item_id] += a.proportion

    for item_id, total_prop in proportion_sums.items():
        if total_prop > Decimal("1.001"):  # tiny tolerance for float→Decimal conversion
            raise ValueError(
                f"Proportions for item {item_id!r} sum to {total_prop}, which exceeds 1."
            )

    # Calculate subtotals
    person_subtotals: dict[str, Decimal] = defaultdict(Decimal)
    for a in assignments:
        person_subtotals[a.person_id] += item_prices[a.item_id] * a.proportion

    return dict(person_subtotals)
