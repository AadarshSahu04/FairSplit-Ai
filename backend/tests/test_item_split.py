"""
Tests for calculations.item_split — calculate_person_item_subtotals().
"""
from decimal import Decimal

import pytest

from app.calculations.item_split import AssignmentTuple, calculate_person_item_subtotals


class TestCalculatePersonItemSubtotals:
    def test_single_person_single_item(self):
        assignments = [AssignmentTuple("item1", "alice", Decimal("1"))]
        prices = {"item1": Decimal("100")}
        result = calculate_person_item_subtotals(assignments, prices)
        assert result["alice"] == Decimal("100")

    def test_two_persons_split_item(self):
        assignments = [
            AssignmentTuple("item1", "alice", Decimal("0.5")),
            AssignmentTuple("item1", "bob", Decimal("0.5")),
        ]
        prices = {"item1": Decimal("200")}
        result = calculate_person_item_subtotals(assignments, prices)
        assert result["alice"] == Decimal("100")
        assert result["bob"] == Decimal("100")

    def test_two_items_different_persons(self):
        assignments = [
            AssignmentTuple("biryani", "alice", Decimal("1")),
            AssignmentTuple("coke",    "bob",   Decimal("1")),
        ]
        prices = {"biryani": Decimal("500"), "coke": Decimal("60")}
        result = calculate_person_item_subtotals(assignments, prices)
        assert result["alice"] == Decimal("500")
        assert result["bob"] == Decimal("60")

    def test_unequal_split(self):
        assignments = [
            AssignmentTuple("item1", "alice", Decimal("0.7")),
            AssignmentTuple("item1", "bob",   Decimal("0.3")),
        ]
        prices = {"item1": Decimal("100")}
        result = calculate_person_item_subtotals(assignments, prices)
        assert result["alice"] == Decimal("70")
        assert result["bob"] == Decimal("30")

    def test_unknown_item_id_raises(self):
        assignments = [AssignmentTuple("unknown", "alice", Decimal("1"))]
        prices = {"item1": Decimal("100")}
        with pytest.raises(ValueError, match="unknown item_id"):
            calculate_person_item_subtotals(assignments, prices)

    def test_proportions_exceed_1_raises(self):
        assignments = [
            AssignmentTuple("item1", "alice", Decimal("0.7")),
            AssignmentTuple("item1", "bob",   Decimal("0.7")),
        ]
        prices = {"item1": Decimal("100")}
        with pytest.raises(ValueError, match="exceed"):
            calculate_person_item_subtotals(assignments, prices)

    def test_empty_assignments_returns_empty(self):
        result = calculate_person_item_subtotals([], {"item1": Decimal("100")})
        assert result == {}

    def test_multiple_items_per_person(self):
        assignments = [
            AssignmentTuple("biryani", "alice", Decimal("1")),
            AssignmentTuple("naan",    "alice", Decimal("1")),
        ]
        prices = {"biryani": Decimal("300"), "naan": Decimal("40")}
        result = calculate_person_item_subtotals(assignments, prices)
        assert result["alice"] == Decimal("340")
