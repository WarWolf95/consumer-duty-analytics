-- C:\Projects\consumer-duty-analytics\queries\consumer_support.sql
-- FCA Consumer Duty Outcome Monitoring: Consumer Support pillar analysis.
-- Calculates complaint volume per 1,000 policies, resolution times, SLA compliance, and redress distributions.

WITH policy_base AS (
    -- Count distinct policies in force by product
    SELECT 
        product_id,
        COUNT(sale_id) AS total_policies
    FROM fact_products
    GROUP BY product_id
),
complaint_aggregates AS (
    -- Aggregate complaints, resolution times, SLA breaches, and redress by product
    SELECT 
        product_id,
        COUNT(complaint_id) AS total_complaints,
        SUM(CASE WHEN complaint_outcome IN ('Upheld', 'Partially Upheld') THEN 1 ELSE 0 END) AS upheld_complaints,
        AVG(days_to_resolve) AS avg_resolution_days,
        SUM(CASE WHEN days_to_resolve <= 5 THEN 1 ELSE 0 END) AS within_sla_count,
        SUM(redress_amount) AS total_redress,
        SUM(CASE WHEN complaint_source = 'FOS Referral' THEN 1 ELSE 0 END) AS fos_escalations
    FROM fact_complaints
    GROUP BY product_id
)
SELECT 
    p.product_category AS "Product Category",
    p.product_name AS "Product Name",
    p.distribution_channel AS "Channel",
    pb.total_policies AS "Policies in Force",
    COALESCE(ca.total_complaints, 0) AS "Total Complaints",
    -- Complaint volume per 1,000 policies (standard FCA MI metric)
    ROUND(COALESCE(ca.total_complaints, 0) * 1000.0 / pb.total_policies, 2) AS "Complaints per 1k Policies",
    -- Uphold rate: proportion of complaints where firm found in customer's favour
    ROUND(COALESCE(ca.upheld_complaints, 0) * 100.0 / NULLIF(ca.total_complaints, 0), 1) AS "Uphold Rate (%)",
    -- Average days to resolve the complaint (SLA target is 5 days)
    ROUND(COALESCE(ca.avg_resolution_days, 0), 1) AS "Avg Resolution Days",
    -- SLA compliance: % of complaints resolved within 5 business days
    ROUND(COALESCE(ca.within_sla_count, 0) * 100.0 / NULLIF(ca.total_complaints, 0), 1) AS "SLA Compliance (%)",
    -- FOS escalation rate
    ROUND(COALESCE(ca.fos_escalations, 0) * 100.0 / NULLIF(ca.total_complaints, 0), 1) AS "FOS Escalation Rate (%)",
    -- Total financial redress paid to customers
    ROUND(COALESCE(ca.total_redress, 0.0), 2) AS "Total Redress (£)"
FROM dim_product p
JOIN policy_base pb ON p.product_id = pb.product_id
LEFT JOIN complaint_aggregates ca ON p.product_id = ca.product_id
ORDER BY "Complaints per 1k Policies" DESC;
