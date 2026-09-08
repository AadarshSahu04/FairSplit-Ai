"""
Pydantic models for bill data: BillItem and ExtractedBill.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, model_validator


class BillItem(BaseModel):
    """A single line item extracted from a restaurant bill."""

    id: str = Field(..., description="UUID — stable even for duplicate item names")
    name: str = Field(..., description="Item name exactly as printed on the bill")
    quantity: Decimal = Field(..., ge=Decimal("0"), description="Number of units")
    unit_price: Decimal = Field(..., ge=Decimal("0"), description="Price per unit")
    total_price: Decimal = Field(..., ge=Decimal("0"), description="quantity × unit_price (from bill)")
    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="AI confidence: ≥0.9 high, ≥0.7 medium, else low",
    )
    needs_review: bool = Field(
        default=False,
        description="True if AI flagged uncertainty OR arithmetic mismatch",
    )

    @model_validator(mode="after")
    def flag_arithmetic_mismatch(self) -> "BillItem":
        """Flag items where quantity × unit_price does not match total_price."""
        expected = (self.quantity * self.unit_price).quantize(Decimal("0.01"))
        if abs(expected - self.total_price) > Decimal("0.02"):
            self.needs_review = True
        return self


class ExtractedBill(BaseModel):
    """Full bill extracted from an image. All monetary values are Decimal."""

    items: list[BillItem] = Field(default_factory=list)
    subtotal: Optional[Decimal] = Field(
        default=None,
        description="Sum of all item total_prices. None if OCR could not read it.",
    )
    gst: Decimal = Field(default=Decimal("0"), ge=Decimal("0"), description="GST / tax amount")
    service_charge: Decimal = Field(
        default=Decimal("0"), ge=Decimal("0"), description="Service charge amount"
    )
    discount: Decimal = Field(
        default=Decimal("0"), ge=Decimal("0"), description="Bill-level discount (positive = reduction)"
    )
    total: Optional[Decimal] = Field(
        default=None,
        description="Grand total printed on bill. None if OCR could not determine.",
    )
    extraction_warnings: list[str] = Field(
        default_factory=list,
        description="Human-readable warnings from AI extraction or arithmetic checks",
    )
