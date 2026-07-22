-- C:\Projects\consumer-duty-analytics\queries\products_services.sql
-- FCA Consumer Duty Outcome Monitoring: Products & Services pillar analysis.
-- Analyzes sales concentration by channel, closed book volume tracking, and core product failure reasons (service barriers, target market mismatches).

WITH product_sales AS (
    SELECT 
        product_id,
        COUNT(sale_id) AS sales_volume,
        SUM(CASE WHEN cancellation_date IS NOT NULL THEN 1 ELSE 0 END) AS total_cancellations,
        SUM(CASE WHEN cancellation_reason = 'Poor Customer Service' THEN 1 ELSE 0 END) AS cancel_service_barriers,
        SUM(CASE WHEN cancellation_reason = 'Unclear Product Terms' THEN 1 ELSE 0 END) AS cancel_terms_mismatch,
        SUM(CASE WHEN cancellation_reason = 'Financial Hardship' THEN 1 ELSE 0 END) AS cancel_financial_hardship
    FROM fact_products
    GROUP BY product_id
),
total_sales AS (
    SELECT COUNT(*) AS grand_total FROM fact_products
)
SELECT 
    p.product_category AS "Product Category",
    p.product_name AS "Product Name",
    p.status AS "Product Status",
    p.distribution_channel AS "Channel",
    ps.sales_volume AS "Sales Volume",
    
    -- Channel Sales Share (to check concentration risk)
    ROUND(ps.sales_volume * 100.0 / ts.grand_total, 1) AS "Sales Share (%)",
    
    -- Cancellation metrics
    ROUND(ps.total_cancellations * 100.0 / ps.sales_volume, 1) AS "Lapse Rate (%)",
    
    -- Root causes of cancellations
    ps.cancel_service_barriers AS "Lapses - Service barriers",
    ps.cancel_terms_mismatch AS "Lapses - Unclear terms",
    ps.cancel_financial_hardship AS "Lapses - Hardship"
FROM dim_product p
JOIN product_sales ps ON p.product_id = ps.product_id
CROSS JOIN total_sales ts
ORDER BY "Sales Volume" DESC;
