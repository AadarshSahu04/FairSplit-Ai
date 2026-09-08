"""
Image Processing: Pillow-based preprocessing pipeline for uploaded bill images.

Operations applied in order:
  1. Decode raw bytes → PIL Image
  2. Apply EXIF orientation (so rotated phone photos are upright)
  3. Convert to RGB (strip alpha / CMYK)
  4. Resize so the longer side is ≤ MAX_DIMENSION (default 2048px)
  5. Mild contrast enhancement via ImageEnhance
  6. Return (PIL.Image, mime_type) ready for Gemini Vision
"""
from __future__ import annotations

import io
import os

from PIL import Image, ImageEnhance, ImageOps

# ── Config ────────────────────────────────────────────────────────────────────

MAX_DIMENSION: int = int(os.getenv("MAX_IMAGE_DIMENSION", "2048"))
CONTRAST_FACTOR: float = 1.15  # subtle boost; >1 = more contrast

# Maps Pillow format strings to MIME types accepted by Gemini
_FORMAT_TO_MIME: dict[str, str] = {
    "JPEG": "image/jpeg",
    "PNG":  "image/png",
    "WEBP": "image/webp",
    "GIF":  "image/gif",
}


# ── Public API ────────────────────────────────────────────────────────────────

def preprocess_image(raw_bytes: bytes) -> tuple[bytes, str]:
    """
    Apply the full preprocessing pipeline to raw image bytes.

    Args:
        raw_bytes: Bytes read from an uploaded file.

    Returns:
        (processed_bytes, mime_type) where mime_type is e.g. "image/jpeg".

    Raises:
        ValueError: If the image format is not supported.
    """
    img = _open_and_orient(raw_bytes)
    img = _to_rgb(img)
    img = _resize(img, MAX_DIMENSION)
    img = _enhance_contrast(img, CONTRAST_FACTOR)
    return _encode(img)


# ── Private helpers ───────────────────────────────────────────────────────────

def _open_and_orient(raw_bytes: bytes) -> Image.Image:
    """Open from bytes and apply EXIF orientation."""
    img = Image.open(io.BytesIO(raw_bytes))
    # ImageOps.exif_transpose is safe even when no EXIF data is present
    return ImageOps.exif_transpose(img)


def _to_rgb(img: Image.Image) -> Image.Image:
    """Convert to RGB, discarding alpha or palette modes cleanly."""
    if img.mode == "RGBA":
        # Composite onto white background to preserve visual fidelity
        background = Image.new("RGB", img.size, (255, 255, 255))
        background.paste(img, mask=img.split()[3])  # use alpha as mask
        return background
    if img.mode != "RGB":
        return img.convert("RGB")
    return img


def _resize(img: Image.Image, max_dim: int) -> Image.Image:
    """Downsample so that max(width, height) ≤ max_dim. Never upscales."""
    w, h = img.size
    long_side = max(w, h)
    if long_side <= max_dim:
        return img
    scale = max_dim / long_side
    new_size = (int(w * scale), int(h * scale))
    return img.resize(new_size, Image.LANCZOS)


def _enhance_contrast(img: Image.Image, factor: float) -> Image.Image:
    """Apply a mild contrast boost to help OCR on low-light bill photos."""
    return ImageEnhance.Contrast(img).enhance(factor)


def _encode(img: Image.Image) -> tuple[bytes, str]:
    """Encode the processed image back to bytes as JPEG."""
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=92, optimize=True)
    return buf.getvalue(), "image/jpeg"
