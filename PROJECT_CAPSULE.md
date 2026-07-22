# Project Capsule: FCA Consumer Duty Outcome Monitoring

> **Created**: 2026-07-15
> **Status**: ✅ Phase 4 complete (Data Acquisition, SQLite Star Schema, DAX Catalog & 4-Page Power BI Layout Complete)
> **Previous work**: See conversation log in OpenCode session (2026-07-15, post-Workforce-Planning project)

---

## 1. Objective

Build a production-grade SQL + Power BI portfolio project targeting **med-senior Data Analyst roles in UK financial services**. The topic is **FCA Consumer Duty Outcome Monitoring** — tracking whether financial products deliver fair value and good outcomes for consumers, as mandated by the Consumer Duty (PS22/9, July 2023).

**Target audience for the deliverable**: Heads of Conduct Risk, Customer Outcomes, or Product Governance — the dashboards and reports should be something an analyst would present at a Product & Pricing Committee or Consumer Duty Forum.

---

## 2. Business Context

### What is Consumer Duty?

The FCA's Consumer Duty (effective 31 July 2023 for new products, 31 July 2024 for closed books) requires firms to:

1. End the "know your customer" tick-box approach
2. Demonstrate **good outcomes** across four Outcome Areas:
   - **Products & Services** — products must meet customer needs and be fit for purpose
   - **Price & Value** — prices must represent fair value relative to the benefit received
   - **Consumer Support** — customers must not face unreasonable barriers to service
   - **Communication** — information must be clear, timely, and understandable

### Why this matters for a portfolio project

- **High regulatory relevance** — every UK retail bank, insurer, wealth manager, and lender has a Consumer Duty workstream (or is being asked about it in RFIs)
- **Data-rich domain** — complaints, product sales, renewals, claims, pricing, vulnerable customer indicators
- **Cross-functional** — touches conduct risk, product, pricing, customer analytics, complaints, and MI reporting teams
- **Proves domain knowledge** — shows you understand the UK regulatory landscape, not just technical skills

---

## 3. Data Sources & Provenance

We follow the same **4-tier hybrid data strategy** as the Workforce Planning project. Every dataset is explicitly classified.

### Data Strategy: Real UK Public Data First

We prioritise real UK public data from FCA, FOS, ONS, BoE, and PRA. Synthetic data is only generated when:
1. No real UK public data source exists for a given need, AND
2. The data is essential for the analysis (e.g., customer-level vulnerability flags)

Every synthetic dataset is labelled Tier 2 (Calibrated/Modelled) with documented calibration sources.

### Tier 1: Real (Direct from Source)
| Dataset | Source | Script | Use |
|---------|--------|--------|-----|
| FCA Firm Complaints 2025 H2 | FCA published XLSX | `fetch_fca_benchmarks.py` | Complaint benchmarks by firm, product, uphold rate, redress |
| FCA GI Value Measures 2024 | FCA published XLSX | `fetch_fca_benchmarks.py` | Claims ratios, acceptance rates, cancellation rates |
| FCA Product Sales Data 2024 | FCA published XLSX | `fetch_fca_benchmarks.py` | Pure protection sales volumes by channel |
| FOS Annual Complaints 2025/26 | FOS published CSV | `fetch_fos_data.py` | Product-level complaint volumes & uphold rates |
| ONS Population Estimates mid-2024 | ONS published XLSX | `fetch_ons_data.py` | Regional demographics for vulnerability proxies |

### Tier 2: Calibrated Synthetic (only where gaps exist)
| Dataset | Calibrated To | When Needed |
|---------|--------------|-------------|
| Customer base with vulnerability flags | ONS demographics + FCA complaints ratios | Phase 3 — vulnerability outcome disparity analysis |
| Complaint records at customer level | FCA firm-level aggregates + FOS product mix | Phase 3 — drill-down analysis |
| GI claims at policy level | FCA GI Value Measures product-level aggregates | Phase 3 — fair value analysis |

---

## 4. Technical Architecture

### Stack
- **Processing**: Python 3.10+ (pandas, numpy, pytest)
- **Storage & Querying**: SQLite (staging, transformation, analytical views)
- **Visualisation**: Power BI (star schema with RLS-context design)
- **Orchestration**: Single `run_pipeline.py` entry point

### Proposed Star Schema

