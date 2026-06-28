from __future__ import annotations

from bs4 import BeautifulSoup

from scrapers.base_scraper import BaseScraper, Opportunity


class IEEEKeralaScraper(BaseScraper):
    source_name = "IEEE Kerala"
    source_url = "https://ieeekerala.org/"

    URLS = [
        "https://ieeekerala.org/events/",
        "https://ieeekerala.org/news/",
    ]

    def _parse_page(self, soup: BeautifulSoup, source_url: str) -> list[Opportunity]:
        selectors = [
            "article",
            ".post",
            ".event",
            ".elementor-post",
        ]

        cards = []
        for selector in selectors:
            cards = soup.select(selector)
            if cards:
                break

        results: list[Opportunity] = []
        seen: set[str] = set()

        for card in cards:
            title_node = card.select_one("h1, h2, h3, .entry-title, .post-title")
            title = title_node.get_text(" ", strip=True) if title_node else ""
            if not title:
                continue

            link_node = card.select_one("a[href]")
            href = link_node.get("href", "").strip() if link_node else source_url
            description_node = card.select_one("p, .entry-summary, .excerpt")
            description = description_node.get_text(" ", strip=True) if description_node else ""
            date_node = card.select_one("time, .date, .entry-date")
            date_value = date_node.get("datetime", "") if date_node and date_node.has_attr("datetime") else date_node.get_text(" ", strip=True) if date_node else ""

            key = title.lower()
            if key in seen:
                continue
            seen.add(key)

            results.append(
                self.build_opportunity(
                    external_id=f"ieee::{key}",
                    title=title,
                    description=description,
                    company="IEEE Kerala Section",
                    type_="Event",
                    category="Event",
                    location="Kerala, India",
                    mode="",
                    start_date=date_value,
                    deadline=date_value,
                    tags=["IEEE", "Kerala", "Engineering"],
                    apply_url=href,
                    source=source_url,
                )
            )

        return results

    def scrape(self) -> list[Opportunity]:
        results: list[Opportunity] = []
        for url in self.URLS:
            try:
                soup = self.fetch_html(url)
                results.extend(self._parse_page(soup, url))
            except Exception:
                continue
        return results
