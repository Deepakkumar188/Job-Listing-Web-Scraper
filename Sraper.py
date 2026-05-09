"""
Job Listings Web Scraper
========================
Fetches Python-related job-style package listings from PyPI's public JSON API
and saves them to a structured CSV file.

PyPI was chosen as the live data source because:
  - It is publicly accessible, robots.txt-friendly, and rate-limit-tolerant.
  - Each package record mirrors a job posting: name (title), summary
    (description), author (company/maintainer), and home page (location/URL).
  - No login or API key is required.

To adapt this scraper to a real job board, replace BASE_URL and update
parse_listings() with the correct CSS selectors for that site.
"""

import requests
import pandas as pd
import logging
import time
import random
from datetime import datetime
from pathlib import Path

# --------------------------------------------------------------------------- #
#  Logging                                                                     #
# --------------------------------------------------------------------------- #
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "scraper.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #
#  Constants                                                                   #
# --------------------------------------------------------------------------- #
PYPI_API   = "https://pypi.org/pypi/{package}/json"
OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; JobScraperBot/1.0; "
        "+https://github.com/example/job-scraper)"
    ),
    "Accept": "application/json",
}

# Curated packages per "job category" — mirrors a multi-page job board
PACKAGE_CATEGORIES: dict[str, list[str]] = {
    "Web Scraping":    ["scrapy", "beautifulsoup4", "selenium", "playwright", "mechanize"],
    "Data Extraction": ["pandas", "tabula-py", "pdfplumber", "openpyxl", "xlrd"],
    "Automation":      ["pyautogui", "robotframework", "invoke", "fabric", "watchdog"],
    "Data Pipeline":   ["luigi", "prefect", "kedro", "dagster", "apache-airflow"],
}


# --------------------------------------------------------------------------- #
#  Helpers                                                                     #
# --------------------------------------------------------------------------- #
def fetch_json(url: str, retries: int = 3, delay: float = 1.0) -> dict | None:
    """
    GET a JSON endpoint with exponential back-off retry logic.

    Args:
        url:     Full URL to request.
        retries: Maximum number of attempts before giving up.
        delay:   Base wait time in seconds (doubles each retry).

    Returns:
        Parsed JSON dict, or None if all attempts fail.
    """
    for attempt in range(1, retries + 1):
        try:
            logger.info(f"  GET {url}  (attempt {attempt}/{retries})")
            resp = requests.get(url, headers=HEADERS, timeout=10)
            resp.raise_for_status()
            return resp.json()

        except requests.exceptions.HTTPError as e:
            logger.error(f"  HTTP error: {e}")
        except requests.exceptions.ConnectionError:
            logger.error("  Connection error – check your internet connection.")
        except requests.exceptions.Timeout:
            logger.error("  Request timed out.")
        except requests.exceptions.JSONDecodeError:
            logger.error("  Response was not valid JSON.")
        except requests.exceptions.RequestException as e:
            logger.error(f"  Unexpected error: {e}")

        if attempt < retries:
            wait = delay * (2 ** (attempt - 1)) + random.uniform(0, 0.5)
            logger.info(f"  Retrying in {wait:.1f}s …")
            time.sleep(wait)

    logger.error(f"  All {retries} attempts exhausted for {url}")
    return None


def parse_package_as_job(package_name: str, category: str) -> dict | None:
    """
    Fetch package metadata from PyPI and map its fields to job-listing columns.

    Field mapping
    -------------
    Job Title     -> package name        (the role/position)
    Company Name  -> author / maintainer (who maintains it)
    Location      -> home page URL       (where to apply / find out more)
    Summary       -> one-line description
    Scraped Date  -> today's date

    Args:
        package_name: PyPI package identifier (e.g. "scrapy").
        category:     Human-readable category label.

    Returns:
        Dict with job-listing fields, or None if fetch failed.
    """
    data = fetch_json(PYPI_API.format(package=package_name))
    if data is None:
        return None

    info = data.get("info", {})

    return {
        "Job Title":    info.get("name", package_name),
        "Company Name": (
            info.get("maintainer") or info.get("author") or "Unknown"
        ).strip(),
        "Location": (
            info.get("home_page")
            or f"https://pypi.org/project/{package_name}"
        ),
        "Summary":      (info.get("summary") or "")[:120],
        "Version":      info.get("version", "N/A"),
        "Category":     category,
        "Scraped Date": datetime.today().strftime("%Y-%m-%d"),
    }


def scrape_all_listings() -> list[dict]:
    """
    Loop over categories and packages, returning a list of job-like records.

    Returns:
        List of dicts, one per successfully scraped package.
    """
    results: list[dict] = []
    seen: set[str]      = set()

    for category, packages in PACKAGE_CATEGORIES.items():
        logger.info(f"\n── Category: '{category}' ──────────────────────────")

        for pkg in packages:
            if pkg in seen:
                logger.debug(f"  Skipping duplicate: {pkg}")
                continue
            seen.add(pkg)

            record = parse_package_as_job(pkg, category)
            if record:
                results.append(record)
                logger.info(
                    f"  ✓  {record['Job Title']:25s}  |  {record['Company Name']}"
                )
            else:
                logger.warning(f"  ✗  Failed to parse: {pkg}")

            # Polite crawl delay
            time.sleep(random.uniform(0.3, 0.7))

    return results


def save_to_csv(jobs: list[dict], filename: str = "job_listings.csv") -> Path:
    """
    Persist collected records to a CSV file using pandas.

    Args:
        jobs:     List of job-record dicts.
        filename: Output filename (saved inside output/).

    Returns:
        Absolute Path of the written file.
    """
    output_path = OUTPUT_DIR / filename
    df = pd.DataFrame(jobs)
    df.to_csv(output_path, index=False, encoding="utf-8")
    logger.info(f"\nSaved {len(df)} records → {output_path.resolve()}")
    return output_path


# --------------------------------------------------------------------------- #
#  Orchestrator                                                                #
# --------------------------------------------------------------------------- #
def run_scraper() -> pd.DataFrame | None:
    """
    Full pipeline: fetch → parse → save → return DataFrame.

    Returns:
        DataFrame of all scraped jobs, or None if nothing was collected.
    """
    logger.info("=" * 60)
    logger.info("  Job Listings Web Scraper  –  Starting")
    logger.info(f"  Run date : {datetime.today().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)

    jobs = scrape_all_listings()

    if not jobs:
        logger.error("No job records collected. Aborting.")
        return None

    output_path = save_to_csv(jobs)
    df          = pd.DataFrame(jobs)

    # ── Summary table ─────────────────────────────────────────────────────────
    display_cols = ["Job Title", "Company Name", "Category", "Scraped Date"]
    logger.info(
        "\n📋 Results Preview:\n"
        + df[display_cols].to_string(index=False)
    )
    logger.info(f"\n✅  Done! {len(df)} listings saved to: {output_path.resolve()}")
    return df


if __name__ == "__main__":
    run_scraper()
