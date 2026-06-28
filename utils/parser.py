from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from dateutil import parser as date_parser


def now_utc_iso() -> str:
    """Return current UTC timestamp in stable ISO-8601 format."""
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_date_safe(value: str | None) -> datetime | None:
    """Parse date string safely and return timezone-aware UTC datetime."""
    if not value:
        return None
    try:
        parsed = date_parser.parse(value)
    except (ValueError, TypeError, OverflowError):
        return None

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def date_to_iso(value: str | None) -> str:
    """Convert parsed date to UTC ISO-8601, else empty string."""
    parsed = parse_date_safe(value)
    if not parsed:
        return ""
    return parsed.replace(microsecond=0).isoformat().replace("+00:00", "Z")


def first_non_empty(*values: Any) -> str:
    """Return first non-empty string representation from provided values."""
    for value in values:
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return text
    return ""
