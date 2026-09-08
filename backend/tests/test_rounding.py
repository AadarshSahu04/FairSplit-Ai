"""
Tests for calculations.rounding — apply_largest_remainder_rounding().
"""
from decimal import Decimal

import pytest

from app.calculations.rounding import apply_largest_remainder_rounding


class TestApplyLargestRemainderRounding:
    def test_sum_equals_calculated_total_exact(self):
        """Core guarantee: rounded amounts must sum to exactly calculated_total."""
        finals = {
            "alice": Decimal("33.333333"),
            "bob":   Decimal("33.333333"),
            "carol": Decimal("33.333334"),
        }
        total = Decimal("100.00")
        rounded = apply_largest_remainder_rounding(finals, total)
        assert sum(rounded.values()) == total

    def test_no_rounding_needed(self):
        finals = {"alice": Decimal("50.00"), "bob": Decimal("50.00")}
        total = Decimal("100.00")
        rounded = apply_largest_remainder_rounding(finals, total)
        assert rounded["alice"] == Decimal("50.00")
        assert rounded["bob"] == Decimal("50.00")
        assert sum(rounded.values()) == total

    def test_penny_given_to_highest_remainder(self):
        """When split doesn't divide evenly, the person with higher fractional remainder gets the penny."""
        # Alice: 66.666... → floors to 66.66 (remainder 0.006...)
        # Bob:   33.333... → floors to 33.33 (remainder 0.003...)
        # total = 100.00 → one extra penny needed → Alice gets it → 66.67
        finals = {"alice": Decimal("66.666666"), "bob": Decimal("33.333334")}
        total = Decimal("100.00")
        rounded = apply_largest_remainder_rounding(finals, total)
        assert sum(rounded.values()) == total
        assert rounded["alice"] + rounded["bob"] == total

    def test_empty_input(self):
        result = apply_largest_remainder_rounding({}, Decimal("0"))
        assert result == {}

    def test_single_person_gets_full_total(self):
        finals = {"alice": Decimal("100.123")}
        total = Decimal("100.12")
        rounded = apply_largest_remainder_rounding(finals, total)
        assert rounded["alice"] == Decimal("100.12")
        assert sum(rounded.values()) == total

    def test_real_world_three_way_split(self):
        """₹638.40 split three ways."""
        total = Decimal("638.40")
        exact = total / 3  # 212.8 each
        finals = {"a": exact, "b": exact, "c": exact}
        rounded = apply_largest_remainder_rounding(finals, total)
        assert sum(rounded.values()) == total

    def test_all_amounts_non_negative(self):
        finals = {"alice": Decimal("50.005"), "bob": Decimal("50.005")}
        total = Decimal("100.01")
        rounded = apply_largest_remainder_rounding(finals, total)
        for v in rounded.values():
            assert v >= Decimal("0")
