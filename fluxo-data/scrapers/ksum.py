from __future__ import annotations

from bs4 import BeautifulSoup

from scrapers.base_scraper import BaseScraper, Opportunity


class KSUMScraper(BaseScraper):
    source_name = "Kerala Startup Mission"
    source_url = "https://startupmission.kerala.gov.in/"

    TARGETS = [
        ("https://startupmission.kerala.gov.in/events", "Event"),
        ("https://startupmission.kerala.gov.in/programmes", "Scholarship"),
    ]

    def _parse_cards(self, soup: BeautifulSoup, category: str, page_url: str) -> list[Opportunity]:
        cards = soup.select("article, .card, .views-row, .event-card")
        opportunities: list[Opportunity] = []
        seen: set[str] = set()

        for card in cards:
            title_node = card.select_one("h1, h2, h3, h4, .title, .card-title")
            title = title_node.get_text(" ", strip=True) if title_node else ""
            if not title:
                continue
            key = title.lower()
            if key in seen:
                continue
            seen.add(key)

            link_node = card.select_one("a[href]")
            href = link_node.get("href", "").strip() if link_node else page_url
            if href.startswith("/"):
                href = f"https://startupmission.kerala.gov.in{href}"

            description_node = card.select_one("p, .desc, .summary")
            description = description_node.get_text(" ", strip=True) if description_node else ""
            date_node = card.select_one("time, .date")
            date_value = date_node.get("datetime", "") if date_node and date_node.has_attr("datetime") else date_node.get_text(" ", strip=True) if date_node else ""

            opportunities.append(
                self.build_opportunity(
                    external_id=f"ksum::{category.lower()}::{key}",
                    title=title,
                    description=description,
                    company="Kerala Startup Mission",
                    type_=category,
                    category=category,
                    location="Kerala, India",
                    start_date=date_value,
                    deadline=date_value,
                    tags=["KSUM", category],
                    apply_url=href,
                    source=page_url,
                )
            )

        return opportunities

    def scrape(self) -> list[Opportunity]:
        opportunities: list[Opportunity] = []
        for url, category in self.TARGETS:
            try:
                soup = self.fetch_html(url)
                opportunities.extend(self._parse_cards(soup, category, url))
            except Exception:
                continue
        return opportunities
