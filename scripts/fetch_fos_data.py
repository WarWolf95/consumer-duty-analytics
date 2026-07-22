import os
import requests
import csv
import re
from bs4 import BeautifulSoup
from scripts.config import RAW_DATA_DIR
from scripts.utils import setup_logging

logger = setup_logging("fetch_fos_data")

FOS_PAGE_URL = (
    "https://www.financial-ombudsman.org.uk/businesses/"
    "resolving-complaint/our-insight/"
    "annual-complaints-data-and-insight-2025-26"
)

OUTPUT_CSV = os.path.join(RAW_DATA_DIR, "fos_complaints_2025_26.csv")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


def fetch_page() -> str | None:
    logger.info("Fetching FOS annual data page")
    try:
        resp = requests.get(FOS_PAGE_URL, headers=HEADERS, timeout=60)
        if resp.status_code == 200:
            logger.info("Page fetched (%.1f KB)", len(resp.text) / 1024)
            return resp.text
        else:
            logger.error("HTTP %s fetching FOS page", resp.status_code)
            return None
    except Exception as e:
        logger.error("Network error fetching FOS page: %s", e)
        return None


def extract_table(html: str) -> list[dict] | None:
    soup = BeautifulSoup(html, "html.parser")

    table = soup.find("table")
    if not table:
        logger.error("No table element found on FOS page")
        return None

    rows = table.find_all("tr")
    if len(rows) < 2:
        logger.error("Table has fewer than 2 rows (no data)")
        return None

    header_cells = rows[0].find_all(["th", "td"])
    headers = [h.get_text(strip=True) for h in header_cells]
    logger.info("Table headers found: %s", headers)

    records = []
    for row in rows[1:]:
        cells = row.find_all(["td", "th"])
        values = [c.get_text(strip=True) for c in cells]
        if len(values) == len(headers):
            records.append(dict(zip(headers, values)))
        elif len(values) > 0:
            logger.warning(
                "Skipping row with %s cells (expected %s): %s",
                len(values), len(headers), values[:3]
            )

    logger.info("Extracted %s rows from table", len(records))
    return records


def write_csv(records: list[dict]) -> str:
    if not records:
        logger.warning("No records to write")
        return ""

    os.makedirs(RAW_DATA_DIR, exist_ok=True)
    fieldnames = list(records[0].keys())

    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)

    logger.info("Wrote %s records to %s", len(records), OUTPUT_CSV)
    return OUTPUT_CSV


def main():
    logger.info("Starting FOS complaints data download")
    html = fetch_page()
    if not html:
        return

    records = extract_table(html)
    if not records:
        return

    write_csv(records)
    logger.info("FOS data ingestion complete")


if __name__ == "__main__":
    main()