```
fact_complaints
│   complaint_id (PK)
│   customer_id (FK)
│   product_id (FK)
│   complaint_date
│   resolved_date
│   complaint_category (e.g., "Admin Error", "Product Performance", "Service")
│   complaint_outcome (Upheld, Partially Upheld, Not Upheld)
│   days_to_resolve
│   redress_amount
│   complaint_source (FOS referral, direct, etc.)
│
├── dim_customer
│   customer_id (PK)
│   age_band
│   region
│   tenure_years
│   product_count
│   vulnerability_flag
│   vulnerability_type
│   ltd_complaint_count
│
├── dim_product
│   product_id (PK)
│   product_category (Motor, Home, Life, Savings, Credit Card, etc.)
│   product_name
│   distribution_channel (Direct, Broker, Tied Agent)
│   launch_date
│   status (Open, Closed, Withdrawn)
│
├── dim_calendar
│   date (PK)
│   year
│   quarter
│   month
│   reporting_period (CD outcome quarter flag)
│
├── dim_outcome_area (bridges to Consumer Duty framework)
│   outcome_id (PK)
│   outcome_area (Products & Service, Price & Value, Consumer Support)
│   kpi_category
│   regulatory_threshold

fact_products
│   sale_id (PK)
│   customer_id (FK)
│   product_id (FK)
│   sale_date
│   premium_or_fee
│   sum_assured_or_cover
│   commission_amount
│   commission_type (Initial, Renewal)
│   retention_period_months
│   cancellation_date
│   cancellation_reason
│   claims_made_count
│   claims_paid_amount
│   claims_declined_count

(Plus aggregated KPI views)
v_cta_kpis
v_price_value_kpis
v_customer_outcomes
```

### Pipeline Flow

```
run_pipeline.py (TBD — optional orchestration)
  ├── Phase 1 — Data Acquisition
  │   ├── fetch_fca_benchmarks.py     → Z_RAW_fca_complaints.xlsx, Z_RAW_gi_value_measures.xlsx
  │   ├── fetch_fos_data.py           → Z_RAW_fos_complaints_2025_26.csv
  │   └── fetch_ons_data.py           → Z_RAW_ons_population_mid2024.xlsx
  ├── Phase 2 — Storage & Schema
  │   ├── ingest_to_sqlite.py         → Staging tables in SQLite
  │   └── build_star_schema.py        → Star schema + aggregate CTA KPI views
  ├── Phase 3 — Analytics & KPIs
  │   ├── (calibrated synthetic generation if needed)
  │   ├── analytical SQL queries
  │   └── verify_db.py                → Assertions on analytical views
  ├── Phase 4 — Power BI
  │   └── export_powerbi.py           → CSV export for Power BI ingestion
  └── Phase 5 — Delivery
      └── Executive Briefing, README, GitHub push
```

---

## 5. Key Deliverables

| Deliverable | Description | Status |
|-------------|-------------|--------|
| Synthetic customer/product/claims data | 50k customers, 20+ products, 10k complaints | ✅ |
| FCA benchmark datasets | Cleaned, normalised FCA published data | ✅ |
| SQLite database | Staging → star schema → aggregate KPI views | ✅ |
| Power BI dashboard | 4-pager: Executive Summary, Product Dashboard, Complaints, Vulnerability | ✅ |
| KPI catalog (CSV/MD) | Definitive list of metric definitions per outcome area | ✅ |
| Data quality tests | pytest suite validating pipeline output | ✅ |
| Executive Briefing (PDF/PPT) | Non-technical summary for C-Suite / Risk Committee | 🔲 |
| Background query validation | Verification of analytical SQL queries | ✅ |
| README.md | Full project documentation with data provenance | 🔲 |

---

## 6. Regulatory KPIs to Implement

The dashboard should answer the specific questions a Consumer Duty Forum would ask:

### Consumer Support Outcome
- Complaint volume per 1,000 policies (by product, by channel)
- Average resolution time (target: < 5 business days)
- Uphold rate (FCA benchmark: varies by product, typically 40-60%)
- Redress ratio (% of complaints resulting in financial redress)
- Complaints by category (root cause breakdown)
- Repeat complaint rate per customer
- Complaints from vulnerable customers vs non-vulnerable

### Price & Value Outcome
- Claims ratio (incurred claims ÷ earned premiums) — benchmark against FCA Value Measures data
- Claims acceptance rate (benchmark against FCA Value Measures)
- Commission ratio (commission ÷ premium — is it reasonable?)
- Cancellation/lapse rate (early cancellations may indicate poor value)
- Price comparison vs market median for similar products (modelled)
- Average premium per risk band

### Products & Services Outcome
- Product sales by distribution channel (are certain channels mis-selling?)
- Product concentration by customer segment
- Switch/upgrade rate
- Product gap analysis (customers with no appropriate product for their life stage)
- New product performance vs projections

### Cross-cutting: Vulnerable Customer Indicators
- Vulnerability rate by product vs portfolio average
- Outcome disparity analysis (vulnerable vs non-vulnerable on each KPI)
- Proportion of complaints from vulnerable customers
- Fair value assessment by vulnerability cohort

---

## 7. Design Decisions Already Made

### Decisions (from 2026-07-15 conversation)

