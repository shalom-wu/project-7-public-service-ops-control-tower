# Data Sources

## NYC 311 Service Requests

| | |
|---|---|
| **Source name** | 311 Service Requests from 2010 to Present |
| **Original publisher** | City of New York — NYC Open Data / NYC 311 (DoITT/OTI) |
| **Access link** | https://data.cityofnewyork.us/Social-Services/311-Service-Requests-from-2010-to-Present/erm2-nwe9 (Socrata dataset id `erm2-nwe9`) |
| **API endpoint used** | `https://data.cityofnewyork.us/resource/erm2-nwe9.csv` (SODA API, no key required; unauthenticated calls are throttled) |
| **Date accessed** | 2026-07-05 |
| **License/terms** | NYC Open Data terms of use (free public use with attribution) |

*(The brief mentions "2020 to Present" as a common name for this dataset;
the canonical NYC Open Data dataset covers 2010 to present — this project
uses a defined 2025–2026 slice of it, documented below.)*

### What was pulled (real data, none synthetic)

Two SoQL-filtered slices, pulled via `scripts/pull_data.py` in 50,000-row
pages ordered by `unique_key`:

| Slice | Filter | Rows |
|---|---|---|
| Activity window | `created_date >= 2026-04-01 AND < 2026-07-01` | 968,993 |
| Aged open backlog | `created_date >= 2025-01-01 AND < 2026-04-01 AND status != 'Closed'` | 101,825 |

Both row counts were verified against SoQL `count()` queries on the pull
date. Total after de-duplication: **1,070,818 records**.

### Fields used (12 of ~40 available)

`unique_key`, `created_date`, `closed_date`, `agency`, `agency_name`,
`complaint_type`, `descriptor`, `location_type`, `incident_zip`, `borough`,
`status`, `open_data_channel_type`.

### Data classification

- **Real:** every record, timestamp, agency, complaint type, borough and
  status comes from NYC Open Data unmodified.
- **Derived:** `is_closed`, `closure_days`, `age_days`, `sla_status`,
  `aging_bucket`, `created_week/month`, priority scores — computed in the
  SQL layer / Excel formulas from the real fields, with definitions in
  `sql/README.md`.
- **Assumed:** per-complaint-type SLA targets
  (`data/assumptions/sla_targets.csv`) and the 30/25/25/20 priority weights.
  NYC publishes no per-type SLA in this dataset; these are labeled
  decision-support thresholds, editable in one place.
- **Synthetic/augmented:** none.

### Transformations applied (scripts/prepare_data.py — deliberately light)

1. Parse `created_date`/`closed_date` to timestamps.
2. Normalize `borough` to Title Case; blank → `Unspecified`.
3. Trim whitespace on text fields; truncate zip to 5 characters.
4. De-duplicate on `unique_key` (0 duplicates found).
5. Tag each row with its slice (`activity_q2_2026` / `aged_open_backlog`).
6. Produce a 100,000-row random sample (seed 42) for the Excel workbook.

All analytical logic (SLA flags, aging, scoring) lives in SQL and Excel, not
in Python.

### Known limitations of the source

- No staffing, capacity, cost, or resident-satisfaction data.
- `status`/`closed_date` occasionally disagree (1.88% of records; SQL check
  #04) and 0.1% of rows have `closed_date` before `created_date` (check
  #05) — both handled explicitly in the KPI logic.
- The activity window is one quarter; winter-seasonal request types are
  underrepresented.
- "Closed" reflects the city's recording practice, not verified resolution.

### Reproducing the pull

```bash
python scripts/pull_data.py      # ~10 min unauthenticated; resumable
python scripts/prepare_data.py
python scripts/run_sql.py
```

To analyze a different window, edit the `WINDOW_*`/`BACKLOG_START` constants
at the top of `scripts/pull_data.py` and the snapshot dates listed in
`power-bi/refresh_instructions.md`.
