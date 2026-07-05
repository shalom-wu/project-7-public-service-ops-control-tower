-- ============================================================================
-- kpi_views.sql — the KPI logic, defined once and reused everywhere
-- (Excel and Power BI implement the same definitions; this layer is the
-- reproducible reference implementation.)
-- ============================================================================

-- ----------------------------------------------------------------------------
-- Enriched request-level view: every derived field the KPIs need.
-- Definitions:
--   is_closed      : has a valid closed_date on/before snapshot (+1d grace)
--   closure_days   : closed - created, in days (invalid sequences excluded)
--   age_days       : snapshot - created, for OPEN requests
--   sla_days       : assumed target for the complaint type (DEFAULT fallback)
--   sla_status     : Met | Missed | Open Within SLA | Open Past SLA
--   aging_bucket   : 0-7 / 8-30 / 31-90 / 91-180 / 180+ days (open requests)
-- ----------------------------------------------------------------------------
CREATE OR REPLACE VIEW v_requests_enriched AS
WITH m AS (SELECT * FROM meta),
     d AS (SELECT sla_days AS default_sla FROM sla_targets WHERE complaint_type = 'DEFAULT')
SELECT
    r.*,
    (r.closed_date IS NOT NULL
     AND r.closed_date >= r.created_date
     AND r.closed_date <  (SELECT snapshot_date + INTERVAL 1 DAY FROM m)) AS is_closed,
    CASE WHEN r.closed_date IS NOT NULL AND r.closed_date >= r.created_date
         THEN date_diff('day', r.created_date, r.closed_date) END          AS closure_days,
    CASE WHEN r.closed_date IS NULL OR r.closed_date < r.created_date
         THEN date_diff('day', r.created_date,
                        (SELECT snapshot_date::TIMESTAMP FROM m)) END      AS age_days,
    COALESCE(s.sla_days, (SELECT default_sla FROM d))                      AS sla_days,
    CASE
        WHEN r.closed_date IS NOT NULL AND r.closed_date >= r.created_date THEN
            CASE WHEN date_diff('day', r.created_date, r.closed_date)
                      <= COALESCE(s.sla_days, (SELECT default_sla FROM d))
                 THEN 'Met' ELSE 'Missed' END
        ELSE
            CASE WHEN date_diff('day', r.created_date,
                                (SELECT snapshot_date::TIMESTAMP FROM m))
                      <= COALESCE(s.sla_days, (SELECT default_sla FROM d))
                 THEN 'Open Within SLA' ELSE 'Open Past SLA' END
    END                                                                    AS sla_status,
    CASE WHEN r.closed_date IS NULL OR r.closed_date < r.created_date THEN
        CASE
            WHEN date_diff('day', r.created_date, (SELECT snapshot_date::TIMESTAMP FROM m)) <= 7   THEN '0-7 days'
            WHEN date_diff('day', r.created_date, (SELECT snapshot_date::TIMESTAMP FROM m)) <= 30  THEN '8-30 days'
            WHEN date_diff('day', r.created_date, (SELECT snapshot_date::TIMESTAMP FROM m)) <= 90  THEN '31-90 days'
            WHEN date_diff('day', r.created_date, (SELECT snapshot_date::TIMESTAMP FROM m)) <= 180 THEN '91-180 days'
            ELSE '180+ days'
        END END                                                            AS aging_bucket,
    date_trunc('week',  r.created_date)::DATE                              AS created_week,
    date_trunc('month', r.created_date)::DATE                              AS created_month
FROM service_requests r
LEFT JOIN sla_targets s USING (complaint_type);

-- ----------------------------------------------------------------------------
-- KPI rollups. "SLA miss rate" counts Missed + Open Past SLA over all
-- requests with a resolved SLA outcome (Met + Missed + Open Past SLA);
-- open-but-still-within-SLA requests are excluded because their outcome is
-- not yet known.
-- ----------------------------------------------------------------------------
CREATE OR REPLACE VIEW v_kpi_by_agency AS
SELECT
    agency,
    any_value(agency_name)                                   AS agency_name,
    COUNT(*)                                                 AS total_requests,
    COUNT(*) FILTER (WHERE is_closed)                        AS closed_requests,
    COUNT(*) FILTER (WHERE NOT is_closed)                    AS open_requests,
    ROUND(AVG(closure_days), 1)                              AS avg_closure_days,
    ROUND(MEDIAN(closure_days), 1)                           AS median_closure_days,
    ROUND(1.0 * COUNT(*) FILTER (WHERE sla_status IN ('Missed', 'Open Past SLA'))
        / NULLIF(COUNT(*) FILTER (WHERE sla_status <> 'Open Within SLA'), 0), 4) AS sla_miss_rate,
    COUNT(*) FILTER (WHERE NOT is_closed
                     AND aging_bucket IN ('31-90 days', '91-180 days', '180+ days')) AS aged_open_30d_plus
FROM v_requests_enriched
GROUP BY agency;

