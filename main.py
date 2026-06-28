from __future__ import annotations

import asyncio
import importlib
import inspect
import json
import pkgutil
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

import scrapers
from scrapers.base_scraper import BaseScraper, Opportunity
from utils.duplicate import deduplicate_opportunities
from utils.logger import setup_logger
from utils.parser import now_utc_iso, parse_date_safe


DATA_DIR = Path(__file__).parent / "data"


def discover_scrapers() -> list[BaseScraper]:
    """Auto-discover scraper classes in scrapers package."""
    instances: list[BaseScraper] = []

    for module_info in pkgutil.iter_modules(scrapers.__path__):
        if module_info.name in {"base_scraper", "__init__"}:
            continue

        module = importlib.import_module(f"scrapers.{module_info.name}")
        for _, obj in inspect.getmembers(module, inspect.isclass):
            if not issubclass(obj, BaseScraper):
                continue
            if obj is BaseScraper:
                continue
            if inspect.isabstract(obj):
                continue
            instances.append(obj())

    instances.sort(key=lambda scraper: scraper.source_name)
    return instances


def sort_opportunities(opportunities: list[Opportunity]) -> list[Opportunity]:
    """Sort by nearest deadline first, then newest scrapedAt."""

    def key(item: Opportunity) -> tuple[datetime, float]:
        deadline = parse_date_safe(item.deadline) or datetime.max.replace(tzinfo=UTC)
        scraped = parse_date_safe(item.scrapedAt) or datetime.min.replace(tzinfo=UTC)
        return deadline, -scraped.timestamp()

    return sorted(opportunities, key=key)


def split_by_output_files(opportunities: list[Opportunity]) -> dict[str, list[dict[str, object]]]:
    """Map normalized opportunities into required output files."""
    groups: dict[str, list[Opportunity]] = {
        "internships": [],
        "hackathons": [],
        "events": [],
        "conferences": [],
        "workshops": [],
        "scholarships": [],
    }

    for item in opportunities:
        if item.category == "Internship":
            groups["internships"].append(item)
        elif item.category == "Hackathon":
            groups["hackathons"].append(item)
        elif item.category == "Workshop":
            groups["workshops"].append(item)
        elif item.category == "Conference":
            groups["conferences"].append(item)
        elif item.category == "Scholarship":
            groups["scholarships"].append(item)
        else:
            groups["events"].append(item)

    return {name: [asdict(item) for item in values] for name, values in groups.items()}


def write_json(file_path: Path, payload: object) -> None:
    """Write UTF-8 pretty JSON output."""
    with file_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)


async def run_scrapers(scraper_instances: list[BaseScraper], logger) -> list[Opportunity]:
    """Run all scrapers concurrently and collect successful results."""
    collected: list[Opportunity] = []

    async def run_single(scraper: BaseScraper) -> None:
        logger.info(f"[cyan]Scraping {scraper.source_name}...[/cyan]")
        try:
            items = await asyncio.to_thread(scraper.scrape)
            logger.info(f"[green]Found {len(items)} opportunities from {scraper.source_name}[/green]")
            collected.extend(items)
        except Exception as error:
            logger.error(f"[red]Failed {scraper.source_name}: {error}[/red]")

    await asyncio.gather(*(run_single(scraper) for scraper in scraper_instances))
    return collected


async def main() -> int:
    logger = setup_logger()
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    scraper_instances = discover_scrapers()
    if not scraper_instances:
        logger.error("[red]No scraper implementations found.[/red]")
        return 1

    raw = await run_scrapers(scraper_instances, logger)
    unique, removed = deduplicate_opportunities(raw)
    logger.info(f"[yellow]Duplicate removed: {removed}[/yellow]")

    sorted_items = sort_opportunities(unique)
    grouped = split_by_output_files(sorted_items)

    write_json(DATA_DIR / "internships.json", grouped["internships"])
    write_json(DATA_DIR / "hackathons.json", grouped["hackathons"])
    write_json(DATA_DIR / "events.json", grouped["events"])
    write_json(DATA_DIR / "conferences.json", grouped["conferences"])
    write_json(DATA_DIR / "workshops.json", grouped["workshops"])
    write_json(DATA_DIR / "scholarships.json", grouped["scholarships"])
    write_json(DATA_DIR / "opportunities.json", [asdict(item) for item in sorted_items])

    stats = {
        "lastUpdated": now_utc_iso(),
        "totalOpportunities": len(sorted_items),
        "internships": len(grouped["internships"]),
        "hackathons": len(grouped["hackathons"]),
        "events": len(grouped["events"]),
        "conferences": len(grouped["conferences"]),
        "workshops": len(grouped["workshops"]),
        "scholarships": len(grouped["scholarships"]),
    }
    write_json(DATA_DIR / "stats.json", stats)

    logger.info("[bold green]JSON generated[/bold green]")
    logger.info("[bold green]Completed successfully[/bold green]")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
