"""
Pydantic models for split request/response:
  Assignment, SplitRequest, PersonBreakdown, SplitResult.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field

from app.models.bill import ExtractedBill
from app.models.person import Person


class Assignment(BaseModel):
    """Maps a bill item to a person with a consumption proportion."""

    item_id: str = Field(..., description="ID of the BillItem")
    person_id: str = Field(..., description="ID of the Person")
    proportion: Decimal = Field(
        ...,
        ge=Decimal("0"),
        le=Decimal("1"),
        description="Fraction of the item this person owes (0–1, e.g. 0.6 = 60%)",
    )


class SplitRequest(BaseModel):
    """Complete request body for the /api/bill/split endpoint."""

    bill: ExtractedBill
    people: list[Person]
    assignments: list[Assignment]


class ItemShare(BaseModel):
    """A single item contributing to a person's food subtotal."""

    item_id: str
    item_name: str
    proportion: Decimal
    amount: Decimal  # item.total_price × proportion


class PersonBreakdown(BaseModel):
    """Per-person result with a full breakdown of charges."""

    person: Person
    items: list[ItemShare]
    food_subtotal: Decimal = Field(description="Sum of item shares before charges")
    gst: Decimal = Field(description="Proportional GST allocated to this person")
    service_charge: Decimal = Field(description="Proportional service charge")
    discount: Decimal = Field(description="Proportional discount (positive = reduction)")
    final_amount: Decimal = Field(description="food_subtotal + gst + service_charge - discount")


class SplitResult(BaseModel):
    """Complete split result returned by the calculation engine."""

    people: list[PersonBreakdown]
    calculated_total: Decimal = Field(description="Sum of all final_amounts")
    printed_total: Optional[Decimal] = Field(
        default=None, description="Total from the printed bill (may differ due to OCR or rounding)"
    )
    balanced: bool = Field(
        description="True if calculated_total equals printed_total within ₹0.01"
    )
    mismatch_amount: Optional[Decimal] = Field(
        default=None, description="calculated_total - printed_total if not balanced"
    )
