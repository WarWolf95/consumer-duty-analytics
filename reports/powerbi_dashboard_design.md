# Power BI Dashboard Design Specifications

This document outlines the layout, metrics, and visual design requirements for the **FCA Consumer Duty Outcome Monitoring Dashboard**. The dashboard is divided into 4 key reporting sheets, mapping directly to the regulatory outcomes.

---

## 1. Design System & Theme
* **Theme File**: Located at [fca_consumer_duty_theme.json](file:///c:/Projects/consumer-duty-analytics/powerbi/fca_consumer_duty_theme.json).
* **Color Palette**:
  * **Primary (FCA Claret)**: `#701B45` — Used for titles, core KPI cards, table headers, and primary data marks.
  * **Secondary (Gov Blue)**: `#1D70B8` — Used for comparison metrics and peer averages.
  * **Teal Accent**: `#008080` — Represents target thresholds/SLAs.
  * **Warning Red**: `#D4351C` — Highlights breach points (e.g. SLA delays, low claims ratio).
  * **Canvas Background**: `#F8F9FA` (Off-white).
* **Typography**: Segoe UI (standard clean enterprise typography).

---

## 2. Dashboard Pages and Visuals

### Page 1: Executive Outcomes Overview
Provides a high-level summary of the firm's compliance with Consumer Duty outcomes for the Board and Risk Committee.

* **Key Performance Indicators (KPI Cards)**:
  * **Total Customers**: Count of distinct customer IDs (`50,000`).
  * **Complaints per 1,000 Policies**: Portfolio average vs target of `15.0`.
  * **Avg Resolution Days**: Enterprise average vs target of `5.0` days.
  * **Lapse Rate**: Percentage of policies cancelled early vs target of `5.0%`.
* **Visuals**:
  1. **Line & Clustered Column Chart**: Monthly Sales vs. Complaints Trend (X-Axis: Month-Year, Y-Axis Columns: Policies Sold, Y-Axis Line: Total Complaints).
  2. **Vulnerability Outcome Disparity (Bar Chart)**: Compares Vulnerable vs. Non-Vulnerable customers across the four outcome metrics side-by-side.
  3. **Regulatory Breaches Alert (Table)**: Lists products where SLA compliance is < 80% or Claims Ratio is below target.

---

### Page 2: Price & Value (Fair Value Assessment)
Enables the Pricing Committee to analyze if products represent fair value and verify compliance against FCA benchmarks.

* **KPI Cards**:
  * **Average Premium Charged**: Average premium per product type.
  * **Portfolio Claims Ratio**: Average claims ratio (`claims paid ÷ written premium`).
  * **Portfolio Commission Ratio**: Commission payout percentage.
* **Visuals**:
  1. **Clustered Column Chart - Claims Ratio vs. FCA Benchmark**:
     * X-Axis: Product Name.
     * Y-Axis: Claims Ratio (%) and FCA Claims Ratio Benchmark (%) side-by-side.
     * *Highlight*: Flag **Motor Insurance** where claims ratio is 40.4% vs FCA benchmark of 54.4% (potential value risk).
  2. **Scatter Plot - Value Index**:
     * X-Axis: Commission Ratio (%).
     * Y-Axis: Claims Acceptance Rate (%).
     * *Highlight*: High commission / low acceptance products appear in the top-left quadrant (e.g., Travel Broker with 31.5% commission).
  3. **Lapse Rate vs. Cancellation Reasons (Donut Chart)**: Breakdown of cancellations (e.g. Financial Hardship, found better price elsewhere).

---

### Page 3: Consumer Support (Complaints & Barriers)
Designed for the Customer Operations team to track response times, customer friction, and ombudsman escalations.

* **KPI Cards**:
  * **Complaints Closed within SLA**: Percentage of cases resolved in ≤ 5 days.
  * **Avg Resolution time (Vulnerable)**: Resolution speed for vulnerable customers.
  * **Total Redress Paid**: Cumulative financial redress.
* **Visuals**:
  1. **Complaints by Root Cause Category (Treemap)**: Shows volumes by category (e.g., Admin Error, Claims Dispute, Unreasonable Service Barriers).
  2. **SLA Compliance by Distribution Channel (Bar Chart)**: Evaluates if specific distribution channels (e.g., Brokers) introduce support bottlenecks.
  3. **Ombudsman Escalation Matrix (Table)**: Lists FOS cases by product type, showing total new cases and firm uphold rates vs the FOS benchmark.

---

### Page 4: Vulnerability Outcome Disparity (Fair Treatment)
Dedicated to showing the Board that vulnerable cohorts do not face systematically worse outcomes.

* **KPI Cards**:
  * **Vulnerable Cohort Share**: % of customers with a vulnerability indicator (`47.0%`).
  * **SLA Disparity Gap**: Difference in average resolution days between cohorts.
* **Visuals**:
  1. **Product Disparity Chart (Line Chart — Native)**:
     * X-Axis: `dim_product[product_category]`
     * Y-Axis: `[Average Resolution Time (Days)]`
     * Legend: `dim_customer[Vulnerability Cohort]` (Vulnerable vs. Non-Vulnerable)
     * *Purpose*: Traces average resolution speed across product lines for both cohorts, allowing the Board to pinpoint which specific product categories drive operational disparity.
  2. **Vulnerability Drivers (Stacked Column Chart)**:
     * Breakdown of vulnerability drivers across the portfolio (Health, Capability, Resilience, Life Events).
  3. **Product Disparity Parity Chart (Scatter Plot)**:
     * X-Axis: Non-Vulnerable SLA Compliance (%)
     * Y-Axis: Vulnerable SLA Compliance (%)
     * Bubble Size: Vulnerable Customer Count
     * Details: Product Name (Color-coded by Product Category)
     * *Highlight*: 45° 1:1 Parity Line (y = x). Products plotted below the line indicate disproportionately worse support SLA compliance for vulnerable customers.
  4. **Cohort Resolution Time Trend (Clustered Line Chart)**:
     * X-Axis: Reporting Month-Year
     * Y-Axis: Average Resolution Time (Days)
     * Legend: Cohort (Vulnerable vs. Non-Vulnerable)
     * *Highlight*: Displays historical operational trend and demonstrates closing of the disparity gap over time.
