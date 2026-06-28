from __future__ import annotations

import json
from typing import Any

from bs4 import BeautifulSoup

from scrapers.base_scraper import BaseScraper, Opportunity


class UnstopScraper(BaseScraper):
    source_name = "Unstop"
    source_url = "https://unstop.com/"

    TARGETS: list[tuple[str, str]] = [
        ("https://unstop.com/hackathons", "Hackathon"),
        ("https://unstop.com/internships", "Internship"),
        ("https://unstop.com/workshops", "Workshop"),
        ("https://unstop.com/competitions", "Competition"),
    ]

    @staticmethod
    def _walk_json(node: Any) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        if isinstance(node, dict):
            has_title = any(key in node for key in ["title", "name", "seo_url"])
            if has_title:
                items.append(node)
            for value in node.values():
                items.extend(UnstopScraper._walk_json(value))
        elif isinstance(node, list):
            for item in node:
                items.extend(UnstopScraper._walk_json(item))
        return items

    def _category_from_target(self, category: str) -> str:
        return category if category in {"Internship", "Hackathon", "Workshop", "Competition"} else "Event"

    def _parse_page(self, url: str, fallback_category: str) -> list[Opportunity]:
        soup = self.fetch_html(url)
        script = soup.select_one("script#__NEXT_DATA__")
        opportunities: list[Opportunity] = []
        seen: set[str] = set()

        if script and script.text.strip():
            try:
                payload = json.loads(script.text)
            except json.JSONDecodeError:
                payload = {}

            for item in self._walk_json(payload):
                title = str(item.get("title") or item.get("name") or "").strip()
                if not title or len(title) < 4:
                    continue
                company = str(item.get("organization_name") or item.get("organisation") or item.get("company_name") or "Unstop")
                key = f"{title.lower()}::{company.lower()}"
                if key in seen:
                    continue
                seen.add(key)

                slug = str(item.get("seo_url") or item.get("slug") or "").strip()
                apply_url = f"https://unstop.com/{slug}" if slug else url
                category = str(item.get("opportunity_type") or fallback_category).title()
                normalized_category = self._category_from_target(category)

                opportunities.append(
                    self.build_opportunity(
                        external_id=f"unstop::{slug or key}",
                        title=title,
                        description=str(item.get("short_desc") or item.get("description") or ""),
                        company=company,
                        type_=normalized_category,
                        category=normalized_category,
                        location=str(item.get("region") or item.get("location") or ""),
                        mode=str(item.get("mode") or ""),
                        start_date=str(item.get("start_date") or ""),
                        deadline=str(item.get("regn_deadline") or item.get("deadline") or ""),
                        tags=["Unstop", normalized_category],
                        image=str(item.get("logo_url") or item.get("banner_mobile") or ""),
                        apply_url=apply_url,
                    )
                )

        if opportunities:
            return opportunities

        cards = soup.select("a[href*='unstop.com/']")
        for card in cards:
            title = card.get_text(" ", strip=True)
            href = card.get("href", "").strip()
            if not title or len(title) < 8:
                continue
            key = title.lower()
            if key in seen:
                continue
            seen.add(key)
            opportunities.append(
                self.build_opportunity(
                    external_id=f"unstop-card::{key}",
                    title=title,
                    company="Unstop",
                    type_=fallback_category,
                    category=self._category_from_target(fallback_category),
                    tags=["Unstop", fallback_category],
                    apply_url=href,
                )
            )

        return opportunities

    def scrape(self) -> list[Opportunity]:
        collected: list[Opportunity] = []
        for url, category in self.TARGETS:
            try:
                collected.extend(self._parse_page(url, category))
            except Exception:
                continue
        return collected
