# C:\Projects\consumer-duty-analytics\scripts\build_star_schema.py
"""
Builds the analytical Star Schema in SQLite and populates it with calibrated
synthetic customer portfolios and operational data.
Adheres to PEP 8 standards and logs execution metrics.
"""

import os
import sqlite3
import random
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from scripts.config import (
    REGIONS,
    PRODUCT_CATEGORIES,
    DISTRIBUTION_CHANNELS,
    VULNERABILITY_CATEGORIES,
    COMPLAINT_CATEGORIES,
    COMPLAINT_OUTCOMES,
    CANCELLATION_REASONS,
    REGULATORY_KPI_THRESHOLDS,
)
from scripts.utils import setup_logging, get_db_connection, execute_sql

logger = setup_logging("build_star_schema")

# Set random seeds for reproducibility
random.seed(42)
np.random.seed(42)


def create_schema(conn: sqlite3.Connection):
    """Drops existing tables and creates the Star Schema tables and analytical views."""
    cursor = conn.cursor()

    logger.info("Dropping existing star schema tables and views...")
    # Drop views
    cursor.execute("DROP VIEW IF EXISTS v_outcome_products_services")
    cursor.execute("DROP VIEW IF EXISTS v_outcome_price_value")
    cursor.execute("DROP VIEW IF EXISTS v_outcome_consumer_support")
    cursor.execute("DROP VIEW IF EXISTS v_vulnerable_disparity")

    # Drop tables
    cursor.execute("DROP TABLE IF EXISTS fact_complaints")
    cursor.execute("DROP TABLE IF EXISTS fact_products")
    cursor.execute("DROP TABLE IF EXISTS dim_outcome_area")
    cursor.execute("DROP TABLE IF EXISTS dim_calendar")
    cursor.execute("DROP TABLE IF EXISTS dim_product")
    cursor.execute("DROP TABLE IF EXISTS dim_customer")

    logger.info("Creating Star Schema table structures...")

    # 1. dim_customer
    cursor.execute("""
        CREATE TABLE dim_customer (
            customer_id TEXT PRIMARY KEY,
            age_band TEXT NOT NULL,
            region TEXT NOT NULL,
            tenure_years INTEGER NOT NULL,
            vulnerability_flag INTEGER NOT NULL CHECK (vulnerability_flag IN (0, 1)),
            vulnerability_type TEXT,
            vulnerability_detail TEXT
        )
    """)

    # 2. dim_product
    cursor.execute("""
        CREATE TABLE dim_product (
            product_id TEXT PRIMARY KEY,
            product_category TEXT NOT NULL,
            product_name TEXT NOT NULL,
            distribution_channel TEXT NOT NULL,
            launch_date TEXT NOT NULL,
            status TEXT NOT NULL CHECK (status IN ('Open', 'Closed', 'Withdrawn'))
        )
    """)

    # 3. dim_calendar
    cursor.execute("""
        CREATE TABLE dim_calendar (
            date_str TEXT PRIMARY KEY,
            year INTEGER NOT NULL,
            quarter TEXT NOT NULL,
            month INTEGER NOT NULL,
            short_month TEXT NOT NULL,
            reporting_period TEXT NOT NULL
        )
    """)

    # 4. dim_outcome_area
    cursor.execute("""
        CREATE TABLE dim_outcome_area (
            outcome_id TEXT PRIMARY KEY,
            outcome_area TEXT NOT NULL,
            kpi_category TEXT NOT NULL,
            regulatory_threshold REAL
        )
    """)

    # 5. fact_products (sales, claims, and cancellations)
    cursor.execute("""
        CREATE TABLE fact_products (
            sale_id TEXT PRIMARY KEY,
            customer_id TEXT NOT NULL,
            product_id TEXT NOT NULL,
            sale_date TEXT NOT NULL,
            premium_or_fee REAL NOT NULL,
            commission_amount REAL NOT NULL,
            cancellation_date TEXT,
            cancellation_reason TEXT,
            claims_made_count INTEGER DEFAULT 0,
            claims_paid_amount REAL DEFAULT 0.0,
            claims_declined_count INTEGER DEFAULT 0,
            FOREIGN KEY (customer_id) REFERENCES dim_customer (customer_id),
            FOREIGN KEY (product_id) REFERENCES dim_product (product_id),
            FOREIGN KEY (sale_date) REFERENCES dim_calendar (date_str),
            FOREIGN KEY (cancellation_date) REFERENCES dim_calendar (date_str)
        )
    """)

    # 6. fact_complaints
    cursor.execute("""
        CREATE TABLE fact_complaints (
            complaint_id TEXT PRIMARY KEY,
            customer_id TEXT NOT NULL,
            product_id TEXT NOT NULL,
            complaint_date TEXT NOT NULL,
            resolved_date TEXT,
            complaint_category TEXT NOT NULL,
            complaint_outcome TEXT NOT NULL CHECK (complaint_outcome IN ('Upheld', 'Partially Upheld', 'Not Upheld')),
            days_to_resolve INTEGER,
            redress_amount REAL DEFAULT 0.0,
            complaint_source TEXT NOT NULL CHECK (complaint_source IN ('Direct', 'FOS Referral')),
            FOREIGN KEY (customer_id) REFERENCES dim_customer (customer_id),
            FOREIGN KEY (product_id) REFERENCES dim_product (product_id),
            FOREIGN KEY (complaint_date) REFERENCES dim_calendar (date_str),
            FOREIGN KEY (resolved_date) REFERENCES dim_calendar (date_str)
        )
    """)

    conn.commit()
    logger.info("Star Schema table structures created successfully.")


