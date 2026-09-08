"""
Tests for calculations.discount_split — allocate_discount().
"""
from decimal import Decimal

import pytest

from app.calculations.discount_split import allocate_discount


class TestAllocateDiscount:
    def test_proportional_discount(self):
        shares = {"alice": Decimal("0.75"), "bob": Decimal("0.25")}
        result = allocate_discount(shares, Decimal("100"))
        assert result["alice"] == Decimal("75")
        assert result["bob"] == Decimal("25")

    def test_zero_discount(self):
        shares = {"alice": Decimal("0.5"), "bob": Decimal("0.5")}
        result = allocate_discount(shares, Decimal("0"))
        assert result["alice"] == Decimal("0")
        assert result["bob"] == Decimal("0")

    def test_discount_amounts_are_positive(self):
        """Discount amounts are always positive (reduction), not negative."""
        shares = {"alice": Decimal("0.6"), "bob": Decimal("0.4")}
        result = allocate_discount(shares, Decimal("50"))
        assert result["alice"] > 0
        assert result["bob"] > 0

    def test_total_matches(self):
        shares = {"a": Decimal("0.5"), "b": Decimal("0.3"), "c": Decimal("0.2")}
        discount = Decimal("200")
        result = allocate_discount(shares, discount)
        total = sum(result.values())
        assert abs(total - discount) < Decimal("0.001")
