from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any

import feedparser
import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from retry import retry

from utils.cleaner import clean_list, clean_text, normalize_mode
from utils.parser import date_to_iso


SUPPORTED_CATEGORIES = {
    "Internship",
    "Hackathon",
    "Workshop",
    "Conference",
    "Competition",
    "Scholarship",
    "Research",
    "Campus Ambassador",
    "Open Source",
    "Event",
}


@dataclass(slots=True)
class Opportunity:
    id: str = ""
    title: str = ""
    description: str = ""
    company: str = ""
    type: str = ""
    category: str = ""
    location: str = ""
    mode: str = ""
    startDate: str = ""
    deadline: str = ""
    skills: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    image: str = ""
    source: str = ""
    sourceName: str = ""
    applyUrl: str = ""
    scrapedAt: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to JSON-serializable dictionary."""
        return asdict(self)


class BaseScraper(ABC):
    """Base class for all source-specific scrapers."""

    source_name: str = ""
    source_url: str = ""

    def __init__(self, timeout: int = 25) -> None:
        self.timeout = timeout
        self.session = requests.Session()
        self.user_agent = UserAgent(platforms="desktop")

    @property
    def headers(self) -> dict[str, str]:
        try:
            user_agent = self.user_agent.random
        except Exception:
            user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
        return {
            "User-Agent": user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }

    @retry(tries=3, delay=1, backoff=2)
    def fetch(self, url: str, extra_headers: dict[str, str] | None = None) -> requests.Response:
        """Fetch a URL with retries and timeout."""
        headers = self.headers.copy()
        if extra_headers:
            headers.update(extra_headers)

        response = self.session.get(url, headers=headers, timeout=self.timeout)
        response.raise_for_status()
        return response

    def fetch_html(self, url: str) -> BeautifulSoup:
        response = self.fetch(url)
        return BeautifulSoup(response.text, "lxml")

    def fetch_feed(self, url: str) -> feedparser.FeedParserDict:
        response = self.fetch(url)
        return feedparser.parse(response.text)

    def build_opportunity(
        self,
        *,
        title: str,
        description: str = "",
        company: str = "",
        type_: str = "",
        category: str = "",
        location: str = "",
        mode: str = "",
        start_date: str = "",
        deadline: str = "",
        skills: list[str] | None = None,
        tags: list[str] | None = None,
        image: str = "",
        apply_url: str = "",
        source: str | None = None,
        source_name: str | None = None,
        external_id: str = "",
    ) -> Opportunity:
        """Build normalized opportunity object from raw fields."""
        normalized_category = clean_text(category) or "Event"
        if normalized_category not in SUPPORTED_CATEGORIES:
            normalized_category = "Event"

        normalized_title = clean_text(title)
        normalized_company = clean_text(company) or source_name or self.source_name
        normalized_mode = clean_text(mode) or normalize_mode(location)

        now = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")

        return Opportunity(
            id=clean_text(external_id) or f"{self.source_name.lower()}::{normalized_title.lower()}::{normalized_company.lower()}",
            title=normalized_title,
            description=clean_text(description),
            company=normalized_company,
            type=clean_text(type_) or normalized_category,
            category=normalized_category,
            location=clean_text(location),
            mode=normalized_mode,
            startDate=date_to_iso(start_date),
            deadline=date_to_iso(deadline),
            skills=clean_list(skills),
            tags=clean_list(tags),
            image=clean_text(image),
            source=source or self.source_url,
            sourceName=source_name or self.source_name,
            applyUrl=clean_text(apply_url),
            scrapedAt=now,
        )

    @abstractmethod
    def scrape(self) -> list[Opportunity]:
        """Scrape source and return normalized opportunities."""
        raise NotImplementedError
