-- ============================================================================
-- data_quality_checks.sql — reproducible data-quality gate
-- Every check returns:  check_name | records_flagged | pct_of_total | note
-- A healthy load shows 0 (or a small, explained number) in records_flagged.
-- ============================================================================

WITH total AS (SELECT COUNT(*) AS n FROM service_requests)

SELECT '01 duplicate unique_key' AS check_name,
       COUNT(*) - COUNT(DISTINCT unique_key)        AS records_flagged,
       ROUND(100.0 * (COUNT(*) - COUNT(DISTINCT unique_key)) / MAX(t.n), 3) AS pct_of_total,
       'each service request should appear exactly once' AS note
FROM service_requests, total t

UNION ALL
SELECT '02 missing created_date',
       COUNT(*) FILTER (WHERE created_date IS NULL),
       ROUND(100.0 * COUNT(*) FILTER (WHERE created_date IS NULL) / MAX(t.n), 3),
       'created_date is required for every downstream metric'
FROM service_requests, total t

UNION ALL
SELECT '03 closed status but no closed_date',
       COUNT(*) FILTER (WHERE status = 'Closed' AND closed_date IS NULL),
       ROUND(100.0 * COUNT(*) FILTER (WHERE status = 'Closed' AND closed_date IS NULL) / MAX(t.n), 3),
       'these rows are excluded from closure-time metrics'
FROM service_requests, total t

UNION ALL
SELECT '04 closed_date but status not Closed',
       COUNT(*) FILTER (WHERE closed_date IS NOT NULL AND status NOT IN ('Closed')),
       ROUND(100.0 * COUNT(*) FILTER (WHERE closed_date IS NOT NULL AND status NOT IN ('Closed')) / MAX(t.n), 3),
       'status/closed_date disagreement — closure logic uses closed_date'
FROM service_requests, total t

UNION ALL
SELECT '05 closed before created (invalid sequence)',
       COUNT(*) FILTER (WHERE closed_date < created_date),
       ROUND(100.0 * COUNT(*) FILTER (WHERE closed_date < created_date) / MAX(t.n), 3),
       'negative closure times are excluded from closure-time metrics'
FROM service_requests, total t

UNION ALL
SELECT '06 closed in the future (after snapshot)',
       COUNT(*) FILTER (WHERE closed_date > (SELECT snapshot_date + INTERVAL 1 DAY FROM meta)),
       ROUND(100.0 * COUNT(*) FILTER (WHERE closed_date > (SELECT snapshot_date + INTERVAL 1 DAY FROM meta)) / MAX(t.n), 3),
       'closure timestamps later than the extract snapshot'
FROM service_requests, total t

UNION ALL
SELECT '07 borough missing/unspecified',
       COUNT(*) FILTER (WHERE borough IS NULL OR borough = 'Unspecified'),
       ROUND(100.0 * COUNT(*) FILTER (WHERE borough IS NULL OR borough = 'Unspecified') / MAX(t.n), 3),
       'kept, reported as their own "Unspecified" borough'
FROM service_requests, total t

UNION ALL
SELECT '08 missing complaint_type',
       COUNT(*) FILTER (WHERE complaint_type IS NULL OR complaint_type = ''),
       ROUND(100.0 * COUNT(*) FILTER (WHERE complaint_type IS NULL OR complaint_type = '') / MAX(t.n), 3),
       'complaint_type drives SLA mapping and priority scoring'
FROM service_requests, total t

UNION ALL
SELECT '09 zip not 5 digits (where present)',
       COUNT(*) FILTER (WHERE incident_zip <> '' AND NOT regexp_matches(incident_zip, '^[0-9]{5}$')),
       ROUND(100.0 * COUNT(*) FILTER (WHERE incident_zip <> '' AND NOT regexp_matches(incident_zip, '^[0-9]{5}$')) / MAX(t.n), 3),
       'zip is descriptive only and not used in KPI logic'
FROM service_requests, total t

ORDER BY check_name;
