"""HTML sanitisation for imported gloss text.

Glosses are escaped at render time; bleach runs at import time so stored
rows never carry script tags or event handlers from a scraped source.
"""

from __future__ import annotations

import bleach

# Glosses are plain vocabulary notes — no markup is allowed through.
ALLOWED_TAGS: list[str] = []
ALLOWED_ATTRIBUTES: dict[str, list[str]] = {}


def clean_gloss(text: str | None) -> str:
    """Strip all HTML from a gloss or term string."""
    if not text:
        return ""
    cleaned = bleach.clean(
        text,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        strip=True,
    )
    return " ".join(cleaned.split())
