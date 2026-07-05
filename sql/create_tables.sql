-- ============================================================================
-- create_tables.sql — load the 311 extract into DuckDB
-- Run from the repo root (the runner script scripts/run_sql.py does this).
-- ============================================================================

-- Analysis snapshot: the date the extract was pulled. Open-request ages are
-- measured against this date, never against "today", so results reproduce.
CREATE OR REPLACE TABLE meta AS
SELECT
    DATE '2026-07-05'  AS snapshot_date,
    DATE '2026-04-01'  AS window_start,
    DATE '2026-07-01'  AS window_end;      -- exclusive

-- Full extract: Q2-2026 activity window + aged open backlog (from 2025-01-01)
CREATE OR REPLACE TABLE service_requests AS
SELECT
    unique_key,
    created_date::TIMESTAMP                    AS created_date,
    closed_date::TIMESTAMP                     AS closed_date,
    agency,
    agency_name,
    complaint_type,
    descriptor,
    location_type,
    incident_zip,
    borough,
    status,
    open_data_channel_type,
    slice
FROM read_parquet('data/processed/service_requests.parquet');

-- SLA targets are an ASSUMPTION layer (NYC publishes no per-type SLA in this
-- dataset). Same file feeds the Excel Assumptions tab and Power BI.
CREATE OR REPLACE TABLE sla_targets AS
SELECT complaint_type, sla_days::INTEGER AS sla_days, rationale
FROM read_csv_auto('data/assumptions/sla_targets.csv', header = true);
