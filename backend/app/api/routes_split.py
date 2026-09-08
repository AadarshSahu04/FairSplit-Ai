"""
Split API route: POST /api/bill/split
Wires the HTTP layer to the calculation engine.
"""
from fastapi import APIRouter, HTTPException

from app.calculations.total_calculator import calculate_split
from app.models.split import SplitRequest, SplitResult

router = APIRouter()


@router.get("/split-ping")
async def split_ping():
    """Route health check."""
    return {"route": "split", "status": "ok"}


@router.post("/split", response_model=SplitResult)
async def split_bill(request: SplitRequest) -> SplitResult:
    """
    Calculate a fair bill split.

    Accepts a validated bill, list of people, and item assignments.
    Returns per-person breakdown with GST, service charge, and discount
    distributed proportionally.
    """
    try:
        result = calculate_split(
            bill=request.bill,
            people=request.people,
            assignments=request.assignments,
        )
        return result
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except AssertionError as exc:
        # Internal rounding assertion failed — should never happen
        raise HTTPException(
            status_code=500,
            detail=f"Internal calculation error: {exc}",
        ) from exc
