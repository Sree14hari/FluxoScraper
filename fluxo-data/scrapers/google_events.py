from __future__ import annotations

from scrapers.base_scraper import BaseScraper, Opportunity


class GlobalEventsFeedScraper(BaseScraper):
    source_name = "Global Tech Events"
    source_url = "https://developers.google.com/community/gdg"

    FEEDS: list[dict[str, str]] = [
        {
            "name": "Google Developer Groups",
            "url": "https://developers.googleblog.com/feeds/posts/default?alt=rss",
            "category": "Event",
            "company": "Google Developer Groups",
            "tags": "Google,GDG,Event",
        },
        {
            "name": "Microsoft Reactor",
            "url": "https://developer.microsoft.com/en-us/reactor/rss",
            "category": "Event",
            "company": "Microsoft Reactor",
            "tags": "Microsoft,Reactor,Event",
        },
        {
            "name": "AWS Events",
            "url": "https://aws.amazon.com/events/feed/",
            "category": "Conference",
            "company": "Amazon Web Services",
            "tags": "AWS,Cloud,Event",
        },
        {
            "name": "NVIDIA Events",
            "url": "https://blogs.nvidia.com/feed/",
            "category": "Conference",
            "company": "NVIDIA",
            "tags": "NVIDIA,AI,Event",
        },
        {
            "name": "GitHub Student Programs",
            "url": "https://github.blog/changelog/label/education/feed/",
            "category": "Open Source",
            "company": "GitHub",
            "tags": "GitHub,Student,Open Source",
        },
    ]

    def scrape(self) -> list[Opportunity]:
        opportunities: list[Opportunity] = []
        seen: set[str] = set()

        for feed_cfg in self.FEEDS:
            feed_url = feed_cfg["url"]
            source_name = feed_cfg["name"]
            category = feed_cfg["category"]
            tags = [item.strip() for item in feed_cfg["tags"].split(",") if item.strip()]

            try:
                parsed_feed = self.fetch_feed(feed_url)
            except Exception:
                continue

            for entry in getattr(parsed_feed, "entries", []):
                title = str(getattr(entry, "title", "")).strip()
                if not title:
                    continue

                key = f"{source_name.lower()}::{title.lower()}"
                if key in seen:
                    continue
                seen.add(key)

                summary = str(getattr(entry, "summary", ""))
                link = str(getattr(entry, "link", feed_url))
                published = str(getattr(entry, "published", ""))

                opportunities.append(
                    self.build_opportunity(
                        external_id=f"feed::{key}",
                        title=title,
                        description=summary,
                        company=feed_cfg["company"],
                        type_=category,
                        category=category,
                        location="Global",
                        mode="Online",
                        start_date=published,
                        deadline=published,
                        tags=tags,
                        apply_url=link,
                        source=feed_url,
                        source_name=source_name,
                    )
                )

        return opportunities
