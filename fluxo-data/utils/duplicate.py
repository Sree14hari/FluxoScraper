from __future__ import annotations

from datetime import timedelta

from rapidfuzz import fuzz

from scrapers.base_scraper import Opportunity
from utils.parser import parse_date_safe


TITLE_THRESHOLD = 90
COMPANY_THRESHOLD = 90
MAX_DEADLINE_DELTA_DAYS = 2


def _same_deadline_window(left: str, right: str) -> bool:
    left_dt = parse_date_safe(left)
    right_dt = parse_date_safe(right)

    if not left_dt and not right_dt:
        return True
    if not left_dt or not right_dt:
        return False
    return abs(left_dt - right_dt) <= timedelta(days=MAX_DEADLINE_DELTA_DAYS)


def is_duplicate(candidate: Opportunity, existing: Opportunity) -> bool:
    """Determine whether two opportunities represent the same listing."""
    title_score = fuzz.token_set_ratio(candidate.title, existing.title)
    company_score = fuzz.token_set_ratio(candidate.company, existing.company)

    if title_score < TITLE_THRESHOLD:
        return False
    if company_score < COMPANY_THRESHOLD:
        return False
    return _same_deadline_window(candidate.deadline, existing.deadline)


def deduplicate_opportunities(opportunities: list[Opportunity]) -> tuple[list[Opportunity], int]:
    """Deduplicate opportunities while preserving first-seen ordering."""
    unique: list[Opportunity] = []
    removed_count = 0

    for item in opportunities:
        if any(is_duplicate(item, existing) for existing in unique):
            removed_count += 1
            continue
        unique.append(item)

    return unique, removed_count
