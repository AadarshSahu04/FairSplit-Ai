"""
Bill API routes: POST /api/bill/extract and POST /api/bill/validate.

Phase 9: Real Gemini Vision OCR wired to /extract.
"""
from decimal import Decimal

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel

from app.models.bill import ExtractedBill
from app.services.extraction_service import parse_extraction_result
from app.services.ocr_service import extract_bill_from_images

router = APIRouter()


# ── Response schemas ───────────────────────────────────────────────────────────


class ExtractResponse(BaseModel):
    bill: ExtractedBill
    warnings: list[str]


class ArithmeticChecks(BaseModel):
    items_sum_matches_subtotal: bool
    subtotal_plus_charges_matches_total: bool


class ValidateResponse(BaseModel):
    bill: ExtractedBill
    arithmetic_checks: ArithmeticChecks
    warnings: list[str]


class ValidateRequest(BaseModel):
    bill: ExtractedBill


# ── Routes ─────────────────────────────────────────────────────────────────────


@router.get("/ping")
async def ping():
    """Route health check."""
    return {"route": "bill", "status": "ok"}


@router.post("/extract", response_model=ExtractResponse)
async def extract_bill(images: list[UploadFile] = File(...)):
    """
    Upload bill image(s) and extract structured data using Gemini Vision OCR.

    Accepts 1–4 images (multipart/form-data, field name: 'images').
    Returns a validated ExtractedBill and any extraction warnings.
    """
    if not images:
        raise HTTPException(status_code=422, detail="At least one image is required.")
    if len(images) > 4:
        raise HTTPException(status_code=422, detail="Maximum 4 images per request.")

    # Read all image bytes
    raw_images: list[bytes] = []
    for upload in images:
        content_type = upload.content_type or ""
        if not content_type.startswith("image/"):
            raise HTTPException(
                status_code=422,
                detail=f"File '{upload.filename}' is not an image (got {content_type!r}).",
            )
        raw_bytes = await upload.read()
        if len(raw_bytes) == 0:
            raise HTTPException(
                status_code=422, detail=f"File '{upload.filename}' is empty."
            )
        raw_images.append(raw_bytes)

    # ── OCR ───────────────────────────────────────────────────────────────────
    try:
        raw_extraction = await extract_bill_from_images(raw_images)
    except RuntimeError as exc:
        # API key not configured
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        # Gemini returned unparsable output
        raise HTTPException(
            status_code=502,
            detail=f"OCR service returned invalid response: {exc}",
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"OCR service error: {exc}",
        ) from exc

    # ── Parse raw → Pydantic ──────────────────────────────────────────────────
    try:
        bill = parse_extraction_result(raw_extraction)
    except ValueError as exc:
        raise HTTPException(
            status_code=502, detail=f"Extraction parsing error: {exc}"
        ) from exc

    return ExtractResponse(bill=bill, warnings=bill.extraction_warnings)


@router.post("/validate", response_model=ValidateResponse)
async def validate_bill(request: ValidateRequest):
    """
    Validate a human-corrected bill with arithmetic cross-checks.
    Returns the bill (potentially with refreshed flags) plus arithmetic check results.
    """
    bill = request.bill
    warnings: list[str] = []
    TOLERANCE = Decimal("0.02")

    # Check 1: items sum → subtotal
    items_sum = sum(item.total_price for item in bill.items)
    items_ok = True
    if bill.subtotal is not None:
        diff = abs(items_sum - bill.subtotal)
        if diff > TOLERANCE:
            items_ok = False
            warnings.append(
                f"Items sum (₹{items_sum:.2f}) differs from subtotal "
                f"(₹{bill.subtotal:.2f}) by ₹{diff:.2f}."
            )

    # Check 2: subtotal + charges − discount → total
    total_ok = True
    if bill.subtotal is not None and bill.total is not None:
        calculated = bill.subtotal + bill.gst + bill.service_charge - bill.discount
        diff = abs(calculated - bill.total)
        if diff > TOLERANCE:
            total_ok = False
            warnings.append(
                f"Calculated total (₹{calculated:.2f}) differs from printed total "
                f"(₹{bill.total:.2f}) by ₹{diff:.2f}."
            )

    return ValidateResponse(
        bill=bill,
        arithmetic_checks=ArithmeticChecks(
            items_sum_matches_subtotal=items_ok,
            subtotal_plus_charges_matches_total=total_ok,
        ),
        warnings=warnings,
    )