def generate_dim_calendar(conn: sqlite3.Connection):
    """Generates dates from 2024-01-01 to 2025-12-31 and populates dim_calendar."""
    logger.info("Generating date dimensions for dim_calendar...")
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2025, 12, 31)
    delta = timedelta(days=1)

    calendar_data = []
    current = start_date
    while current <= end_date:
        date_str = current.strftime("%Y-%m-%d")
        year = current.year
        month = current.month
        short_month = current.strftime("%b")
        quarter = f"Q{((current.month - 1) // 3) + 1}-{year}"
        # Consumer duty reporting quarter
        reporting_period = f"CD-{quarter}"
        
        calendar_data.append((date_str, year, quarter, month, short_month, reporting_period))
        current += delta

    cursor = conn.cursor()
    cursor.executemany(
        "INSERT INTO dim_calendar VALUES (?, ?, ?, ?, ?, ?)",
        calendar_data
    )
    conn.commit()
    logger.info("Loaded %d calendar days.", len(calendar_data))


def generate_dim_outcome_area(conn: sqlite3.Connection):
    """Populates the dim_outcome_area dimensions table."""
    logger.info("Populating dim_outcome_area...")
    outcomes = [
        ("OUT_PRD", "Products & Services", "Product concentration limit", REGULATORY_KPI_THRESHOLDS["target_sales_concentration_limit"]),
        ("OUT_VAL", "Price & Value", "Early cancellation rate cap", REGULATORY_KPI_THRESHOLDS["target_early_cancellation_rate"]),
        ("OUT_SUP_VOL", "Consumer Support", "Complaint rate per 1,000 policies", REGULATORY_KPI_THRESHOLDS["target_complaints_per_1000_policies"]),
        ("OUT_SUP_RES", "Consumer Support", "Average resolution days SLA", REGULATORY_KPI_THRESHOLDS["target_avg_resolution_days"]),
        ("OUT_SUP_UPH", "Consumer Support", "FCA uphold benchmark", REGULATORY_KPI_THRESHOLDS["fca_uphold_rate_benchmark"]),
        ("OUT_VUL_DIS", "Cross-cutting Outcomes", "Vulnerable cohort outcome disparity", REGULATORY_KPI_THRESHOLDS["target_vulnerable_outcome_disparity"]),
    ]

    cursor = conn.cursor()
    cursor.executemany(
        "INSERT INTO dim_outcome_area VALUES (?, ?, ?, ?)",
        outcomes
    )
    conn.commit()
    logger.info("Loaded %d outcome area mappings.", len(outcomes))


