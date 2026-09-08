"""
Pytest configuration and shared fixtures for FairSplit AI backend tests.
"""
import uuid
from decimal import Decimal

import pytest

from app.models.bill import BillItem, ExtractedBill
from app.models.person import Person
from app.models.split import Assignment


# ── Reusable factory helpers ───────────────────────────────────────────────────


def make_item(
    name: str = "Test Item",
    quantity: str = "1",
    unit_price: str = "100.00",
    total_price: str = "100.00",
    confidence: float = 0.95,
) -> BillItem:
    return BillItem(
        id=str(uuid.uuid4()),
        name=name,
        quantity=Decimal(quantity),
        unit_price=Decimal(unit_price),
        total_price=Decimal(total_price),
        confidence=confidence,
    )


def make_person(name: str) -> Person:
    return Person(id=str(uuid.uuid4()), name=name)


def make_assignment(item: BillItem, person: Person, proportion: str) -> Assignment:
    return Assignment(item_id=item.id, person_id=person.id, proportion=Decimal(proportion))


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def alice() -> Person:
    return Person(id="alice-id", name="Alice")


@pytest.fixture
def bob() -> Person:
    return Person(id="bob-id", name="Bob")


@pytest.fixture
def item_biryani() -> BillItem:
    return BillItem(
        id="biryani-id",
        name="Chicken Biryani",
        quantity=Decimal("2"),
        unit_price=Decimal("250.00"),
        total_price=Decimal("500.00"),
    )


@pytest.fixture
def item_coke() -> BillItem:
    return BillItem(
        id="coke-id",
        name="Coke",
        quantity=Decimal("1"),
        unit_price=Decimal("60.00"),
        total_price=Decimal("60.00"),
    )


@pytest.fixture
def simple_bill(item_biryani: BillItem, item_coke: BillItem) -> ExtractedBill:
    """Bill: 2× Biryani (₹500) + 1× Coke (₹60) = ₹560 subtotal.
    GST ₹50.40, service charge ₹28, discount ₹0, total ₹638.40."""
    return ExtractedBill(
        items=[item_biryani, item_coke],
        subtotal=Decimal("560.00"),
        gst=Decimal("50.40"),
        service_charge=Decimal("28.00"),
        discount=Decimal("0"),
        total=Decimal("638.40"),
    )
