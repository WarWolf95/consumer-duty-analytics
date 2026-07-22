from scripts.config import RAW_DATA_DIR
from scripts.utils import setup_logging, download_file, inspect_xlsx

logger = setup_logging("fetch_ons_data")

ONS_DATASETS = {
    "ons_population_england_wales_mid2024.xlsx": (
        "https://www.ons.gov.uk/file?uri=/peoplepopulationandcommunity/"
        "populationandmigration/populationestimates/datasets/"
        "estimatesofthepopulationforenglandandwales/"
        "mid20242023localauthorityboundaries/mye24tablesew.xlsx"
    ),
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


def main():
    logger.info("Starting ONS population data download")
    for filename, url in ONS_DATASETS.items():
        if download_file(filename, url, RAW_DATA_DIR, logger, HEADERS, timeout=120):
            inspect_xlsx(filename, RAW_DATA_DIR, logger, max_sheets=3)
        else:
            logger.warning("Failed to download %s", filename)

    logger.info("ONS data ingestion complete")


if __name__ == "__main__":
    main()

