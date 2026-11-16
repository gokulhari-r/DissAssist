"""
Handwriting analysis helper.

The student writes a target letter/word on an HTML5 <canvas>. The canvas
is exported as a base64 PNG and posted to /handwriting/check, which
calls `analyse_handwriting()` below.

Two levels of feedback:

1. Heuristic shape analysis (always available, no extra setup) - looks
   at how much of the canvas has ink, how the strokes are distributed
   across the writing area, and how the drawing's proportions compare
   to a normal line of handwriting. This gives encouraging, useful
   feedback (e.g. "letters look too small", "try to stay on the line")
   without needing any OCR engine installed.

2. Optional OCR recognition (best effort) - if `pytesseract` AND the
   Tesseract-OCR engine are installed on the machine running this app,
   we also try to actually read back what was written and compare it
   to the target word. This is skipped automatically if either is
   missing, so the feature degrades gracefully.
"""

import base64
import io

import numpy as np
from PIL import Image, ImageOps

try:
    import pytesseract
    _OCR_AVAILABLE = True
except ImportError:
    _OCR_AVAILABLE = False


def _decode_canvas_image(data_url):
    """Turn a 'data:image/png;base64,....' string into a grayscale PIL image."""
    header, encoded = data_url.split(",", 1)
    raw = base64.b64decode(encoded)
    image = Image.open(io.BytesIO(raw)).convert("RGBA")

    # Canvas exports a transparent background; flatten onto white first so
    # ink (drawn in a dark colour) reads correctly after grayscale conversion.
    background = Image.new("RGBA", image.size, (255, 255, 255, 255))
    background.paste(image, mask=image.split()[3])
    return background.convert("L")  # grayscale


def _shape_feedback(gray_image, target_text):
    """Heuristic, OCR-free feedback based on ink coverage and bounding box."""
    arr = np.array(gray_image)
    ink_mask = arr < 200  # dark pixels = ink, on a white background
    ink_pixels = int(ink_mask.sum())
    total_pixels = arr.size

    if ink_pixels < total_pixels * 0.002:
        return {
            "score": 0,
            "feedback": "It looks like nothing was written yet. Try writing "
            f"'{target_text}' on the canvas, then submit again.",
        }

    rows = np.where(ink_mask.any(axis=1))[0]
    cols = np.where(ink_mask.any(axis=0))[0]
    height = rows.max() - rows.min() + 1
    width = cols.max() - cols.min() + 1
    canvas_h, canvas_w = arr.shape

    coverage_ratio = ink_pixels / (height * width)  # how "filled in" the bounding box is
    height_ratio = height / canvas_h
    width_ratio = width / canvas_w

    notes = []
    score = 70  # baseline: something reasonable was written

    if height_ratio < 0.15:
        notes.append("Your writing is quite small — try making your letters a little bigger.")
        score -= 10
    elif height_ratio > 0.85:
        notes.append("Your writing is very large for the box — try to keep it a bit more contained.")
        score -= 5
    else:
        notes.append("Good letter size!")
        score += 10

    if width_ratio < 0.2 and len(target_text.replace(" ", "")) > 2:
        notes.append("Try to space your letters out a bit more evenly.")
        score -= 5

    if coverage_ratio < 0.04:
        notes.append("Your strokes look quite thin or broken — try writing a bit slower and more smoothly.")
        score -= 5
    elif coverage_ratio > 0.35:
        notes.append("Your strokes are nice and clear.")
        score += 5

    score = max(5, min(100, score))
    return {"score": score, "feedback": " ".join(notes)}


def _ocr_feedback(gray_image, target_text):
    """Best-effort OCR comparison. Returns None if OCR isn't usable."""
    if not _OCR_AVAILABLE:
        return None
    try:
        # Slightly upscale + threshold tends to help Tesseract on canvas drawings.
        resized = gray_image.resize((gray_image.width * 2, gray_image.height * 2))
        bw = resized.point(lambda p: 255 if p > 140 else 0)
        bw = ImageOps.invert(ImageOps.invert(bw))  # no-op, kept for clarity/extension
        recognised = pytesseract.image_to_string(bw, config="--psm 7").strip()
    except Exception:
        return None

    if not recognised:
        return None

    cleaned = recognised.lower().strip()
    target = target_text.lower().strip()
    matched = cleaned == target or target in cleaned or cleaned in target
    return {
        "recognised_text": recognised,
        "matched": matched,
    }


def analyse_handwriting(data_url, target_text):
    """
    Main entry point. Returns:
      {
        "score": 0-100,
        "feedback": "...",
        "ocr": {"recognised_text": "...", "matched": bool} | None
      }
    """
    gray_image = _decode_canvas_image(data_url)
    shape_result = _shape_feedback(gray_image, target_text)
    ocr_result = _ocr_feedback(gray_image, target_text)

    score = shape_result["score"]
    feedback = shape_result["feedback"]

    if ocr_result is not None:
        if ocr_result["matched"]:
            score = min(100, score + 15)
            feedback += " I could also read your writing and it matched the target word — nice!"
        else:
            feedback += (
                f" I tried to read your writing and saw '{ocr_result['recognised_text']}' — "
                f"have another look and compare it to '{target_text}'."
            )

    return {
        "score": round(score, 1),
        "feedback": feedback.strip(),
        "ocr": ocr_result,
        "ocr_available": _OCR_AVAILABLE,
    }
