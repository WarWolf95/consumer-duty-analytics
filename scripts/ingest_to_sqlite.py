# C:\Projects\consumer-duty-analytics\scripts\ingest_to_sqlite.py
"""
Ingests raw FCA, FOS, and ONS datasets into SQLite staging tables.
Adheres to PEP 8 standards and logs progress detailing parsed row/column shapes.
"""

import os
import sqlite3
import pandas as pd
import numpy as np
from scripts.config import RAW_DATA_DIR, SQLITE_DB_PATH
from scripts.utils import setup_logging, get_db_connection

logger = setup_logging("ingest_to_sqlite")


INVALID_CELL_VALUES = {"*", "", "None", "NaN", "\xa0", "-", "N/A"}

def clean_cell_value(val):
    """Replaces empty strings, asterisks, and non-breaking spaces with None."""
    if pd.isna(val) or str(val).strip() in INVALID_CELL_VALUES:
        return None
    return val



def clean_df_values(df: pd.DataFrame) -> pd.DataFrame:
    """Applies cell cleaning across all columns in a DataFrame."""
    return df.map(clean_cell_value)


def ingest_fca_complaints(conn: sqlite3.Connection):
    """Parses and ingests firm-level complaints data worksheets."""
    file_path = os.path.join(RAW_DATA_DIR, "fca_firm_complaints_2025_h2.xlsx")
    if not os.path.exists(file_path):
        logger.error("FCA Complaints spreadsheet missing: %s", file_path)
        return

    sheets_to_tables = {
        "Opened": "stage_fca_complaints_opened",
        "Closed": "stage_fca_complaints_closed",
        "Percentage upheld": "stage_fca_complaints_upheld",
        "Percentage within 3 days": "stage_fca_complaints_speed_3d",
        "Percentage after 3 days, within": "stage_fca_complaints_speed_8w",
    }

    logger.info("Ingesting FCA Firm Complaints from %s", os.path.basename(file_path))

    for sheet, table in sheets_to_tables.items():
        try:
            df = pd.read_excel(file_path, sheet_name=sheet)
            # Standardise column names to snake_case
            df.columns = [
                c.strip()
                .lower()
                .replace(" ", "_")
                .replace("&", "and")
                .replace(",", "")
                for c in df.columns
            ]
            df = clean_df_values(df)

            # Ingest to SQLite
            df.to_sql(table, conn, if_exists="replace", index=False)
            logger.info("Loaded sheet '%s' into table '%s' (%d rows)", sheet, table, len(df))
        except Exception as e:
            logger.error("Failed to ingest sheet '%s': %s", sheet, e)


def ingest_fca_gi_value_measures(conn: sqlite3.Connection):
    """Parses and ingests FCA General Insurance Value Measures."""
    file_path = os.path.join(RAW_DATA_DIR, "fca_gi_value_measures_2024.xlsx")
    if not os.path.exists(file_path):
        logger.error("FCA GI Value Measures spreadsheet missing: %s", file_path)
        return

    logger.info("Ingesting FCA GI Value Measures from %s", os.path.basename(file_path))

    try:
        # Row 10 (index 9) contains column headers. Skip first 9 rows.
        df = pd.read_excel(file_path, sheet_name="Product Table", skiprows=9, header=None)

        # Expected columns matching 2023/2024 layout
        col_names = [
            "product_category",
            "claims_frequency_2023", "claims_frequency_2024",
            "claims_acceptance_rate_2023", "claims_acceptance_rate_2024",
            "avg_claims_payout_2023", "avg_claims_payout_2024",
            "claim_complaints_pct_claims_2023", "claim_complaints_pct_claims_2024",
            "avg_policies_in_force_2023", "avg_policies_in_force_2024",
            "total_premiums_2023", "total_premiums_2024",
            "claims_ratio_2023", "claims_ratio_2024",
        ]
        
        # Handle cases where excel column count differs
        col_count = df.shape[1]
        df.columns = col_names[:col_count]

        # First two rows of df after skip contain subheaders/year row
        df = df.iloc[2:].reset_index(drop=True)
        df = clean_df_values(df)

        # Remove rows without product category or where category is blank
        df = df[df["product_category"].notna()].reset_index(drop=True)

        df.to_sql("stage_fca_gi_value_measures", conn, if_exists="replace", index=False)
        logger.info("Loaded GI Value Measures into table 'stage_fca_gi_value_measures' (%d rows)", len(df))
    except Exception as e:
        logger.error("Failed to ingest GI Value Measures: %s", e)


