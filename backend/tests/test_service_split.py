"""
Tests for calculations.service_split — allocate_service_charge().
"""
from decimal import Decimal

import pytest

from app.calculations.service_split import allocate_service_charge


class TestAllocateServiceCharge:
    def test_proportional_service(self):
        shares = {"alice": Decimal("0.5"), "bob": Decimal("0.5")}
        result = allocate_service_charge(shares, Decimal("100"))
        assert result["alice"] == Decimal("50")
        assert result["bob"] == Decimal("50")

    def test_zero_service_charge(self):
        shares = {"alice": Decimal("0.8"), "bob": Decimal("0.2")}
        result = allocate_service_charge(shares, Decimal("0"))
        assert result["alice"] == Decimal("0")
        assert result["bob"] == Decimal("0")

    def test_unequal_distribution(self):
        shares = {"alice": Decimal("0.8"), "bob": Decimal("0.2")}
        result = allocate_service_charge(shares, Decimal("50"))
        assert result["alice"] == Decimal("40")
        assert result["bob"] == Decimal("10")

    def test_total_matches(self):
        shares = {"a": Decimal("0.333"), "b": Decimal("0.333"), "c": Decimal("0.334")}
        sc_total = Decimal("30")
        result = allocate_service_charge(shares, sc_total)
        total = sum(result.values())
        assert abs(total - sc_total) < Decimal("0.01")
