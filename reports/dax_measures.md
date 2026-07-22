# Power BI DAX Measures Catalog

This catalog contains the official **DAX (Data Analysis Expressions)** definitions and data formatting specifications for the FCA Consumer Duty Outcome Monitoring dashboard.

> [!WARNING]
> Do NOT use the DAX `FORMAT(value, "string")` function directly in the measure formula itself. Doing so converts the measure's output into a **Text** data type, which prevents Power BI from plotting it on numeric chart axes or using it in sub-aggregations. Instead, set the format string in the **Measure Tools -> Formatting** pane or via Tabular Editor metadata as specified in the comments below.

---

## 1. Core Portfolio Measures

### Total Customers
Counts the total size of the customer database.
* **DAX Code**:
  ```dax
  Total Customers = 
  // FormatString: #,0
  DISTINCTCOUNT(dim_customer[customer_id])
  ```
* **Data Format**: `Whole Number` (Format string: `#,0`)

### Total Policies
Counts the total number of policy sales transactions.
* **DAX Code**:
  ```dax
  Total Policies = 
  // FormatString: #,0
  COUNT(fact_products[sale_id])
  ```
* **Data Format**: `Whole Number` (Format string: `#,0`)

### Total Complaints
Counts the total number of complaints logged.
* **DAX Code**:
  ```dax
  Total Complaints = 
  // FormatString: #,0
  COUNT(fact_complaints[complaint_id])
  ```
* **Data Format**: `Whole Number` (Format string: `#,0`)

---

## 2. Consumer Support Pillar Measures

### Complaints per 1,000 Policies
Normalizes complaint volumes to make products of different scale directly comparable.
* **DAX Code**:
  ```dax
  Complaints per 1k Policies = 
  // FormatString: 0.0
  DIVIDE(
      [Total Complaints] * 1000,
      [Total Policies],
      0
  )
  ```
* **Data Format**: `Decimal Number` (1 decimal place, e.g. `15.4`)

### Average Resolution Time (Days)
Average number of days taken to resolve customer complaints.
* **DAX Code**:
  ```dax
  Average Resolution Time (Days) = 
  // FormatString: 0.0
  AVERAGE(fact_complaints[days_to_resolve])
  ```
* **Data Format**: `Decimal Number` (1 decimal place, e.g. `4.2`)

### Complaint SLA Compliance (%)
Percentage of complaints resolved within the internal 5-day SLA.
* **DAX Code**:
  ```dax
  Complaint SLA Compliance (%) = 
  // FormatString: 0.0%
  DIVIDE(
      CALCULATE(
          [Total Complaints],
          fact_complaints[days_to_resolve] <= 5
      ),
      [Total Complaints],
      0
  )
  ```
* **Data Format**: `Percentage` (1 decimal place, e.g. `68.5%`)

### Uphold Rate (%)
Percentage of complaints where the firm found in favor of the customer (Upheld or Partially Upheld).
* **DAX Code**:
  ```dax
  Uphold Rate (%) = 
  // FormatString: 0.0%
  DIVIDE(
      CALCULATE(
          [Total Complaints],
          fact_complaints[complaint_outcome] IN { "Upheld", "Partially Upheld" }
      ),
      [Total Complaints],
      0
  )
  ```
* **Data Format**: `Percentage` (1 decimal place, e.g. `45.0%`)

### FOS Escalation Rate (%)
Percentage of complaints that were referred to the Financial Ombudsman Service.
* **DAX Code**:
  ```dax
  FOS Escalation Rate (%) = 
  // FormatString: 0.0%
  DIVIDE(
      CALCULATE(
          [Total Complaints],
          fact_complaints[complaint_source] = "FOS Referral"
      ),
      [Total Complaints],
      0
  )
  ```
* **Data Format**: `Percentage` (1 decimal place, e.g. `10.2%`)

### Total Redress Paid (£)
Total financial compensation/redress paid to customers.
* **DAX Code**:
  ```dax
  Total Redress Paid (£) = 
  // FormatString: £#,0.00
  SUM(fact_complaints[redress_amount])
  ```
* **Data Format**: `Currency` (English (United Kingdom) £, 2 decimal places, e.g. `£15,250.00`)

---

## 3. Price & Value Pillar Measures

### Total Premiums (£)
Total written premium volume.
* **DAX Code**:
  ```dax
  Total Premiums (£) = 
  // FormatString: £#,0.00
  SUM(fact_products[premium_or_fee])
  ```
* **Data Format**: `Currency` (English (United Kingdom) £, 2 decimal places, e.g. `£435,288.67`)

### Total Commission (£)
Total commission paid out to intermediaries (brokers/agents).
* **DAX Code**:
  ```dax
  Total Commission (£) = 
  // FormatString: £#,0.00
  SUM(fact_products[commission_amount])
  ```
* **Data Format**: `Currency` (English (United Kingdom) £, 2 decimal places, e.g. `£137,115.00`)

