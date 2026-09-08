"""
OCR Service: Calls Google Gemini Vision API to extract raw bill data from images.

Design:
- Each image is preprocessed then sent to Gemini as a multimodal message.
- A structured JSON prompt instructs the model to extract only what it can read.
- Multiple images are merged: items from all images are concatenated; totals
  are taken from the last image (since bill totals appear at the end).
- Returns the raw parsed dict — extraction_service.py converts it to Pydantic.

Phase 9 implementation.
"""
from __future__ import annotations

import json
import logging
import os
import re
import uuid

import google.generativeai as genai

from app.utils.image_processing import preprocess_image

logger = logging.getLogger(__name__)

# ── Config ────────────────────────────────────────────────────────────────────

_MODEL_NAME = "gemini-1.5-flash"

# Gemini is configured lazily on first call so startup doesn't fail if key is missing
_client_initialized = False


def _ensure_client() -> None:
    global _client_initialized
    if _client_initialized:
        return
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY environment variable is not set. "
            "Add it to backend/.env before using OCR extraction."
        )
    genai.configure(api_key=api_key)
    _client_initialized = True


# ── Prompt ────────────────────────────────────────────────────────────────────

_EXTRACTION_PROMPT = """
You are an expert restaurant bill parser. Your task is to extract structured data from restaurant bill image(s) with maximum accuracy.

IMPORTANT RULES:
1. Extract ONLY what you can clearly read. If a value is unclear or absent, use null — NEVER guess or invent numbers.
2. Preserve item names EXACTLY as printed on the bill (preserve capitalization, abbreviations, etc.).
3. For each item: quantity × unit_price should equal total_price. If they don't match, still extract all three and note the discrepancy in the item's warning field.
4. Assign a confidence float (0.0–1.0) to each item based on how legible it is.
5. Do NOT determine who ate what. Do NOT calculate splits. Do NOT guess missing totals.
6. If multiple pages/images are provided, treat them as one combined bill. Do NOT duplicate items.
7. Currency is Indian Rupees (₹). Return numeric values only (no ₹ symbol, no commas).
8. GST, CGST, SGST, IGST, VAT — treat all as "gst" in your output (sum them).
9. Service charge, service fee — treat as "service_charge".
10. Any discount (zomato, coupon, loyalty, etc.) — treat as "discount" (positive number = reduction).

Return ONLY valid JSON matching this exact schema (no markdown, no explanation):
{
  "items": [
    {
      "id": "<unique_string>",
      "name": "<item name as printed>",
      "quantity": <number or null>,
      "unit_price": <number or null>,
      "total_price": <number>,
      "confidence": <0.0 to 1.0>,
      "warning": "<any concern about this item or null>"
    }
  ],
  "subtotal": <number or null>,
  "gst": <number or null>,
  "service_charge": <number or null>,
  "discount": <number or null>,
  "total": <number or null>,
  "extraction_notes": "<any overall concerns about the bill image quality or ambiguous fields>"
}
""".strip()


# ── Public API ────────────────────────────────────────────────────────────────

async def extract_bill_from_images(raw_images: list[bytes]) -> dict:
    """
    Send bill image(s) to Gemini Vision and return a raw extraction dict.

    Args:
        raw_images: List of raw image bytes (1–4 images).

    Returns:
        Parsed dict matching the schema in _EXTRACTION_PROMPT.

    Raises:
        RuntimeError: If GEMINI_API_KEY is not set.
        ValueError: If Gemini returns non-parsable JSON.
    """
    _ensure_client()

    model = genai.GenerativeModel(model_name=_MODEL_NAME)

    # Build the multimodal content parts: [prompt_text, image1, image2, ...]
    parts: list = [_EXTRACTION_PROMPT]

    for i, raw in enumerate(raw_images):
        processed_bytes, mime_type = preprocess_image(raw)
        parts.append(
            {"mime_type": mime_type, "data": processed_bytes}
        )
        logger.debug(f"Image {i + 1}: {len(processed_bytes)} bytes after preprocessing")

    logger.info(f"Sending {len(raw_images)} image(s) to Gemini Vision ({_MODEL_NAME})")

    response = model.generate_content(
        parts,
        generation_config=genai.types.GenerationConfig(
            temperature=0.0,   # deterministic extraction
            max_output_tokens=4096,
        ),
    )

    raw_text = response.text.strip()
    logger.debug(f"Gemini raw response length: {len(raw_text)} chars")

    return _parse_response(raw_text)


# ── Private helpers ───────────────────────────────────────────────────────────

def _parse_response(raw_text: str) -> dict:
    """
    Parse the Gemini JSON response, stripping markdown fences if present.

    Raises:
        ValueError: If the response is not valid JSON after cleanup.
    """
    # Strip markdown code fences (```json ... ```)
    cleaned = re.sub(r"^```(?:json)?\s*", "", raw_text, flags=re.MULTILINE)
    cleaned = re.sub(r"\s*```$", "", cleaned, flags=re.MULTILINE)
    cleaned = cleaned.strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as exc:
        # Try to extract JSON from the middle of a mixed response
        json_match = re.search(r"\{[\s\S]+\}", cleaned)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass
        logger.error(f"Gemini returned unparsable JSON:\n{cleaned[:500]}")
        raise ValueError(
            f"Gemini Vision returned output that could not be parsed as JSON: {exc}"
        ) from exc
