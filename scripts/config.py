# C:\Projects\consumer-duty-analytics\scripts\config.py
"""
Centralized configuration, taxonomies, and KPI targets for the Consumer Duty Outcome Monitoring project.
Mimics standard enterprise configuration files used in UK financial institutions.
"""

import os
from pathlib import Path

# Project Directories (Dynamically resolved relative to this file)
PROJECT_ROOT = str(Path(__file__).resolve().parent.parent)
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
RAW_DATA_DIR = os.path.join(DATA_DIR, "raw")
PROCESSED_DATA_DIR = os.path.join(DATA_DIR, "processed")
SQLITE_DB_PATH = os.path.join(PROCESSED_DATA_DIR, "consumer_duty.db")
REPORTS_DIR = os.path.join(PROJECT_ROOT, "reports")
POWERBI_DIR = os.path.join(PROJECT_ROOT, "powerbi")

# Taxonomy & Categories
PRODUCT_CATEGORIES = {
    "General Insurance": ["Motor Insurance", "Home Insurance", "Travel Insurance", "Pet Insurance"],
    "Retail Banking": ["Standard Savings Account", "Reward Credit Card", "Easy Access ISA"],
    "Protection & Investments": ["Term Life Insurance", "Guaranteed Income Bond"]
}

PRODUCT_LIST = [prod for prods in PRODUCT_CATEGORIES.values() for prod in prods]

REGIONS = [
    "London", "South East", "South West", "East of England", 
    "West Midlands", "East Midlands", "Yorkshire and the Humber", 
    "North West", "North East", "Wales", "Scotland", "Northern Ireland"
]

DISTRIBUTION_CHANNELS = ["Direct", "Broker", "Tied Agent", "Digital Platform"]

VULNERABILITY_CATEGORIES = {
    "Health": ["Physical Disability", "Severe/Long-term Illness", "Mental Health Condition"],
    "Life Events": ["Bereavement", "Redundancy", "Relationship Breakdown", "Caring Responsibilities"],
    "Resilience": ["Low/Fluctuating Income", "High Debt Burden", "Low Savings", "No Support Network"],
    "Capability": ["Low English Literacy", "Low Financial Capability", "Cognitive Impairment", "Digital Exclusion"]
}

# Source categories for complaints
COMPLAINT_CATEGORIES = [
    "Admin or IT System Error",
    "Product Performance & Fees",
    "Customer Support Delay",
    "Misleading or Unclear Communication",
    "Claims Assessment Dispute",
    "Unreasonable Service Barriers"
]

COMPLAINT_OUTCOMES = ["Upheld", "Partially Upheld", "Not Upheld"]

CANCELLATION_REASONS = [
    "Found Better Price Elsewhere",
    "No Longer Needs Product",
    "Poor Customer Service",
    "Unclear Product Terms",
    "Financial Hardship"
]

# Benchmark Targets & Thresholds (Calibrated to FCA and UK sector averages)
REGULATORY_KPI_THRESHOLDS = {
    # Consumer Support Outcome
    "target_complaints_per_1000_policies": 15.0,  # Alert threshold if complaints cross this
    "target_avg_resolution_days": 5.0,            # Enterprise SLA
    "fca_uphold_rate_benchmark": 0.45,            # Market uphold average (~45%)
    "max_vulnerable_support_delay_ratio": 1.10,   # Vulnerable customers should face <= 10% longer delays than non-vulnerable

    # Price & Value Outcome
    "target_claims_ratio": {
        "Motor Insurance": 0.75,                  # 75% target claims payout ratio
        "Home Insurance": 0.60,                   # 60%
        "Travel Insurance": 0.45,                 # 45% (typically lower, indicating potential value risk)
        "Pet Insurance": 0.65                     # 65%
    },
    "target_claims_acceptance_rate": {
        "Motor Insurance": 0.98,
        "Home Insurance": 0.85,
        "Travel Insurance": 0.88,
        "Pet Insurance": 0.82
    },
    "max_commission_premium_ratio": {
        "Motor Insurance": 0.12,                  # Commission shouldn't exceed 12%
        "Home Insurance": 0.20,                   # 20%
        "Travel Insurance": 0.35,                 # 35% (high-risk commission, value-testing indicator)
        "Pet Insurance": 0.22                     # 22%
    },
    "target_early_cancellation_rate": 0.05,       # 5% target cap on cooling-off/early lapses

    # Products & Services Outcome
    "target_sales_concentration_limit": 0.40,     # Max 40% sales in any single distributor (diversification check)
    "target_product_switch_rate_low_value": 0.15, # Target 15% annual switch rate for customers in low-yield/outdated accounts

    # Cross-cutting outcomes
    "target_vulnerable_outcome_disparity": 0.05   # No metric (e.g. claims acceptance) should have >5% disparity for vulnerable groups
}

# Ensure directories exist
for folder in [RAW_DATA_DIR, PROCESSED_DATA_DIR, REPORTS_DIR, POWERBI_DIR]:
    os.makedirs(folder, exist_ok=True)
