from __future__ import annotations

import feedparser

from scrapers.base_scraper import BaseScraper, Opportunity


class TinkerHubScraper(BaseScraper):
    source_name = "TinkerHub"
    source_url = "https://tinkerhub.org/"

    FEEDS = [
        "https://tinkerhub.org/blog/rss.xml",
        "https://tinkerhub.org/feed.xml",
    ]

    def scrape(self) -> list[Opportunity]:
        opportunities: list[Opportunity] = []
        seen: set[str] = set()

        for feed_url in self.FEEDS:
            try:
                feed = self.fetch_feed(feed_url)
            except Exception:
                continue

            for entry in getattr(feed, "entries", []):
                title = str(getattr(entry, "title", "")).strip()
                if not title:
                    continue
                key = title.lower()
                if key in seen:
                    continue
                seen.add(key)

                tags = [tag.term for tag in getattr(entry, "tags", []) if getattr(tag, "term", None)]
                published = str(getattr(entry, "published", ""))

                opportunities.append(
                    self.build_opportunity(
                        external_id=f"tinkerhub::{key}",
                        title=title,
                        description=str(getattr(entry, "summary", "")),
                        company="TinkerHub Foundation",
                        type_="Event",
                        category="Event",
                        location="Kerala, India",
                        mode="",
                        start_date=published,
                        deadline=published,
                        tags=["TinkerHub", *tags],
                        image=str(getattr(entry, "image", "")),
                        apply_url=str(getattr(entry, "link", self.source_url)),
                        source=feed_url,
                    )
                )

        return opportunities
