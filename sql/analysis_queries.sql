-- ============================================================================
-- analysis_queries.sql — the questions an ops lead would actually ask.
-- Each query is standalone; run after create_tables.sql and kpi_views.sql.
-- ============================================================================

-- Q1. Where is service demand concentrated? (top 15 request types)
SELECT complaint_type, primary_agency, total_requests,
       ROUND(100.0 * total_requests / SUM(total_requests) OVER (), 1) AS pct_of_all
FROM v_kpi_by_complaint_type
ORDER BY total_requests DESC
LIMIT 15;

-- Q2. Which agencies carry the load, and how fast do they close?
SELECT agency, agency_name, total_requests, closed_requests, open_requests,
       avg_closure_days, median_closure_days, sla_miss_rate
FROM v_kpi_by_agency
ORDER BY total_requests DESC
LIMIT 15;

-- Q3. Borough pressure: volume, backlog and SLA performance side by side
SELECT * FROM v_kpi_by_borough ORDER BY total_requests DESC;

-- Q4. Weekly rhythm: is demand rising, and does closure keep pace?
SELECT * FROM v_kpi_weekly ORDER BY created_week;

-- Q5. The aging backlog: how much is sitting past 30 / 90 / 180 days?
SELECT aging_bucket, SUM(open_requests) AS open_requests,
       ROUND(100.0 * SUM(open_requests) / SUM(SUM(open_requests)) OVER (), 1) AS pct_of_backlog
FROM v_backlog_aging
GROUP BY aging_bucket
ORDER BY CASE aging_bucket
    WHEN '0-7 days' THEN 1 WHEN '8-30 days' THEN 2 WHEN '31-90 days' THEN 3
    WHEN '91-180 days' THEN 4 ELSE 5 END;

-- Q6. Worst SLA performance among high-volume request types (>= 5,000 requests)
SELECT complaint_type, primary_agency, total_requests, sla_miss_rate,
       avg_closure_days, open_requests
FROM v_kpi_by_complaint_type
WHERE total_requests >= 5000
ORDER BY sla_miss_rate DESC
LIMIT 15;

-- Q7. High-pressure hotspots: complaint x borough cells ranked by priority
SELECT priority_rank, complaint_type, borough, agency, total_requests,
       open_requests, sla_miss_rate, aged_share_of_open, priority_score
FROM v_priority_scores
ORDER BY priority_rank
LIMIT 20;

-- Q8. High-risk unresolved requests: oldest open items in priority hotspots
SELECT r.unique_key, r.complaint_type, r.borough, r.agency,
       r.created_date::DATE AS created, r.age_days, r.aging_bucket, r.status
FROM v_requests_enriched r
JOIN (SELECT complaint_type, borough FROM v_priority_scores
      WHERE priority_rank <= 10) hot USING (complaint_type, borough)
WHERE NOT r.is_closed
ORDER BY r.age_days DESC
LIMIT 25;

-- Q9. Channel mix: how do requests arrive?
SELECT open_data_channel_type, COUNT(*) AS requests,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS pct
FROM v_requests_enriched
GROUP BY open_data_channel_type
ORDER BY requests DESC;

-- Q10. Month-over-month demand change by borough (activity window)
SELECT borough, created_month, COUNT(*) AS requests,
       ROUND(100.0 * (COUNT(*) - LAG(COUNT(*)) OVER (PARTITION BY borough ORDER BY created_month))
           / NULLIF(LAG(COUNT(*)) OVER (PARTITION BY borough ORDER BY created_month), 0), 1) AS mom_change_pct
FROM v_requests_enriched
WHERE slice = 'activity_q2_2026' AND borough <> 'Unspecified'
GROUP BY borough, created_month
ORDER BY borough, created_month;
