from __future__ import annotations

import json
from typing import Any

from bs4 import BeautifulSoup

from scrapers.base_scraper import BaseScraper, Opportunity


class DevfolioScraper(BaseScraper):
    source_name = "Devfolio"
    source_url = "https://devfolio.co/hackathons"

    @staticmethod
    def _walk_json(node: Any) -> list[dict[str, Any]]:
        hits: list[dict[str, Any]] = []
        if isinstance(node, dict):
            if node.get("name") and (node.get("url") or node.get("slug")):
                hits.append(node)
            for value in node.values():
                hits.extend(DevfolioScraper._walk_json(value))
        elif isinstance(node, list):
            for item in node:
                hits.extend(DevfolioScraper._walk_json(item))
        return hits

    def _parse_from_next_data(self, soup: BeautifulSoup) -> list[Opportunity]:
        script = soup.select_one("script#__NEXT_DATA__")
        if not script or not script.text.strip():
            return []

        try:
            payload = json.loads(script.text)
        except json.JSONDecodeError:
            return []

        opportunities: list[Opportunity] = []
        seen_titles: set[str] = set()

        for item in self._walk_json(payload):
            title = str(item.get("name") or item.get("title") or "").strip()
            if not title:
                continue
            key = title.lower()
            if key in seen_titles:
                continue
            seen_titles.add(key)

            slug = str(item.get("slug") or "").strip()
            url = str(item.get("url") or "").strip()
            apply_url = url if url.startswith("http") else f"https://devfolio.co/{slug}" if slug else self.source_url
            deadline = str(item.get("registrationDeadline") or item.get("deadline") or "")
            start_date = str(item.get("startDate") or item.get("startsAt") or "")

            opportunities.append(
                self.build_opportunity(
                    external_id=f"devfolio::{slug or key}",
                    title=title,
                    description=str(item.get("tagline") or item.get("description") or ""),
                    company=str(item.get("organizationName") or "Devfolio"),
                    type_="Hackathon",
                    category="Hackathon",
                    location=str(item.get("city") or item.get("location") or ""),
                    mode=str(item.get("mode") or ""),
                    start_date=start_date,
                    deadline=deadline,
                    tags=["Devfolio", "Hackathon"],
                    image=str(item.get("logo") or item.get("coverImage") or ""),
                    apply_url=apply_url,
                )
            )

        return opportunities

    def _parse_from_cards(self, soup: BeautifulSoup) -> list[Opportunity]:
        cards = soup.select("a[href*='/hackathon/'], a[href*='hackathon']")
        opportunities: list[Opportunity] = []
        seen: set[str] = set()

        for card in cards:
            title = card.get_text(" ", strip=True)
            href = card.get("href", "").strip()
            if not title or len(title) < 6:
                continue
            key = title.lower()
            if key in seen:
                continue
            seen.add(key)

            if href and href.startswith("/"):
                href = f"https://devfolio.co{href}"

            opportunities.append(
                self.build_opportunity(
                    external_id=f"devfolio-card::{key}",
                    title=title,
                    company="Devfolio",
                    type_="Hackathon",
                    category="Hackathon",
                    tags=["Devfolio", "Hackathon"],
                    apply_url=href or self.source_url,
                )
            )

        return opportunities

    def scrape(self) -> list[Opportunity]:
        soup = self.fetch_html(self.source_url)
        opportunities = self._parse_from_next_data(soup)
        if opportunities:
            return opportunities
        return self._parse_from_cards(soup)
