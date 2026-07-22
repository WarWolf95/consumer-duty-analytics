# C:\Projects\consumer-duty-analytics\tests\test_db.py
"""
Pytest suite verifying SQLite database integrity, schema structures, row counts,
referential integrity, and calibration benchmarks.
"""

import sqlite3
import pytest
from scripts.config import SQLITE_DB_PATH


@pytest.fixture
def db_conn():
    """Provides a connection to the analytical SQLite database."""
    conn = sqlite3.connect(SQLITE_DB_PATH)
    conn.row_factory = sqlite3.Row
    yield conn
    conn.close()


def test_staging_tables_exist(db_conn):
    """Verifies that all raw staging tables were successfully created."""
    cursor = db_conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row["name"] for row in cursor.fetchall()]

    staging_tables = [
        "stage_fca_complaints_opened",
        "stage_fca_complaints_closed",
        "stage_fca_complaints_upheld",
        "stage_fca_complaints_speed_3d",
        "stage_fca_complaints_speed_8w",
        "stage_fca_gi_value_measures",
        "stage_fca_product_sales",
        "stage_fos_complaints",
        "stage_ons_population",
    ]

    for table in staging_tables:
        assert table in tables, f"Staging table '{table}' is missing from the database."


def test_star_schema_tables_exist(db_conn):
    """Verifies that all star schema dimension and fact tables exist."""
    cursor = db_conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row["name"] for row in cursor.fetchall()]

    star_tables = [
        "dim_customer",
        "dim_product",
        "dim_calendar",
        "dim_outcome_area",
        "fact_products",
        "fact_complaints",
    ]

    for table in star_tables:
        assert table in tables, f"Star schema table '{table}' is missing from the database."


def test_analytical_views_exist(db_conn):
    """Verifies that all regulatory outcome aggregate views exist."""
    cursor = db_conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='view'")
    views = [row["name"] for row in cursor.fetchall()]

    expected_views = [
        "v_outcome_consumer_support",
        "v_outcome_price_value",
        "v_outcome_products_services",
        "v_vulnerable_disparity",
    ]

    for view in expected_views:
        assert view in views, f"Analytical view '{view}' is missing from the database."


def test_row_counts(db_conn):
    """Asserts exact target row counts for dimensions and facts."""
    cursor = db_conn.cursor()

    # 1. Customers
    cursor.execute("SELECT COUNT(*) FROM dim_customer")
    customers_count = cursor.fetchone()[0]
    assert customers_count == 50000, f"Expected 50,000 customers, got {customers_count}."

    # 2. Products
    cursor.execute("SELECT COUNT(*) FROM dim_product")
    products_count = cursor.fetchone()[0]
    assert products_count > 0, "Expected product catalog to be populated."

    # 3. Calendar
    cursor.execute("SELECT COUNT(*) FROM dim_calendar")
    calendar_count = cursor.fetchone()[0]
    # 2024 (leap year = 366 days) + 2025 (365 days) = 731 days
    assert calendar_count == 731, f"Expected 731 calendar days, got {calendar_count}."

    # 4. Product Sales Facts
    cursor.execute("SELECT COUNT(*) FROM fact_products")
    sales_count = cursor.fetchone()[0]
    assert sales_count == 75000, f"Expected 75,000 policy sales, got {sales_count}."

    # 5. Complaints Facts
    cursor.execute("SELECT COUNT(*) FROM fact_complaints")
    complaints_count = cursor.fetchone()[0]
    assert complaints_count == 10000, f"Expected 10,000 complaint cases, got {complaints_count}."