### Commission Ratio (%)
Measures the proportion of customer premium going to brokers (indicates value drag).
* **DAX Code**:
  ```dax
  Commission Ratio (%) = 
  // FormatString: 0.0%
  DIVIDE([Total Commission (£)], [Total Premiums (£)], 0)
  ```
* **Data Format**: `Percentage` (1 decimal place, e.g. `31.5%`)

### Claims Ratio (%)
The percentage of premiums returned to customers as claims payouts. This is the primary metric for fair value.
* **DAX Code**:
  ```dax
  Claims Ratio (%) = 
  // FormatString: 0.0%
  DIVIDE(
      SUM(fact_products[claims_paid_amount]),
      [Total Premiums (£)],
      0
  )
  ```
* **Data Format**: `Percentage` (1 decimal place, e.g. `40.4%`)

### Claims Acceptance Rate (%)
The proportion of claims made that were successfully accepted and paid.
* **DAX Code**:
  ```dax
  Claims Acceptance Rate (%) = 
  // FormatString: 0.0%
  VAR ClaimsMade = SUM(fact_products[claims_made_count])
  VAR ClaimsDeclined = SUM(fact_products[claims_declined_count])
  VAR DecidedClaims = ClaimsMade - ClaimsDeclined
  RETURN
  DIVIDE(DecidedClaims, ClaimsMade, 0)
  ```
* **Data Format**: `Percentage` (1 decimal place, e.g. `84.1%`)

### Policy Lapse Rate (%)
Proportion of active policies cancelled by the customer prior to maturity.
* **DAX Code**:
  ```dax
  Policy Lapse Rate (%) = 
  // FormatString: 0.0%
  DIVIDE(
      CALCULATE(
          [Total Policies],
          NOT(ISBLANK(fact_products[cancellation_date]))
      ),
      [Total Policies],
      0
  )
  ```
* **Data Format**: `Percentage` (1 decimal place, e.g. `5.6%`)

---

## 4. Vulnerability Disparity Measures (Cross-Cutting Outcomes)

### Vulnerable Customer Count
* **DAX Code**:
  ```dax
  Vulnerable Customer Count = 
  // FormatString: #,0
  CALCULATE([Total Customers], dim_customer[vulnerability_flag] = 1)
  ```
* **Data Format**: `Whole Number` (Format string: `#,0`)

### Vulnerable Customer Share (%)
* **DAX Code**:
  ```dax
  Vulnerable Customer Share (%) = 
  // FormatString: 0.0%
  DIVIDE([Vulnerable Customer Count], [Total Customers], 0)
  ```
* **Data Format**: `Percentage` (1 decimal place, e.g. `47.0%`)

### Avg Resolution Time - Vulnerable (Days)
Average complaint resolution time specifically for customers with vulnerability flags.
* **DAX Code**:
  ```dax
  Avg Resolution Time - Vulnerable (Days) = 
  // FormatString: 0.0
  CALCULATE(
      [Average Resolution Time (Days)],
      dim_customer[vulnerability_flag] = 1
  )
  ```
* **Data Format**: `Decimal Number` (1 decimal place, e.g. `6.7`)

### Avg Resolution Time - Non-Vulnerable (Days)
* **DAX Code**:
  ```dax
  Avg Resolution Time - Non-Vulnerable (Days) = 
  // FormatString: 0.0
  CALCULATE(
      [Average Resolution Time (Days)],
      dim_customer[vulnerability_flag] = 0
  )
  ```
* **Data Format**: `Decimal Number` (1 decimal place, e.g. `4.7`)

### SLA Disparity Gap (Days)
Calculates the operational delay gap between cohorts. Positive values indicate vulnerable customers face longer delays.
* **DAX Code**:
  ```dax
  SLA Disparity Gap (Days) = 
  // FormatString: 0.0
  [Avg Resolution Time - Vulnerable (Days)] - [Avg Resolution Time - Non-Vulnerable (Days)]
  ```
* **Data Format**: `Decimal Number` (1 decimal place, e.g. `2.0`)

### SLA Compliance - Vulnerable (%)
Percentage of complaints resolved within 5 days for vulnerable customers.
* **DAX Code**:
  ```dax
  SLA Compliance - Vulnerable (%) = 
  // FormatString: 0.0%
  CALCULATE([Complaint SLA Compliance (%)], dim_customer[vulnerability_flag] = 1)
  ```
* **Data Format**: `Percentage` (1 decimal place, e.g. `62.5%`)

### SLA Compliance - Non-Vulnerable (%)
Percentage of complaints resolved within 5 days for non-vulnerable customers.
* **DAX Code**:
  ```dax
  SLA Compliance - Non-Vulnerable (%) = 
  // FormatString: 0.0%
  CALCULATE([Complaint SLA Compliance (%)], dim_customer[vulnerability_flag] = 0)
  ```
* **Data Format**: `Percentage` (1 decimal place, e.g. `78.2%`)