def ingest_fca_product_sales(conn: sqlite3.Connection):
    """Ingests pure protection sales volume aggregates."""
    file_path = os.path.join(RAW_DATA_DIR, "fca_product_sales_pure_protection_2024.xlsx")
    if not os.path.exists(file_path):
        logger.error("FCA Pure Protection sales file missing: %s", file_path)
        return

    logger.info("Ingesting FCA Product Sales Pure Protection from %s", os.path.basename(file_path))

    try:
        df = pd.read_excel(file_path, sheet_name="PSD PPC Quarterly Data")
        df.columns = [
            c.strip().lower().replace(" ", "_").replace("(", "").replace(")", "")
            for c in df.columns
        ]
        df = clean_df_values(df)

        df.to_sql("stage_fca_product_sales", conn, if_exists="replace", index=False)
        logger.info("Loaded Product Sales into table 'stage_fca_product_sales' (%d rows)", len(df))
    except Exception as e:
        logger.error("Failed to ingest Product Sales Data: %s", e)


def ingest_fos_complaints(conn: sqlite3.Connection):
    """Ingests Ombudsman decision aggregates and upholds."""
    file_path = os.path.join(RAW_DATA_DIR, "fos_complaints_2025_26.csv")
    if not os.path.exists(file_path):
        logger.error("FOS complaints CSV missing: %s", file_path)
        return

    logger.info("Ingesting FOS Complaints from %s", os.path.basename(file_path))

    try:
        df = pd.read_csv(file_path, encoding="utf-8-sig")
        df.columns = [
            c.strip().lower().replace(" ", "_").replace("%", "pct")
            for c in df.columns
        ]
        df = clean_df_values(df)

        # Convert uphold_pct string to decimal float (e.g. "45%" to 0.45)
        def clean_uphold_pct(x):
            if x is None:
                return None
            x_str = str(x).replace("%", "").strip()
            try:
                return float(x_str) / 100.0
            except ValueError:
                return None

        df["uphold_pct"] = df["uphold_pct"].apply(clean_uphold_pct)

        # Convert new_cases to integer
        def clean_int(x):
            if x is None:
                return None
            try:
                return int(str(x).replace(",", "").strip())
            except ValueError:
                return None

        df["new_cases"] = df["new_cases"].apply(clean_int)

        df.to_sql("stage_fos_complaints", conn, if_exists="replace", index=False)
        logger.info("Loaded FOS Complaints into table 'stage_fos_complaints' (%d rows)", len(df))
    except Exception as e:
        logger.error("Failed to ingest FOS Complaints: %s", e)


def ingest_ons_population(conn: sqlite3.Connection):
    """Ingests regional ONS population data for vulnerability weights."""
    file_path = os.path.join(RAW_DATA_DIR, "ons_population_england_wales_mid2024.xlsx")
    if not os.path.exists(file_path):
        logger.error("ONS Population Estimates spreadsheet missing: %s", file_path)
        return

    logger.info("Ingesting ONS Population data from %s", os.path.basename(file_path))

    try:
        df = pd.read_excel(file_path, sheet_name="MYE2 - Persons", skiprows=7)
        df.columns = [str(c).strip() for c in df.columns]
        
        # Select key columns
        df = df[["Code", "Name", "Geography", "All ages"]]
        df.columns = ["code", "name", "geography", "all_ages"]

        df = clean_df_values(df)
        df = df[df["geography"].isin(["Region", "Country"])].reset_index(drop=True)

        df.to_sql("stage_ons_population", conn, if_exists="replace", index=False)
        logger.info("Loaded ONS Population data into table 'stage_ons_population' (%d rows)", len(df))
    except Exception as e:
        logger.error("Failed to ingest ONS Population: %s", e)


def main():
    logger.info("Starting staging data ingestion into SQLite...")
    
    # Establish connection
    conn = get_db_connection()
    try:
        ingest_fca_complaints(conn)
        ingest_fca_gi_value_measures(conn)
        ingest_fca_product_sales(conn)
        ingest_fos_complaints(conn)
        ingest_ons_population(conn)
        logger.info("Staging ingestion complete. Staged data is verified.")
    except Exception as e:
        logger.critical("Critical pipeline error during ingestion: %s", e)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
