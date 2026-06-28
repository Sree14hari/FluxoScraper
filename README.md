# Fluxo Data Pipeline

Production-ready Python scraping pipeline that generates static JSON opportunity feeds for the Fluxo Flutter app. No backend server is required.

## Architecture

Python Scrapers -> Merge Data -> Generate JSON Files -> GitHub Repository -> Flutter App downloads JSON

## Tech Stack

- Python 3.12
- requests
- beautifulsoup4
- lxml
- feedparser
- python-dateutil
- rapidfuzz
- fake-useragent
- retry
- rich

## Project Structure

```text
fluxo-data/
├── data/
│   ├── internships.json
│   ├── hackathons.json
│   ├── workshops.json
│   ├── conferences.json
│   ├── events.json
│   ├── scholarships.json
│   ├── opportunities.json
│   └── stats.json
├── scrapers/
│   ├── base_scraper.py
│   ├── devfolio.py
│   ├── unstop.py
│   ├── ieee.py
│   ├── tinkerhub.py
│   ├── ksum.py
│   ├── wellfound.py
│   └── google_events.py
├── utils/
│   ├── cleaner.py
│   ├── duplicate.py
│   ├── parser.py
│   └── logger.py
├── assets/
├── main.py
├── requirements.txt
└── README.md
```

## Installation

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/macOS
source .venv/bin/activate
pip install -r requirements.txt
```

## Run Locally

```bash
python main.py
```

Output JSON files are generated in `data/`.

## JSON Schema

Each scraper returns `List[Opportunity]` where each object has:

```json
{
  "id": "",
  "title": "",
  "description": "",
  "company": "",
  "type": "",
  "category": "",
  "location": "",
  "mode": "",
  "startDate": "",
  "deadline": "",
  "skills": [],
  "tags": [],
  "image": "",
  "source": "",
  "sourceName": "",
  "applyUrl": "",
  "scrapedAt": ""
}
```

## Duplicate Detection

Two opportunities are considered duplicates when:

- Title similarity is high (RapidFuzz token set ratio)
- Company similarity is high (RapidFuzz token set ratio)
- Deadline is within 2 days

## Sorting

Results are sorted by:

1. Nearest deadline
2. Newest scraped timestamp

## Supported Sources

- Devfolio
- Unstop
- IEEE Kerala
- TinkerHub
- Kerala Startup Mission
- Wellfound
- Google Developer Groups
- Microsoft Reactor
- AWS Events
- NVIDIA Events
- GitHub Student Programs

## How To Add A New Scraper

No change to `main.py` is required.

1. Create a new file inside `scrapers/`.
2. Add one class that inherits `BaseScraper`.
3. Implement `scrape(self) -> list[Opportunity]`.
4. Return normalized opportunities using `self.build_opportunity(...)`.

The discovery system auto-loads every non-abstract `BaseScraper` subclass in `scrapers/`.

## GitHub Actions Automation

Workflow file: `.github/workflows/update.yml`

- Runs every 6 hours (`cron: 0 */6 * * *`)
- Uses Python 3.12
- Installs dependencies
- Executes `python main.py`
- Commits and pushes updated files in `data/*.json`

## Logging

Rich logging outputs steps such as:

- Scraping Devfolio...
- Found N opportunities
- Duplicate removed
- JSON generated
- Completed successfully
