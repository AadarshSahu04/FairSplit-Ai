"""
Decimal utilities: helpers for consistent Decimal usage throughout FairSplit AI.
"""
from decimal import ROUND_HALF_UP, Decimal

TWO_PLACES = Decimal("0.01")
ZERO = Decimal("0")


def to_decimal(value) -> Decimal:
    """Convert a string, int, or float to Decimal safely."""
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def round_currency(value: Decimal) -> Decimal:
    """Round a Decimal to 2 decimal places using ROUND_HALF_UP."""
    return value.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)


def format_inr(value: Decimal) -> str:
    """Format a Decimal as an Indian Rupee string, e.g. '₹123.45'."""
    return f"₹{value:.2f}"
