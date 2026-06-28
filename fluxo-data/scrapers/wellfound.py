from __future__ import annotations

import json
from typing import Any

from bs4 import BeautifulSoup

from scrapers.base_scraper import BaseScraper, Opportunity


class WellfoundScraper(BaseScraper):
    source_name = "Wellfound"
    source_url = "https://wellfound.com/jobs"

    URL = "https://wellfound.com/jobs?job_types[]=internship"

    @staticmethod
    def _walk(node: Any) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        if isinstance(node, dict):
            if any(key in node for key in ["title", "company", "company_name", "job_title"]):
                items.append(node)
            for value in node.values():
                items.extend(WellfoundScraper._walk(value))
        elif isinstance(node, list):
            for item in node:
                items.extend(WellfoundScraper._walk(item))
        return items

    def _parse_next_data(self, soup: BeautifulSoup) -> list[Opportunity]:
        script = soup.select_one("script#__NEXT_DATA__")
        if not script or not script.text.strip():
            return []

        try:
            payload = json.loads(script.text)
        except json.JSONDecodeError:
            return []

        opportunities: list[Opportunity] = []
        seen: set[str] = set()

        for item in self._walk(payload):
            title = str(item.get("title") or item.get("job_title") or "").strip()
            company = str(item.get("company_name") or item.get("company") or "Wellfound").strip()
            if not title:
                continue

            key = f"{title.lower()}::{company.lower()}"
            if key in seen:
                continue
            seen.add(key)

            job_slug = str(item.get("slug") or item.get("id") or "").strip()
            job_url = str(item.get("job_url") or item.get("url") or "").strip()
            if not job_url:
                job_url = f"https://wellfound.com/jobs/{job_slug}" if job_slug else self.URL

            opportunities.append(
                self.build_opportunity(
                    external_id=f"wellfound::{job_slug or key}",
                    title=title,
                    description=str(item.get("description") or item.get("summary") or ""),
                    company=company,
                    type_="Internship",
                    category="Internship",
                    location=str(item.get("location") or ""),
                    mode=str(item.get("remote") or item.get("mode") or ""),
                    start_date=str(item.get("created_at") or ""),
                    deadline=str(item.get("deadline") or ""),
                    skills=item.get("skills") if isinstance(item.get("skills"), list) else [],
                    tags=["Wellfound", "Startup", "Internship"],
                    image=str(item.get("company_logo") or ""),
                    apply_url=job_url,
                )
            )

        return opportunities

    def _parse_cards(self, soup: BeautifulSoup) -> list[Opportunity]:
        cards = soup.select("a[href*='/jobs/']")
        opportunities: list[Opportunity] = []
        seen: set[str] = set()

        for card in cards:
            title = card.get_text(" ", strip=True)
            if not title or len(title) < 6:
                continue
            href = card.get("href", "").strip()
            if href.startswith("/"):
                href = f"https://wellfound.com{href}"
            key = title.lower()
            if key in seen:
                continue
            seen.add(key)

            opportunities.append(
                self.build_opportunity(
                    external_id=f"wellfound-card::{key}",
                    title=title,
                    company="Wellfound",
                    type_="Internship",
                    category="Internship",
                    tags=["Wellfound", "Internship"],
                    apply_url=href,
                )
            )

        return opportunities

    def scrape(self) -> list[Opportunity]:
        soup = self.fetch_html(self.URL)
        opportunities = self._parse_next_data(soup)
        if opportunities:
            return opportunities
        return self._parse_cards(soup)
