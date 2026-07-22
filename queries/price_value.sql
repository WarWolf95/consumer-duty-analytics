-- C:\Projects\consumer-duty-analytics\queries\price_value.sql
-- FCA Consumer Duty Outcome Monitoring: Price & Value pillar analysis.
-- Compares product claims ratios, claim acceptance rates, and commissions against FCA GI Value Measures industry benchmarks.

WITH firm_metrics AS (
    -- Calculate claims ratios, commissions, and cancellations at product level
    SELECT 
        product_id,
        COUNT(sale_id) AS active_policies,
        SUM(premium_or_fee) AS total_premiums,
        SUM(commission_amount) AS total_commission,
        SUM(claims_made_count) AS total_claims,
        SUM(claims_paid_amount) AS total_claims_paid,
        SUM(CASE WHEN claims_declined_count = 0 AND claims_made_count > 0 THEN 1 ELSE 0 END) AS accepted_claims,
        SUM(CASE WHEN claims_made_count > 0 THEN 1 ELSE 0 END) AS total_claims_with_decision,
        SUM(CASE WHEN cancellation_date IS NOT NULL THEN 1 ELSE 0 END) AS total_cancellations
    FROM fact_products
    GROUP BY product_id
),
industry_benchmarks AS (
    -- Normalize and retrieve 2024 sector benchmarks from staged FCA Value Measures
    SELECT 
        CASE 
            WHEN product_category = 'Motor (All)' THEN 'Motor Insurance'
            WHEN product_category = 'Home - (buildings and contents combined) (All)' THEN 'Home Insurance'
            WHEN product_category = 'Travel - annual european (All)' THEN 'Travel Insurance'
            WHEN product_category = 'Pet - covered for life (All)' THEN 'Pet Insurance'
            ELSE NULL 
        END AS mapped_product_name,
        -- Convert percentage strings to decimal fractions
        CAST(claims_acceptance_rate_2024 AS REAL) AS fca_acceptance_benchmark,
        CAST(claims_ratio_2024 AS REAL) AS fca_claims_ratio_benchmark
    FROM stage_fca_gi_value_measures
    WHERE mapped_product_name IS NOT NULL
)
SELECT 
    p.product_category AS "Product Category",
    p.product_name AS "Product Name",
    p.distribution_channel AS "Channel",
    fm.active_policies AS "Policies Sold",
    ROUND(fm.total_premiums, 2) AS "Total Premiums (£)",
    
    -- Commission ratio (indicator of distribution chain value drag)
    ROUND(fm.total_commission * 100.0 / fm.total_premiums, 1) AS "Commission Ratio (%)",
    
    -- Claims acceptance rate compared directly to FCA benchmarks
    ROUND(fm.accepted_claims * 100.0 / NULLIF(fm.total_claims_with_decision, 0), 1) AS "Claims Acceptance Rate (%)",
    ROUND(ib.fca_acceptance_benchmark * 100.0, 1) AS "FCA Acceptance Benchmark (%)",
    
    -- Claims ratio (payouts / premium) compared directly to FCA benchmarks
    ROUND(fm.total_claims_paid * 100.0 / fm.total_premiums, 1) AS "Claims Ratio (%)",
    ROUND(ib.fca_claims_ratio_benchmark * 100.0, 1) AS "FCA Claims Ratio Benchmark (%)",
    
    -- Early cancellation / lapse rate (poor customer value indicator)
    ROUND(fm.total_cancellations * 100.0 / fm.active_policies, 1) AS "Lapse Rate (%)"
FROM dim_product p
JOIN firm_metrics fm ON p.product_id = fm.product_id
LEFT JOIN industry_benchmarks ib ON p.product_name = ib.mapped_product_name
ORDER BY "Product Category" ASC, "Claims Ratio (%)" ASC;
