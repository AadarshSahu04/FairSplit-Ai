"""
Tests for calculations.tax_split — allocate_gst() and calculate_consumption_shares().
"""
from decimal import Decimal

import pytest

from app.calculations.tax_split import allocate_gst, calculate_consumption_shares


class TestCalculateConsumptionShares:
    def test_equal_subtotals(self):
        subtotals = {"alice": Decimal("100"), "bob": Decimal("100")}
        shares = calculate_consumption_shares(subtotals)
        assert shares["alice"] == Decimal("0.5")
        assert shares["bob"] == Decimal("0.5")

    def test_unequal_subtotals(self):
        subtotals = {"alice": Decimal("300"), "bob": Decimal("100")}
        shares = calculate_consumption_shares(subtotals)
        assert shares["alice"] == Decimal("0.75")
        assert shares["bob"] == Decimal("0.25")

    def test_zero_subtotals_returns_equal_shares(self):
        subtotals = {"alice": Decimal("0"), "bob": Decimal("0")}
        shares = calculate_consumption_shares(subtotals)
        # Both get 0.5 (equal split when no food assigned)
        assert shares["alice"] == Decimal("0.5")
        assert shares["bob"] == Decimal("0.5")

    def test_shares_sum_to_one(self):
        subtotals = {"a": Decimal("333"), "b": Decimal("333"), "c": Decimal("334")}
        shares = calculate_consumption_shares(subtotals)
        total = sum(shares.values())
        assert abs(total - Decimal("1")) < Decimal("0.0001")


class TestAllocateGst:
    def test_proportional_gst(self):
        shares = {"alice": Decimal("0.75"), "bob": Decimal("0.25")}
        gst = allocate_gst(shares, Decimal("100"))
        assert gst["alice"] == Decimal("75")
        assert gst["bob"] == Decimal("25")

    def test_zero_gst(self):
        shares = {"alice": Decimal("0.5"), "bob": Decimal("0.5")}
        gst = allocate_gst(shares, Decimal("0"))
        assert gst["alice"] == Decimal("0")
        assert gst["bob"] == Decimal("0")

    def test_gst_amounts_sum_to_total(self):
        shares = {"a": Decimal("0.333333"), "b": Decimal("0.333333"), "c": Decimal("0.333334")}
        gst_total = Decimal("50.40")
        gst = allocate_gst(shares, gst_total)
        total = sum(gst.values())
        # Exact values; rounding happens later in total_calculator
        assert abs(total - gst_total) < Decimal("0.001")