1. **Topic**: FCA Consumer Duty Outcome Monitoring — not generic complaints analysis.
2. **Data strategy**: Real UK public data first (FCA, FOS, ONS). Synthetic only where no public data exists. Every dataset labelled with provenance tier.
3. **Database**: SQLite-only (no DuckDB, no Polars, no Oracle). Keeps it simple and reproducible.
4. **Real data to fetch**:
   - FCA Firm Complaints Data → Consumer Support benchmarks
   - FCA Product Sales Data (Pure Protection) → Products & Services benchmarks
   - FCA GI Value Measures → Price & Value benchmarks
   - FOS Annual Complaints Data → Consumer Support (ombudsman-level)
   - ONS Population Estimates → Regional demographics for vulnerability proxies
5. **Calibrated synthetic data**: Only where no real source exists (customer-level vulnerability flags). Labelled Tier 2 with documented calibration sources.
6. **Power BI**: Star schema with `dim_outcome_area` as an explicit bridge to the regulatory framework.
7. **Vulnerable customers**: Treated as a cross-cutting dimension, not a separate outcome area. This is the approach we see in leading firms (e.g. Lloyds, Nationwide CD disclosures).

### Decisions NOT yet made (need input)

- Which specific Power BI visuals for the 4-page layout?
- Aggregation level for the complaints view: daily, weekly, or monthly?
- Should we include a claims severity model for reserve estimation (actuarial cross-over)?

---

## 8. Directory Structure (planned)

```
C:\Projects\consumer-duty-analytics\
├── data\
│   ├── raw\               # Real downloaded datasets (FCA, FOS, ONS XLSX/CSV)
│   └── processed\         # Star schema CSV exports for Power BI
├── powerbi\               # .pbix file and exported PDF
├── queries\               # SQL analytical queries (one per outcome area)
├── reports\               # Executive Briefing, KPI catalog, verification outputs
├── scripts\               # Python modules
│   ├── config.py          # Taxonomies, KPI thresholds, paths
│   ├── utils.py           # Logging, DB connection, CSV helpers
│   ├── fetch_fca_benchmarks.py  # FCA complaints, GI value measures, PSD downloads
│   ├── fetch_fos_data.py        # FOS annual complaints data download
│   ├── fetch_ons_data.py        # ONS population estimates download
│   ├── ingest_to_sqlite.py      # TBD Phase 2
│   ├── build_star_schema.py     # TBD Phase 2
│   ├── export_powerbi.py        # TBD Phase 4
│   └── verify_db.py             # TBD Phase 3
├── tests\                 # pytest suite
├── PROJECT_CAPSULE.md     # This file
├── requirements.txt
```

---

## 9. Next Steps (immediate)

### Phase 1 — Data Acquisition
1. ✅ `config.py` — product taxonomies, region mappings, vulnerability types, KPI thresholds
2. ✅ `utils.py` — logging, DB connection, CSV helpers  
3. ✅ `fetch_fca_benchmarks.py` — downloads FCA firm complaints, GI value measures, product sales data
4. ✅ `fetch_fos_data.py` — download FOS annual complaints data with product-level breakdown
5. ✅ `fetch_ons_data.py` — download ONS mid-year population estimates by region
6. 🔲 Data gap report — document what each source provides vs what's needed

### Phase 2 — Storage & Schema
7. ✅ `ingest_to_sqlite.py` — staging table creation and data loading
8. ✅ `build_star_schema.py` — star schema transforms, CTA KPI aggregation views

### Phase 3 — Analytics & KPIs
9. ✅ Calibrated synthetic data loaded to dimensions and facts
10. ✅ Analytical SQL queries (one per outcome area)
11. ✅ Background verification of database queries

### Phase 4 — Power BI
12. ❌ `export_powerbi.py` — Bypassed (connecting Power BI directly to SQLite db for industry realism)
13. 🔲 4-page .pbix dashboard (Connect to SQLite db)

### Phase 5 — Delivery
14. Executive Briefing
15. README
16. Push to GitHub

---

## 10. Handover Notes

- **Who to hand over to**: Any data analyst / data engineer familiar with UK financial services
- **How this capsule is structured**: Sections 1-6 explain the *what* and *why*. Sections 7-9 explain the *how* and *what next*.
- **Contact**: If continuing from this capsule, read the full conversation log in OpenCode session history (2026-07-15) for nuance on specific discussions about data provenance labelling, the Consumer Duty regulatory framework, and the 4-tier strategy.
- **OpenCode config**: See `C:\Users\curil\.config\opencode\AGENTS.md` for communication style preferences and UK finance code conventions. OpenCode is running `opencode/deepseek-v4-flash-free` via OpenCode Zen — not configured for Gemini yet.
- **Previous project reference**: Workforce Planning at `C:\Projects\Workforce Planning & Labour Market Intelligence\` is the template for architecture, code style, and README structure. Refer to it for patterns.
