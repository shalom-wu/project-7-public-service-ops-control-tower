# SQL Layer — Reproducible Validation & KPI Reference

This folder is the **reference implementation of every KPI** in the project.
The Excel workbook and the Power BI dashboard both implement the same
definitions; when in doubt, this SQL is the source of truth.

Runs locally on [DuckDB](https://duckdb.org/) — no database server needed.

## Files (run in this order)

| File | What it does |
|---|---|
| `create_tables.sql` | Loads the processed extract + SLA assumptions into DuckDB; pins the analysis snapshot date (2026-07-05) so results reproduce |
| `data_quality_checks.sql` | 9 checks: duplicate keys, missing/invalid dates, closed-before-created sequences, status/date disagreements, borough & zip coverage |
| `kpi_views.sql` | The KPI logic: enriched request view (SLA status, aging buckets, closure days) + rollups by agency / complaint type / borough / week + the priority-score model |
| `analysis_queries.sql` | 10 standalone questions an ops lead would ask (demand concentration, closure pace, hotspots, oldest unresolved items, channel mix, MoM change) |

## How to run

With Python (used by this repo's tooling):

```bash
pip install duckdb
python scripts/run_sql.py     # runs everything + exports Power BI tables
```

Or with the DuckDB CLI from the repo root:

```sql
.read sql/create_tables.sql
.read sql/data_quality_checks.sql
.read sql/kpi_views.sql
.read sql/analysis_queries.sql
```

## Key definitions (mirrored in Excel and Power BI)

- **Closed** — has a valid `closed_date` on/before the snapshot date, not
  earlier than `created_date`.
- **Closure days** — `closed_date - created_date` in days; invalid sequences
  excluded.
- **Age (open requests)** — days from `created_date` to the snapshot date
  (2026-07-05), never to "today", so results are stable.
- **SLA status** — `Met` / `Missed` for closed requests, `Open Within SLA` /
  `Open Past SLA` for open ones, against the **assumed** per-type targets in
  `data/assumptions/sla_targets.csv` (NYC publishes no per-type SLA in this
  dataset — these are decision-support thresholds, adjustable in one file).
- **SLA miss rate** — (Missed + Open Past SLA) ÷ all requests with a known
  SLA outcome. Open requests still inside their SLA window are excluded —
  they haven't succeeded or failed yet.
- **Priority score** — per complaint-type × borough cell:
  `30% × volume percentile + 25% × backlog percentile + 25% × SLA miss rate
  + 20% × aged share of open`. Cells with <200 requests excluded.

## Outputs

`scripts/run_sql.py` exports the view results as CSVs into `data/powerbi/`,
which are the exact tables the Power BI dashboard loads.