def test_referential_integrity(db_conn):
    """Verifies that fact tables do not contain orphaned foreign key relationships."""
    cursor = db_conn.cursor()

    # check fact_products references
    cursor.execute("""
        SELECT COUNT(*) FROM fact_products f
        LEFT JOIN dim_customer c ON f.customer_id = c.customer_id
        WHERE c.customer_id IS NULL
    """)
    orphaned_customers = cursor.fetchone()[0]
    assert orphaned_customers == 0, f"Found {orphaned_customers} orphaned customers in fact_products."

    cursor.execute("""
        SELECT COUNT(*) FROM fact_products f
        LEFT JOIN dim_product p ON f.product_id = p.product_id
        WHERE p.product_id IS NULL
    """)
    orphaned_products = cursor.fetchone()[0]
    assert orphaned_products == 0, f"Found {orphaned_products} orphaned products in fact_products."

    # check fact_complaints references
    cursor.execute("""
        SELECT COUNT(*) FROM fact_complaints comp
        LEFT JOIN dim_customer c ON comp.customer_id = c.customer_id
        WHERE c.customer_id IS NULL
    """)
    orphaned_complaint_customers = cursor.fetchone()[0]
    assert orphaned_complaint_customers == 0, f"Found {orphaned_complaint_customers} orphaned customers in fact_complaints."

    cursor.execute("""
        SELECT COUNT(*) FROM fact_complaints comp
        LEFT JOIN dim_product p ON comp.product_id = p.product_id
        WHERE p.product_id IS NULL
    """)
    orphaned_complaint_products = cursor.fetchone()[0]
    assert orphaned_complaint_products == 0, f"Found {orphaned_complaint_products} orphaned products in fact_complaints."


def test_vulnerability_calibration(db_conn):
    """Validates that customer vulnerability flags are calibrated to the ~47% survey rate."""
    cursor = db_conn.cursor()
    cursor.execute("SELECT SUM(vulnerability_flag) * 1.0 / COUNT(*) FROM dim_customer")
    vuln_rate = cursor.fetchone()[0]
    
    # Assert vulnerability rate is between 45% and 49% (surrounding the 47% survey target)
    assert 0.45 <= vuln_rate <= 0.49, f"Vulnerability rate {vuln_rate:.2%} is out of bounds."


def test_regional_distribution_calibration(db_conn):
    """Validates that customers are generated according to ONS geographic weights."""
    cursor = db_conn.cursor()
    
    cursor.execute("SELECT region, COUNT(*) as count FROM dim_customer GROUP BY region")
    rows = cursor.fetchall()
    counts = {r["region"]: r["count"] for r in rows}
    total = sum(counts.values())

    # Verify that London and South East represent the largest portions of the customer base
    london_share = counts.get("London", 0) / total
    se_share = counts.get("South East", 0) / total
    ni_share = counts.get("Northern Ireland", 0) / total
    
    assert 0.11 <= london_share <= 0.15, f"London share {london_share:.2%} is out of ONS calibration ranges."
    assert 0.12 <= se_share <= 0.16, f"South East share {se_share:.2%} is out of ONS calibration ranges."
    assert 0.01 <= ni_share <= 0.04, f"Northern Ireland share {ni_share:.2%} is out of calibration ranges."


def test_conduct_risk_disparity_calibration(db_conn):
    """Verifies that the generated data contains the built-in vulnerable customer outcome disparities."""
    cursor = db_conn.cursor()
    
    # Query resolution speed SLA from v_vulnerable_disparity
    cursor.execute("""
        SELECT vulnerability_flag, AVG(avg_complaint_resolution_days) as avg_days
        FROM v_vulnerable_disparity
        GROUP BY vulnerability_flag
    """)
    rows = cursor.fetchall()
    disparities = {r["vulnerability_flag"]: r["avg_days"] for r in rows}
    
    # Vulnerable cohort (vulnerability_flag = 1) should have a higher average resolution time
    vuln_days = disparities.get(1)
    non_vuln_days = disparities.get(0)
    
    assert vuln_days > non_vuln_days, f"Expected vulnerable customers to face longer resolution times. Got: Vuln={vuln_days:.2f} days, Non-Vuln={non_vuln_days:.2f} days."
