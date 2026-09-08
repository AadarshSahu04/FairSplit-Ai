"""
End-to-end integration tests for calculations.total_calculator — calculate_split().
Tests the full 8-step pipeline with representative bill scenarios.
"""
from decimal import Decimal

import pytest

from app.calculations.total_calculator import calculate_split
from app.models.bill import BillItem, ExtractedBill
from app.models.person import Person
from app.models.split import Assignment


# ── Fixtures ───────────────────────────────────────────────────────────────────


def make_item(id, name, qty, unit, total):
    return BillItem(
        id=id,
        name=name,
        quantity=Decimal(qty),
        unit_price=Decimal(unit),
        total_price=Decimal(total),
    )


ALICE = Person(id="alice", name="Alice")
BOB = Person(id="bob", name="Bob")


# ── Tests ──────────────────────────────────────────────────────────────────────


class TestCalculateSplit:
    def test_single_person_whole_bill(self):
        """One person takes everything — final == calculated total."""
        item = make_item("i1", "Biryani", "1", "500", "500")
        bill = ExtractedBill(
            items=[item],
            subtotal=Decimal("500"),
            gst=Decimal("45"),
            service_charge=Decimal("25"),
            discount=Decimal("0"),
            total=Decimal("570"),
        )
        assignments = [Assignment(item_id="i1", person_id="alice", proportion=Decimal("1"))]
        result = calculate_split(bill, [ALICE], assignments)

        assert len(result.people) == 1
        assert result.people[0].final_amount == Decimal("570")
        assert result.calculated_total == Decimal("570")
        assert result.balanced is True

    def test_two_person_even_split(self):
        """Two persons split one item 50-50; charges distributed equally."""
        item = make_item("i1", "Pizza", "1", "200", "200")
        bill = ExtractedBill(
            items=[item],
            subtotal=Decimal("200"),
            gst=Decimal("20"),
            service_charge=Decimal("10"),
            discount=Decimal("0"),
            total=Decimal("230"),
        )
        assignments = [
            Assignment(item_id="i1", person_id="alice", proportion=Decimal("0.5")),
            Assignment(item_id="i1", person_id="bob",   proportion=Decimal("0.5")),
        ]
        result = calculate_split(bill, [ALICE, BOB], assignments)

        alice_bd = next(p for p in result.people if p.person.id == "alice")
        bob_bd   = next(p for p in result.people if p.person.id == "bob")

        assert alice_bd.final_amount == bob_bd.final_amount
        assert alice_bd.final_amount + bob_bd.final_amount == result.calculated_total
        assert result.balanced is True

    def test_two_person_unequal_items(self):
        """Alice ate biryani (₹500), Bob drank coke (₹60). Charges split proportionally."""
        biryani = make_item("biryani", "Biryani", "1", "500", "500")
        coke    = make_item("coke",    "Coke",    "1",  "60",  "60")
        bill = ExtractedBill(
            items=[biryani, coke],
            subtotal=Decimal("560"),
            gst=Decimal("50.40"),
            service_charge=Decimal("28"),
            discount=Decimal("0"),
            total=Decimal("638.40"),
        )
        assignments = [
            Assignment(item_id="biryani", person_id="alice", proportion=Decimal("1")),
            Assignment(item_id="coke",    person_id="bob",   proportion=Decimal("1")),
        ]
        result = calculate_split(bill, [ALICE, BOB], assignments)

        # Alice has higher subtotal → higher charges
        alice = next(p for p in result.people if p.person.id == "alice")
        bob   = next(p for p in result.people if p.person.id == "bob")

        assert alice.food_subtotal == Decimal("500")
        assert bob.food_subtotal == Decimal("60")
        assert alice.gst > bob.gst
        assert alice.final_amount + bob.final_amount == result.calculated_total
        assert result.calculated_total == Decimal("638.40")
        assert result.balanced is True

    def test_discount_reduces_final_amounts(self):
        """A discount must reduce each person's final_amount."""
        item = make_item("i1", "Meal", "1", "400", "400")
        bill_no_discount = ExtractedBill(
            items=[item], subtotal=Decimal("400"),
            gst=Decimal("36"), service_charge=Decimal("20"),
            discount=Decimal("0"), total=Decimal("456"),
        )
        bill_with_discount = ExtractedBill(
            items=[item], subtotal=Decimal("400"),
            gst=Decimal("36"), service_charge=Decimal("20"),
            discount=Decimal("50"), total=Decimal("406"),
        )
        assignments = [Assignment(item_id="i1", person_id="alice", proportion=Decimal("1"))]

        r1 = calculate_split(bill_no_discount, [ALICE], assignments)
        r2 = calculate_split(bill_with_discount, [ALICE], assignments)

        assert r2.calculated_total < r1.calculated_total
        assert r2.people[0].discount == Decimal("50")

    def test_mismatch_detected(self):
        """If printed total differs by more than ₹0.01, balanced=False."""
        item = make_item("i1", "Item", "1", "200", "200")
        bill = ExtractedBill(
            items=[item], subtotal=Decimal("200"),
            gst=Decimal("18"), service_charge=Decimal("10"),
            discount=Decimal("0"),
            total=Decimal("999"),  # deliberately wrong
        )
        assignments = [Assignment(item_id="i1", person_id="alice", proportion=Decimal("1"))]
        result = calculate_split(bill, [ALICE], assignments)

        assert result.balanced is False
        assert result.mismatch_amount is not None

    def test_sum_of_finals_equals_calculated_total(self):
        """Rounding guarantee: sum of all person final amounts == calculated_total exactly."""
        item = make_item("i1", "Group meal", "3", "111.11", "333.33")
        bill = ExtractedBill(
            items=[item], subtotal=Decimal("333.33"),
            gst=Decimal("30"), service_charge=Decimal("15"),
            discount=Decimal("0"), total=Decimal("378.33"),
        )
        assignments = [
            Assignment(item_id="i1", person_id="alice", proportion=Decimal("0.333333")),
            Assignment(item_id="i1", person_id="bob",   proportion=Decimal("0.333333")),
        ]
        # Carol gets the remainder
        carol = Person(id="carol", name="Carol")
        assignments.append(
            Assignment(item_id="i1", person_id="carol", proportion=Decimal("0.333334"))
        )
        result = calculate_split(bill, [ALICE, BOB, carol], assignments)

        total_from_persons = sum(p.final_amount for p in result.people)
        assert total_from_persons == result.calculated_total

    def test_unknown_person_in_assignment_raises(self):
        item = make_item("i1", "Food", "1", "100", "100")
        bill = ExtractedBill(items=[item], subtotal=Decimal("100"),
                             gst=Decimal("0"), service_charge=Decimal("0"),
                             discount=Decimal("0"), total=Decimal("100"))
        assignments = [Assignment(item_id="i1", person_id="nobody", proportion=Decimal("1"))]
        with pytest.raises(ValueError, match="unknown person_id"):
            calculate_split(bill, [ALICE], assignments)
