"""
Tests for app.models — BillItem, ExtractedBill, Person, Assignment, SplitResult.
"""
import uuid
from decimal import Decimal

import pytest

from app.models.bill import BillItem, ExtractedBill
from app.models.person import Person
from app.models.split import Assignment, PersonBreakdown, SplitRequest, SplitResult, ItemShare


class TestBillItem:
    def test_valid_item(self):
        item = BillItem(
            id="abc",
            name="Biryani",
            quantity=Decimal("2"),
            unit_price=Decimal("250"),
            total_price=Decimal("500"),
        )
        assert item.name == "Biryani"
        assert item.needs_review is False

    def test_arithmetic_mismatch_flags_needs_review(self):
        """If quantity × unit_price ≠ total_price, needs_review must be True."""
        item = BillItem(
            id="abc",
            name="Mystery Item",
            quantity=Decimal("2"),
            unit_price=Decimal("100"),
            total_price=Decimal("250"),  # should be 200
        )
        assert item.needs_review is True

    def test_arithmetic_ok_no_flag(self):
        item = BillItem(
            id="abc",
            name="Naan",
            quantity=Decimal("3"),
            unit_price=Decimal("40"),
            total_price=Decimal("120"),
        )
        assert item.needs_review is False

    def test_low_confidence_does_not_auto_flag(self):
        """Low confidence alone does NOT set needs_review; only arithmetic mismatch does."""
        item = BillItem(
            id="abc",
            name="Unclear item",
            quantity=Decimal("1"),
            unit_price=Decimal("50"),
            total_price=Decimal("50"),
            confidence=0.5,
            needs_review=False,
        )
        assert item.needs_review is False

    def test_negative_total_price_rejected(self):
        with pytest.raises(Exception):
            BillItem(
                id="abc",
                name="Bad",
                quantity=Decimal("1"),
                unit_price=Decimal("50"),
                total_price=Decimal("-10"),
            )


class TestExtractedBill:
    def test_empty_bill(self):
        bill = ExtractedBill()
        assert bill.items == []
        assert bill.gst == Decimal("0")
        assert bill.total is None

    def test_bill_with_items(self):
        item = BillItem(
            id="x",
            name="Pizza",
            quantity=Decimal("1"),
            unit_price=Decimal("300"),
            total_price=Decimal("300"),
        )
        bill = ExtractedBill(items=[item], gst=Decimal("27"), total=Decimal("327"))
        assert len(bill.items) == 1
        assert bill.total == Decimal("327")


class TestPerson:
    def test_valid_person(self):
        p = Person(id="abc", name="Alice")
        assert p.name == "Alice"

    def test_empty_name_rejected(self):
        with pytest.raises(Exception):
            Person(id="abc", name="")


class TestAssignment:
    def test_valid_assignment(self):
        a = Assignment(item_id="i1", person_id="p1", proportion=Decimal("0.5"))
        assert a.proportion == Decimal("0.5")

    def test_proportion_above_1_rejected(self):
        with pytest.raises(Exception):
            Assignment(item_id="i1", person_id="p1", proportion=Decimal("1.5"))

    def test_proportion_negative_rejected(self):
        with pytest.raises(Exception):
            Assignment(item_id="i1", person_id="p1", proportion=Decimal("-0.1"))