def get_regional_weights(conn: sqlite3.Connection) -> dict:
    """Calculates population weights by querying ONS data, filling Scotland/N.Ireland."""
    logger.info("Calculating region weights from staged ONS population data...")
    cursor = conn.cursor()
    
    # Query ONS Region/Country rows
    cursor.execute("SELECT name, all_ages FROM stage_ons_population")
    rows = cursor.fetchall()
    
    raw_pop = {}
    total_ons_pop = 0
    for row in rows:
        name = row["name"].upper()
        # Filter for England regions and Wales
        if name in ["ENGLAND AND WALES", "ENGLAND"]:
            continue
        pop = row["all_ages"]
        raw_pop[name] = pop
        total_ons_pop += pop
        
    # Map ONS names to config.REGIONS names
    mapped_pop = {
        "London": raw_pop.get("LONDON", 9089736),
        "South East": raw_pop.get("SOUTH EAST", 9642942),
        "South West": raw_pop.get("SOUTH WEST", 5889695),
        "East of England": raw_pop.get("EAST", 6576306),
        "West Midlands": raw_pop.get("WEST MIDLANDS", 6187204),
        "East Midlands": raw_pop.get("EAST MIDLANDS", 5063164),
        "Yorkshire and the Humber": raw_pop.get("YORKSHIRE AND THE HUMBER", 5672962),
        "North West": raw_pop.get("NORTH WEST", 7737414),
        "North East": raw_pop.get("NORTH EAST", 2760678),
        "Wales": raw_pop.get("WALES", 3186581),
        # Calibrated estimates for Scotland and N.Ireland which are outside ONS England/Wales file
        "Scotland": 5440000,
        "Northern Ireland": 1910000
    }
    
    total_pop = sum(mapped_pop.values())
    weights = {k: v / total_pop for k, v in mapped_pop.items()}
    logger.info("Calibrated UK regional weights: %s", {k: f"{v*100:.2f}%" for k, v in weights.items()})
    return weights


def generate_dim_customer(conn: sqlite3.Connection, num_customers: int = 50000):
    """Generates calibrated customer profiles matching ONS regional and FCA vulnerability stats."""
    logger.info("Generating %d synthetic customer profiles...", num_customers)
    
    region_weights = get_regional_weights(conn)
    regions_list = list(region_weights.keys())
    regions_probs = list(region_weights.values())
    
    age_bands = ["18-29", "30-49", "50-64", "65+"]
    age_probs = [0.18, 0.35, 0.27, 0.20]
    
    # Financial Lives survey target (~47% of UK consumers show vulnerability characteristics)
    vulnerability_pct = 0.47
    
    vuln_types = list(VULNERABILITY_CATEGORIES.keys())
    
    customers = []
    for i in range(1, num_customers + 1):
        cust_id = f"C{i:05d}"
        age = np.random.choice(age_bands, p=age_probs)
        region = np.random.choice(regions_list, p=regions_probs)
        tenure = random.randint(1, 15)
        
        is_vulnerable = 1 if random.random() < vulnerability_pct else 0
        v_type = None
        v_detail = None
        
        if is_vulnerable:
            # Pick a core vulnerability type (Health, Resilience, etc.)
            v_type = random.choice(vuln_types)
            v_detail = random.choice(VULNERABILITY_CATEGORIES[v_type])
            
        customers.append((cust_id, age, region, tenure, is_vulnerable, v_type, v_detail))

    cursor = conn.cursor()
    cursor.executemany(
        "INSERT INTO dim_customer VALUES (?, ?, ?, ?, ?, ?, ?)",
        customers
    )
    conn.commit()
    logger.info("Loaded %d customer profiles into dim_customer.", len(customers))


def generate_dim_product(conn: sqlite3.Connection):
    """Generates standard products catalog based on config PRODUCT_CATEGORIES."""
    logger.info("Generating product catalog for dim_product...")
    
    # Expand PRODUCT_CATEGORIES into specific products with codes and channels
    products_data = []
    prod_id_counter = 1
    
    for category, name_list in PRODUCT_CATEGORIES.items():
        for name in name_list:
            # We want each product category to be distributed through appropriate channels
            if category == "General Insurance":
                channels = ["Direct", "Broker", "Digital Platform"]
            elif category == "Retail Banking":
                channels = ["Direct", "Digital Platform"]
            else: # Protection
                channels = ["Direct", "Tied Agent"]
                
            for channel in channels:
                prod_id = f"P{prod_id_counter:03d}"
                status = "Open"
                
                # Make some products closed to model Consumer Duty closed book rules
                if prod_id_counter in [2, 7]: 
                    status = "Closed"
                elif prod_id_counter in [12]:
                    status = "Withdrawn"
                    
                launch_date = (datetime(2020, 1, 1) + timedelta(days=random.randint(1, 1000))).strftime("%Y-%m-%d")
                
                products_data.append((prod_id, category, name, channel, launch_date, status))
                prod_id_counter += 1

    cursor = conn.cursor()
    cursor.executemany(
        "INSERT INTO dim_product VALUES (?, ?, ?, ?, ?, ?)",
        products_data
    )
    conn.commit()
    logger.info("Loaded %d products into dim_product.", len(products_data))


