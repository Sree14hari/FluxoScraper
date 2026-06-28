from __future__ import annotations

import re
from html import unescape
from typing import Iterable


def clean_text(value: str | None) -> str:
    """Normalize whitespace and strip HTML-like artifacts from text."""
    if not value:
        return ""
    value = unescape(value)
    value = re.sub(r"<[^>]+>", " ", value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def clean_list(values: Iterable[str] | None) -> list[str]:
    """Clean a list of strings, drop empties, and preserve stable order."""
    if not values:
        return []

    seen: set[str] = set()
    cleaned: list[str] = []
    for value in values:
        item = clean_text(value)
        if item and item.lower() not in seen:
            seen.add(item.lower())
            cleaned.append(item)
    return cleaned


def normalize_mode(value: str | None) -> str:
    """Map free-form location/mode text into Online/Offline/Hybrid."""
    text = clean_text(value).lower()
    if not text:
        return ""
    if any(keyword in text for keyword in ["remote", "virtual", "online"]):
        return "Online"
    if any(keyword in text for keyword in ["hybrid", "mixed"]):
        return "Hybrid"
    if any(keyword in text for keyword in ["in-person", "onsite", "offline"]):
        return "Offline"
    return ""