CREATE OR REPLACE VIEW v_kpi_by_complaint_type AS
SELECT
    complaint_type,
    any_value(agency)                                        AS primary_agency,
    COUNT(*)                                                 AS total_requests,
    COUNT(*) FILTER (WHERE is_closed)                        AS closed_requests,
    COUNT(*) FILTER (WHERE NOT is_closed)                    AS open_requests,
    ROUND(AVG(closure_days), 1)                              AS avg_closure_days,
    ROUND(MEDIAN(closure_days), 1)                           AS median_closure_days,
    ROUND(1.0 * COUNT(*) FILTER (WHERE sla_status IN ('Missed', 'Open Past SLA'))
        / NULLIF(COUNT(*) FILTER (WHERE sla_status <> 'Open Within SLA'), 0), 4) AS sla_miss_rate,
    COUNT(*) FILTER (WHERE NOT is_closed
                     AND aging_bucket IN ('31-90 days', '91-180 days', '180+ days')) AS aged_open_30d_plus
FROM v_requests_enriched
GROUP BY complaint_type;

CREATE OR REPLACE VIEW v_kpi_by_borough AS
SELECT
    borough,
    COUNT(*)                                                 AS total_requests,
    COUNT(*) FILTER (WHERE is_closed)                        AS closed_requests,
    COUNT(*) FILTER (WHERE NOT is_closed)                    AS open_requests,
    ROUND(AVG(closure_days), 1)                              AS avg_closure_days,
    ROUND(1.0 * COUNT(*) FILTER (WHERE sla_status IN ('Missed', 'Open Past SLA'))
        / NULLIF(COUNT(*) FILTER (WHERE sla_status <> 'Open Within SLA'), 0), 4) AS sla_miss_rate,
    COUNT(*) FILTER (WHERE NOT is_closed
                     AND aging_bucket IN ('31-90 days', '91-180 days', '180+ days')) AS aged_open_30d_plus
FROM v_requests_enriched
GROUP BY borough;

-- Weekly demand vs closure (activity window only, so both series are complete)
CREATE OR REPLACE VIEW v_kpi_weekly AS
SELECT
    created_week,
    COUNT(*)                                       AS requests_created,
    COUNT(*) FILTER (WHERE is_closed)              AS eventually_closed,
    COUNT(*) FILTER (WHERE NOT is_closed)          AS still_open,
    ROUND(AVG(closure_days), 1)                    AS avg_closure_days,
    ROUND(1.0 * COUNT(*) FILTER (WHERE sla_status IN ('Missed', 'Open Past SLA'))
        / NULLIF(COUNT(*) FILTER (WHERE sla_status <> 'Open Within SLA'), 0), 4) AS sla_miss_rate
FROM v_requests_enriched
WHERE slice = 'activity_q2_2026'
GROUP BY created_week
ORDER BY created_week;

-- Backlog aging distribution (open requests only)
CREATE OR REPLACE VIEW v_backlog_aging AS
SELECT
    aging_bucket,
    borough,
    COUNT(*)                        AS open_requests,
    ROUND(AVG(age_days), 0)         AS avg_age_days
FROM v_requests_enriched
WHERE NOT is_closed
GROUP BY aging_bucket, borough;

-- ----------------------------------------------------------------------------
-- Priority scores at the actionable unit: complaint_type x borough.
-- Transparent weighted model (weights mirrored in Excel Assumptions tab):
--   30% demand volume + 25% open backlog + 25% SLA miss rate + 20% aged share
-- Volume and backlog enter as percentile ranks so no single huge category
-- dominates by scale alone. Cells under 200 requests are excluded as noise.
-- ----------------------------------------------------------------------------
CREATE OR REPLACE VIEW v_priority_scores AS
WITH cells AS (
    SELECT
        complaint_type,
        borough,
        any_value(agency)                                    AS agency,
        COUNT(*)                                             AS total_requests,
        COUNT(*) FILTER (WHERE NOT is_closed)                AS open_requests,
        ROUND(1.0 * COUNT(*) FILTER (WHERE sla_status IN ('Missed', 'Open Past SLA'))
            / NULLIF(COUNT(*) FILTER (WHERE sla_status <> 'Open Within SLA'), 0), 4) AS sla_miss_rate,
        ROUND(1.0 * COUNT(*) FILTER (WHERE NOT is_closed AND aging_bucket IN ('31-90 days', '91-180 days', '180+ days'))
            / NULLIF(COUNT(*) FILTER (WHERE NOT is_closed), 0), 4)                    AS aged_share_of_open
    FROM v_requests_enriched
    WHERE borough <> 'Unspecified'
    GROUP BY complaint_type, borough
    HAVING COUNT(*) >= 200
)
, scored AS (
    SELECT
        complaint_type,
        borough,
        agency,
        total_requests,
        open_requests,
        sla_miss_rate,
        COALESCE(aged_share_of_open, 0)                      AS aged_share_of_open,
        ROUND(  0.30 * percent_rank() OVER (ORDER BY total_requests)
              + 0.25 * percent_rank() OVER (ORDER BY open_requests)
              + 0.25 * COALESCE(sla_miss_rate, 0)
              + 0.20 * COALESCE(aged_share_of_open, 0), 4)   AS priority_score
    FROM cells
)
SELECT *,
       ROW_NUMBER() OVER (ORDER BY priority_score DESC)      AS priority_rank
FROM scored;
