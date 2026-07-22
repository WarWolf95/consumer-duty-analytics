# C:\Projects\consumer-duty-analytics\scripts\utils.py
"""
Shared utilities for the Consumer Duty Outcome Monitoring project.
Handles logging, database connection management, and DataFrame handling.
"""

import os
import sys
import logging
import sqlite3
import pandas as pd
from datetime import datetime
from scripts.config import REPORTS_DIR, SQLITE_DB_PATH

def setup_logging(script_name: str) -> logging.Logger:
    """Sets up standard logger printing to console and appending to file in reports/."""
    log_file = os.path.join(REPORTS_DIR, "pipeline_execution.log")
    
    logger = logging.getLogger(script_name)
    logger.setLevel(logging.INFO)
    
    # Avoid duplicate handlers if logger is already set up
    if logger.handlers:
        return logger
        
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | [%(name)s] | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File Handler
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger

def get_db_connection() -> sqlite3.Connection:
    """Returns a connection to the SQLite analytical database. Creates directories if missing."""
    os.makedirs(os.path.dirname(SQLITE_DB_PATH), exist_ok=True)
    conn = sqlite3.connect(SQLITE_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def execute_sql(sql: str, params: tuple = None) -> None:
    """Executes a single raw SQL query (DDL or DML)."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        if params:
            cursor.execute(sql, params)
        else:
            cursor.execute(sql)
        conn.commit()

def run_query(sql: str, params: tuple = None) -> pd.DataFrame:
    """Executes a SELECT query and returns a pandas DataFrame."""
    with get_db_connection() as conn:
        return pd.read_sql_query(sql, conn, params=params)

def safe_write_dataframe(df: pd.DataFrame, file_path: str, index: bool = False) -> None:
    """Saves a pandas DataFrame to CSV with directory checks and standard error handling."""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    df.to_csv(file_path, index=index, encoding="utf-8")

def download_file(filename: str, url: str, target_dir: str, logger: logging.Logger, headers: dict = None, timeout: int = 60) -> bool:
    """Downloads a file from a URL to target_dir with status logging."""
    import requests
    target_path = os.path.join(target_dir, filename)
    logger.info("Downloading %s from %s", filename, url)
    try:
        resp = requests.get(url, headers=headers or {}, stream=True, timeout=timeout)
        if resp.status_code == 200:
            with open(target_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            size_kb = os.path.getsize(target_path) / 1024
            logger.info("Downloaded %s (%.1f KB)", filename, size_kb)
            return True
        logger.error("HTTP %s for %s", resp.status_code, filename)
        return False
    except Exception as e:
        logger.error("Network error downloading %s: %s", filename, e)
        return False

def inspect_xlsx(filename: str, target_dir: str, logger: logging.Logger, max_sheets: int = 3):
    """Logs worksheet metadata and sample top rows for an Excel workbook."""
    import openpyxl
    target_path = os.path.join(target_dir, filename)
    if not os.path.exists(target_path):
        logger.warning("File %s not found — skipping inspection", filename)
        return
    try:
        wb = openpyxl.load_workbook(target_path, read_only=True, data_only=True)
        sheets = wb.sheetnames[:max_sheets] if max_sheets else wb.sheetnames
        logger.info("Inspection — %s: sheets=%s", filename, wb.sheetnames)
        for sheet_name in sheets:
            ws = wb[sheet_name]
            for row_idx, row in enumerate(ws.iter_rows(max_row=3, values_only=True), 1):
                non_none = [str(c)[:60] if c is not None else "" for c in row]
                logger.info("  %s row %s: %s", sheet_name, row_idx, " | ".join(non_none))
        wb.close()
    except Exception as e:
        logger.error("Failed to inspect %s: %s", filename, e)