def get_gi_benchmarks(conn: sqlite3.Connection) -> dict:
    """Reads FCA General Insurance value measures to return benchmark rates for GI products."""
    logger.info("Fetching General Insurance value measures from SQLite...")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT product_category, claims_frequency_2024, claims_acceptance_rate_2024, avg_claims_payout_2024
        FROM stage_fca_gi_value_measures
    """)
    rows = cursor.fetchall()
    
    benchmarks = {}
    for r in rows:
        cat = r["product_category"]
        benchmarks[cat] = {
            "freq": r["claims_frequency_2024"],
            "acceptance": r["claims_acceptance_rate_2024"],
            "payout": r["avg_claims_payout_2024"]
        }
        
    return benchmarks


def generate_fact_products(conn: sqlite3.Connection, num_sales_target: int = 75000):
    """Generates policy sales records, calibrates claims/cancellations to GI measures."""
    logger.info("Generating %d product portfolios...", num_sales_target)
    cursor = conn.cursor()
    
    # Retrieve product catalog
    cursor.execute("SELECT product_id, product_category, product_name, distribution_channel FROM dim_product")
    products = cursor.fetchall()
    gi_benchmarks = get_gi_benchmarks(conn)
    
    # Retrive customers and their vulnerability indicators
    cursor.execute("SELECT customer_id, vulnerability_flag FROM dim_customer")
    customers = cursor.fetchall()
    
    # We will iterate through customers and assign 1 to 3 products
    sales = []
    sale_counter = 1
    
    # Set dates range: 2024-01-01 to 2025-12-31
    start_date = datetime(2024, 1, 1)
    
    for customer in customers:
        cust_id, is_vulnerable = customer
        num_products = random.randint(1, 3)
        cust_prods = random.sample(products, num_products)
        
        for prod in cust_prods:
            if sale_counter > num_sales_target:
                break
                
            sale_id = f"S{sale_counter:06d}"
            prod_id, prod_cat, prod_name, channel = prod
            
            # Sale date
            sale_date = (start_date + timedelta(days=random.randint(0, 700))).strftime("%Y-%m-%d")
            
            # Premium pricing (calibrated base rates)
            if prod_name == "Motor Insurance":
                base_prem = random.uniform(500, 1100)
            elif prod_name == "Home Insurance":
                base_prem = random.uniform(250, 600)
            elif prod_name == "Travel Insurance":
                base_prem = random.uniform(60, 200)
            elif prod_name == "Pet Insurance":
                base_prem = random.uniform(180, 500)
            elif prod_name == "Reward Credit Card":
                base_prem = 120.0 # Annual fee
            elif prod_name == "Term Life Insurance":
                base_prem = random.uniform(240, 600) # Annualized
            elif prod_name == "Guaranteed Income Bond":
                base_prem = random.uniform(10000, 50000) # Principal deposit
            else:
                base_prem = 0.0 # Savings / ISA
                
            # Direct/Digital Platform has minimal commission. Broker/Agent has high.
            commission = 0.0
            if channel == "Broker":
                if prod_name == "Motor Insurance":
                    commission = base_prem * random.uniform(0.08, 0.12)
                elif prod_name == "Home Insurance":
                    commission = base_prem * random.uniform(0.15, 0.22)
                elif prod_name == "Travel Insurance":
                    commission = base_prem * random.uniform(0.25, 0.38) # Unfair Value alert indicator!
                elif prod_name == "Pet Insurance":
                    commission = base_prem * random.uniform(0.15, 0.25)
            elif channel == "Tied Agent":
                commission = base_prem * random.uniform(0.18, 0.30)
                
            # Cancellations
            cancellation_date = None
            cancellation_reason = None
            
            # Vulnerable customers might have slightly higher early lapse rates due to financial hardship (disparity modeling)
            cancel_prob = 0.08 if is_vulnerable else 0.05
            if random.random() < cancel_prob:
                cancel_days = random.randint(15, 300)
                c_date = datetime.strptime(sale_date, "%Y-%m-%d") + timedelta(days=cancel_days)
                if c_date <= datetime(2025, 12, 31):
                    cancellation_date = c_date.strftime("%Y-%m-%d")
                    cancellation_reason = random.choice(CANCELLATION_REASONS)
                    if is_vulnerable and random.random() < 0.4:
                        cancellation_reason = "Financial Hardship"
            
            # Claims (only for General Insurance)
            claims_made = 0
            claims_paid = 0.0
            claims_declined = 0
            
            if prod_cat == "General Insurance":
                # Find the benchmark key
                bm_key = None
                if prod_name == "Motor Insurance":
                    bm_key = "Motor (All)"
                elif prod_name == "Home Insurance":
                    bm_key = "Home - (buildings and contents combined) (All)"
                elif prod_name == "Travel Insurance":
                    bm_key = "Travel - annual european (All)"
                elif prod_name == "Pet Insurance":
                    bm_key = "Pet - covered for life (All)"
                    
                bm = gi_benchmarks.get(bm_key, {"freq": 0.05, "acceptance": 0.90, "payout": 1000.0})
                
                # Claims Frequency calibration
                freq = float(bm["freq"]) if bm["freq"] is not None else 0.05
                if freq > 1.0: # represented as % (e.g. 4.9% vs 0.049)
                    freq = freq / 100.0
                    
                if random.random() < freq:
                    claims_made = 1
                    
                    # Claims Acceptance rate calibration
                    accept_rate = float(bm["acceptance"]) if bm["acceptance"] is not None else 0.90
                    if accept_rate > 1.0:
                        accept_rate = accept_rate / 100.0
                        
                    # Model a minor outcome disparity (e.g., vulnerable customers face slightly higher decline rates due to complex terms)
                    if is_vulnerable:
                        accept_rate = max(0.60, accept_rate - 0.04) # 4% lower acceptance rate
                        
                    if random.random() < accept_rate:
                        avg_payout = float(bm["payout"]) if bm["payout"] is not None else 1000.0
                        claims_paid = avg_payout * random.uniform(0.7, 1.3)
                    else:
                        claims_declined = 1
                        
            sales.append((
                sale_id, cust_id, prod_id, sale_date, base_prem, commission,
                cancellation_date, cancellation_reason, claims_made, claims_paid, claims_declined
            ))
            
            sale_counter += 1
            if sale_counter > num_sales_target:
                break
                
    cursor.executemany(
        "INSERT INTO fact_products VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        sales
    )
    conn.commit()
    logger.info("Loaded %d policy sales into fact_products.", len(sales))


def generate_fact_complaints(conn: sqlite3.Connection, num_complaints: int = 10000):
    """Generates customer complaints calibrated to FCA uphold and speed benchmarks."""
    logger.info("Generating %d complaint events...", num_complaints)
    cursor = conn.cursor()
    
    # Retrieve product sales
    cursor.execute("""
        SELECT f.sale_id, f.customer_id, f.product_id, f.sale_date, c.vulnerability_flag 
        FROM fact_products f
        JOIN dim_customer c ON f.customer_id = c.customer_id
    """)
    policies = cursor.fetchall()
    
    # Retrieve FOS product benchmarks
    cursor.execute("SELECT product, uphold_pct FROM stage_fos_complaints")
    fos_rows = cursor.fetchall()
    fos_upholds = {}
    for r in fos_rows:
        prod_lbl = r["product"].upper() if r["product"] else ""
        fos_upholds[prod_lbl] = r["uphold_pct"]
        
    complaints = []
    complaint_counter = 1
    
    # Distribute complaints
    for i in range(num_complaints):
        complaint_id = f"CPL{complaint_counter:05d}"
        
        # Select a random policy
        policy = random.choice(policies)
        sale_id, cust_id, prod_id, sale_date_str, is_vulnerable = policy
        
        # Complaint date (must be after sale)
        sale_date = datetime.strptime(sale_date_str, "%Y-%m-%d")
        comp_date = sale_date + timedelta(days=random.randint(5, 300))
        
        if comp_date > datetime(2025, 12, 31):
            comp_date = datetime(2025, 12, 30)
            
        comp_date_str = comp_date.strftime("%Y-%m-%d")
        
        category = random.choice(COMPLAINT_CATEGORIES)
        
        # Standard Uphold rates: target benchmark is 45% (0.45)
        # Model conduct risk disparity: vulnerable customer complaints might be upheld slightly more as they highlight genuine detriments (50% vs 43%)
        uphold_prob = 0.50 if is_vulnerable else 0.43
        outcome = np.random.choice(COMPLAINT_OUTCOMES, p=[uphold_prob * 0.8, uphold_prob * 0.2, 1 - uphold_prob])
        
        # Resolution speed: SLA target is 5 days (threshold)
        # Model support delays: vulnerable customers experience longer delays due to complex administrative barriers (average 6.4 days vs 4.2 days)
        if is_vulnerable:
            res_days = int(np.random.exponential(scale=6.4) + 1)
        else:
            res_days = int(np.random.exponential(scale=4.2) + 1)
            
        resolved_date = comp_date + timedelta(days=res_days)
        resolved_date_str = resolved_date.strftime("%Y-%m-%d")
        
        # Redress
        redress = 0.0
        if outcome in ["Upheld", "Partially Upheld"]:
            redress = random.choice([20.0, 50.0, 100.0, 250.0])
            if is_vulnerable and random.random() < 0.2:
                redress += 50.0 # additional distress/inconvenience payment
                
        # Source
        source = np.random.choice(["Direct", "FOS Referral"], p=[0.90, 0.10])
        
        if source == "FOS Referral":
            # Calibrate uphold rate based on FOS database if possible
            # Standard default FOS uphold is 35% if no match
            uphold_prob = 0.35
            # We try to match product name
            cursor.execute("SELECT product_name FROM dim_product WHERE product_id = ?", (prod_id,))
            pname = cursor.fetchone()[0].upper()
            
            for f_lbl, val in fos_upholds.items():
                if pname in f_lbl or f_lbl in pname:
                    if val is not None:
                        uphold_prob = float(val)
                        break
            
            outcome = np.random.choice(COMPLAINT_OUTCOMES, p=[uphold_prob * 0.8, uphold_prob * 0.2, 1 - uphold_prob])
            
        complaints.append((
            complaint_id, cust_id, prod_id, comp_date_str, resolved_date_str,
            category, outcome, res_days, redress, source
        ))
        
        complaint_counter += 1
        
    cursor.executemany(
        "INSERT INTO fact_complaints VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        complaints
    )
    conn.commit()
    logger.info("Loaded %d complaints into fact_complaints.", len(complaints))


def create_views(conn: sqlite3.Connection):
    """Creates the analytical reporting views for the 4 outcome areas."""
    cursor = conn.cursor()
    logger.info("Creating analytical database views...")

    # View 1: Consumer Support Outcome KPIs
    cursor.execute("""
        CREATE VIEW v_outcome_consumer_support AS
        SELECT 
            p.product_category,
            p.product_name,
            COUNT(c.complaint_id) AS total_complaints,
            SUM(CASE WHEN c.complaint_outcome IN ('Upheld', 'Partially Upheld') THEN 1 ELSE 0 END) * 1.0 / COUNT(c.complaint_id) AS uphold_rate,
            AVG(c.days_to_resolve) AS avg_resolution_days,
            SUM(CASE WHEN c.days_to_resolve <= 5 THEN 1 ELSE 0 END) * 1.0 / COUNT(c.complaint_id) AS within_sla_rate,
            SUM(c.redress_amount) AS total_redress,
            COUNT(DISTINCT c.customer_id) * 1000.0 / COUNT(DISTINCT f.sale_id) AS complaints_per_1000_policies
        FROM dim_product p
        JOIN fact_products f ON p.product_id = f.product_id
        LEFT JOIN fact_complaints c ON f.customer_id = c.customer_id AND f.product_id = c.product_id
        GROUP BY p.product_category, p.product_name
    """)

    # View 2: Price & Value Outcome KPIs
    cursor.execute("""
        CREATE VIEW v_outcome_price_value AS
        SELECT 
            p.product_category,
            p.product_name,
            p.distribution_channel,
            COUNT(f.sale_id) AS active_policies,
            SUM(f.premium_or_fee) AS total_premiums,
            SUM(f.commission_amount) AS total_commission,
            SUM(f.commission_amount) * 1.0 / SUM(f.premium_or_fee) AS commission_ratio,
            SUM(f.claims_made_count) AS total_claims_made,
            SUM(f.claims_paid_amount) AS total_claims_paid,
            SUM(f.claims_paid_amount) * 1.0 / SUM(f.premium_or_fee) AS claims_ratio,
            SUM(f.claims_paid_amount) * 1.0 / (SUM(f.claims_made_count) - SUM(f.claims_declined_count) + 0.0001) AS avg_claim_payment,
            SUM(CASE WHEN f.claims_declined_count = 0 AND f.claims_made_count > 0 THEN 1 ELSE 0 END) * 1.0 / SUM(CASE WHEN f.claims_made_count > 0 THEN 1 ELSE 0 END) AS claims_acceptance_rate,
            SUM(CASE WHEN f.cancellation_date IS NOT NULL THEN 1 ELSE 0 END) * 1.0 / COUNT(f.sale_id) AS lapse_rate
        FROM dim_product p
        JOIN fact_products f ON p.product_id = f.product_id
        GROUP BY p.product_category, p.product_name, p.distribution_channel
    """)

    # View 3: Products & Services Concentration
    cursor.execute("""
        CREATE VIEW v_outcome_products_services AS
        SELECT 
            p.product_category,
            p.product_name,
            p.distribution_channel,
            COUNT(f.sale_id) AS sales_volume,
            COUNT(f.sale_id) * 1.0 / (SELECT COUNT(*) FROM fact_products) AS sales_share,
            SUM(CASE WHEN f.cancellation_reason = 'Poor Customer Service' THEN 1 ELSE 0 END) AS cancel_service_barrier,
            SUM(CASE WHEN f.cancellation_reason = 'Financial Hardship' THEN 1 ELSE 0 END) AS cancel_hardship
        FROM dim_product p
        JOIN fact_products f ON p.product_id = f.product_id
        GROUP BY p.product_category, p.product_name, p.distribution_channel
    """)

    # View 4: Vulnerability Disparity Analysis (Consumer Duty Core requirement)
    cursor.execute("""
        CREATE VIEW v_vulnerable_disparity AS
        SELECT 
            p.product_category,
            c.vulnerability_flag,
            COUNT(DISTINCT c.customer_id) AS customer_count,
            COUNT(DISTINCT comp.complaint_id) AS complaint_count,
            AVG(comp.days_to_resolve) AS avg_complaint_resolution_days,
            SUM(CASE WHEN comp.days_to_resolve <= 5 THEN 1 ELSE 0 END) * 1.0 / COUNT(DISTINCT comp.complaint_id) AS complaint_within_sla_rate,
            SUM(CASE WHEN comp.complaint_outcome IN ('Upheld', 'Partially Upheld') THEN 1 ELSE 0 END) * 1.0 / COUNT(DISTINCT comp.complaint_id) AS complaint_uphold_rate,
            SUM(f.claims_made_count) AS claims_count,
            SUM(f.claims_paid_amount) AS claims_paid_total,
            SUM(CASE WHEN f.claims_made_count > 0 AND f.claims_declined_count = 0 THEN 1 ELSE 0 END) * 1.0 / SUM(CASE WHEN f.claims_made_count > 0 THEN 1 ELSE 0 END) AS claims_acceptance_rate,
            SUM(CASE WHEN f.cancellation_date IS NOT NULL THEN 1 ELSE 0 END) * 1.0 / COUNT(f.sale_id) AS policy_lapse_rate
        FROM dim_customer c
        JOIN fact_products f ON c.customer_id = f.customer_id
        JOIN dim_product p ON f.product_id = p.product_id
        LEFT JOIN fact_complaints comp ON c.customer_id = comp.customer_id AND f.product_id = comp.product_id
        GROUP BY p.product_category, c.vulnerability_flag
    """)

    conn.commit()
    logger.info("All database analytical views created successfully.")


def main():
    logger.info("Starting Star Schema database generation...")
    conn = get_db_connection()
    try:
        create_schema(conn)
        generate_dim_calendar(conn)
        generate_dim_outcome_area(conn)
        generate_dim_customer(conn, 50000)
        generate_dim_product(conn)
        generate_fact_products(conn, 75000)
        generate_fact_complaints(conn, 10000)
        create_views(conn)
        logger.info("Star Schema building and data load complete. Database is ready.")
    except Exception as e:
        logger.critical("Critical pipeline error during star schema execution: %s", e)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
