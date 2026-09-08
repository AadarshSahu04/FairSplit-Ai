"""
Extraction Service: Converts raw Gemini Vision JSON output into a validated Pydantic ExtractedBill.

Responsibilities:
  1. Map raw dict fields to BillItem / ExtractedBill Pydantic models.
  2. Generate stable UUIDs for any items missing an id.
  3. Handle null / missing fields gracefully (use defaults, flag for review).
  4. Build extraction_warnings list from per-item warnings + overall notes.
  5. Set needs_review = True for low-confidence items (< 0.7) or items with extracted warnings.

Phase 9 implementation.
"""
from __future__ import annotations

import logging
import uuid
from decimal import Decimal, InvalidOperation

from app.models.bill import BillItem, ExtractedBill
from app.utils.decimal_utils import ZERO, to_decimal

logger = logging.getLogger(__name__)

# Confidence threshold below which needs_review is forced True
LOW_CONFIDENCE_THRESHOLD: float = 0.70


# ── Public API ────────────────────────────────────────────────────────────────

def parse_extraction_result(raw: dict) -> ExtractedBill:
    """
    Convert a raw Gemini extraction dict into a validated ExtractedBill.

    Args:
        raw: Dict parsed from Gemini JSON response.

    Returns:
        ExtractedBill with BillItem list and summary charges.

    Raises:
        ValueError: If "items" key is missing or not a list.
    """
    if not isinstance(raw.get("items"), list):
        raise ValueError(
            "Gemini extraction result missing 'items' list. "
            "The model may have returned an unexpected format."
        )

    warnings: list[str] = []

    # ── Overall extraction notes ───────────────────────────────────────────────
    notes = raw.get("extraction_notes") or ""
    if notes and notes.strip():
        warnings.append(f"AI note: {notes.strip()}")

    # ── Parse items ───────────────────────────────────────────────────────────
    items: list[BillItem] = []
    for idx, raw_item in enumerate(raw["items"]):
        item, item_warnings = _parse_item(raw_item, idx)
        items.append(item)
        warnings.extend(item_warnings)

    # ── Parse summary charges ─────────────────────────────────────────────────
    subtotal       = _to_decimal_or_none(raw.get("subtotal"),       "subtotal",       warnings)
    gst            = _to_decimal_or_zero(raw.get("gst"),            "gst",            warnings)
    service_charge = _to_decimal_or_zero(raw.get("service_charge"), "service_charge", warnings)
    discount       = _to_decimal_or_zero(raw.get("discount"),       "discount",       warnings)
    total          = _to_decimal_or_none(raw.get("total"),          "total",          warnings)

    return ExtractedBill(
        items=items,
        subtotal=subtotal,
        gst=gst,
        service_charge=service_charge,
        discount=discount,
        total=total,
        extraction_warnings=warnings,
    )


# ── Private helpers ───────────────────────────────────────────────────────────

def _parse_item(raw_item: dict, idx: int) -> tuple[BillItem, list[str]]:
    """Parse a single raw item dict into a BillItem + list of warnings."""
    warnings: list[str] = []

    # ── ID ────────────────────────────────────────────────────────────────────
    item_id = str(raw_item.get("id") or uuid.uuid4())

    # ── Name ─────────────────────────────────────────────────────────────────
    name = str(raw_item.get("name") or f"Item {idx + 1}").strip()

    # ── Confidence ───────────────────────────────────────────────────────────
    try:
        confidence = float(raw_item.get("confidence", 1.0))
        confidence = max(0.0, min(1.0, confidence))
    except (TypeError, ValueError):
        confidence = 1.0

    # ── Quantity ─────────────────────────────────────────────────────────────
    quantity = _to_decimal_or_one(raw_item.get("quantity"), name, warnings, "quantity")

    # ── Unit price ───────────────────────────────────────────────────────────
    # If unit_price is null, derive it: total / quantity (when both are available)
    raw_unit = raw_item.get("unit_price")
    raw_total = raw_item.get("total_price")

    total_price = _to_decimal_required(raw_total, name, warnings)
    if raw_unit is None and total_price > ZERO and quantity > ZERO:
        unit_price = (total_price / quantity).quantize(Decimal("0.01"))
    else:
        unit_price = _to_decimal_or_zero(raw_unit, f"{name} unit_price", warnings)

    # ── Item warning ─────────────────────────────────────────────────────────
    item_warning = raw_item.get("warning") or ""
    needs_review = (confidence < LOW_CONFIDENCE_THRESHOLD) or bool(item_warning.strip())

    if item_warning.strip():
        warnings.append(f'"{name}": {item_warning.strip()}')

    if confidence < LOW_CONFIDENCE_THRESHOLD:
        warnings.append(
            f'"{name}" has low confidence ({confidence:.0%}) — please verify.'
        )

    bill_item = BillItem(
        id=item_id,
        name=name,
        quantity=quantity,
        unit_price=unit_price,
        total_price=total_price,
        confidence=confidence,
        needs_review=needs_review,
    )
    return bill_item, warnings


# ── Decimal coercion helpers ──────────────────────────────────────────────────

def _to_decimal_or_none(value, field_name: str, warnings: list[str]) -> Decimal | None:
    if value is None:
        return None
    try:
        return to_decimal(value)
    except InvalidOperation:
        warnings.append(f"Could not parse '{field_name}' value ({value!r}) — treated as null.")
        return None


def _to_decimal_or_zero(value, field_name: str, warnings: list[str]) -> Decimal:
    if value is None:
        return ZERO
    try:
        return max(ZERO, to_decimal(value))
    except InvalidOperation:
        warnings.append(f"Could not parse '{field_name}' value ({value!r}) — treated as 0.")
        return ZERO


def _to_decimal_or_one(value, item_name: str, warnings: list[str], field: str) -> Decimal:
    """Return Decimal for quantity, defaulting to 1 when absent."""
    if value is None:
        return Decimal("1")
    try:
        d = to_decimal(value)
        return d if d > ZERO else Decimal("1")
    except InvalidOperation:
        warnings.append(
            f'"{item_name}": could not parse {field} ({value!r}) — defaulted to 1.'
        )
        return Decimal("1")


def _to_decimal_required(value, item_name: str, warnings: list[str]) -> Decimal:
    """Return Decimal for total_price, defaulting to 0 when absent."""
    if value is None:
        warnings.append(f'"{item_name}": missing total_price — defaulted to 0.')
        return ZERO
    try:
        return max(ZERO, to_decimal(value))
    except InvalidOperation:
        warnings.append(
            f'"{item_name}": could not parse total_price ({value!r}) — defaulted to 0.'
        )
        return ZERO
