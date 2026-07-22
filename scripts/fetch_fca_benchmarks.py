from scripts.config import RAW_DATA_DIR
from scripts.utils import setup_logging, download_file, inspect_xlsx

logger = setup_logging("fetch_fca_benchmarks")

DATASETS = {
    "fca_firm_complaints_2025_h2.xlsx": (
        "https://www.fca.org.uk/publication/data/firm-level-complaints-data-2025-h2.xlsx"
    ),
    "fca_gi_value_measures_2024.xlsx": (
        "https://www.fca.org.uk/publication/data/gi-value-measures-data-2024.xlsx"
    ),
    "fca_product_sales_pure_protection_2024.xlsx": (
        "https://www.fca.org.uk/publication/data/product-sales-data-pure-protection-contracts-2024.xlsx"
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
    logger.info("Starting FCA benchmark data ingestion")
    all_ok = True

    for filename, url in DATASETS.items():
        if download_file(filename, url, RAW_DATA_DIR, logger, HEADERS):
            inspect_xlsx(filename, RAW_DATA_DIR, logger, max_sheets=None)
        else:
            all_ok = False

    if all_ok:
        logger.info("All FCA datasets downloaded successfully")
    else:
        logger.warning("One or more FCA datasets failed to download — check logs")


if __name__ == "__main__":
    main()

