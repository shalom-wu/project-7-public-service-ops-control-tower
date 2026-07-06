# Public Service Operations Control Tower (e)

This repository builds an Excel-led operations control tower from public NYC 311 service-request data. It includes SQL KPI definitions, a 10-tab Excel workbook, and a Power BI dashboard for request volume, closure performance, SLA misses, backlog aging, and priority scoring.

The `(e)` marker identifies this as one of the Excel-based projects.

## Project Summary

| Area | Details |
|---|---|
| Business question | Which service-request categories and boroughs need operational attention based on volume, SLA risk, backlog age, and priority score? |
| Data | NYC Open Data 311 service requests: Q2 2026 requests plus older still-open requests back to January 2025, snapshot 2026-07-05. |
| Methods | Data extraction, quality checks, SLA assumptions, backlog aging, priority scoring, SQL KPI views, Excel pivots, Power BI dashboarding. |
| Main outputs | Excel workbook, SQL KPI layer, Power BI dashboard, strategy brief, screenshots. |
| Tools | Excel, Python, DuckDB SQL, Power BI, Power BI Project files. |

## Key Findings

| # | Finding | Evidence |
|---|---|---|
| 1 | Q2 request volume is high and rising. | About 969K Q2 requests, or roughly 75K per week. |
| 2 | The open backlog is material. | About 168K requests are open at the snapshot date. |
| 3 | Much of the backlog is old. | 77% of open backlog is older than 30 days, and 36% is older than 180 days. |
| 4 | SLA misses are concentrated by request type. | Citywide miss rate is 18.7% under the documented assumed targets. |
| 5 | Enforcement and works-type demand behave differently. | NYPD handles 48% of Q2 demand with very short average closure times. |
| 6 | Reporting artifacts are flagged, not hidden. | Helicopter-noise requests show about 19K unclosed records and are explicitly called out as a likely recording issue. |

![Power BI dashboard - Executive Operations Overview](power-bi/screenshots/pbix_page1_executive_overview.png)

## Data

The project uses [NYC Open Data - 311 Service Requests](https://data.cityofnewyork.us/Social-Services/311-Service-Requests-from-2010-to-Present/erm2-nwe9), dataset `erm2-nwe9`. The snapshot includes every request created from April through June 2026 plus older still-open requests back to January 2025.

This is public city service-request data, not private company operations data. Staffing and true agency capacity are not in the dataset and are not inferred. Full citation, field list, and reproduction steps are in [data-sources.md](data-sources.md).

## Methodology

1. Pull the public 311 extract and normalize request dates, statuses, boroughs, agencies, and complaint types.
2. Define SLA assumptions and aging buckets in editable assumption files.
3. Validate the data and compute full-population KPIs in DuckDB SQL.
4. Build a 100K-row Excel sample with live formulas, pivot tables, and editable assumptions.
5. Build a Power BI dashboard from SQL exports with executive, demand, SLA/backlog, and priority pages.

## Repository Contents

| Path | Purpose |
|---|---|
| [excel/](excel) | 10-tab Excel control tower workbook with assumptions, pivots, formulas, and action views. |
| [sql/](sql) | DuckDB data-quality checks, KPI views, analysis queries, and priority scoring. |
| [power-bi/](power-bi) | Working `.pbix`, PBIP source, DAX, model documentation, refresh notes, and screenshots. |
| [reports/](reports) | Strategy brief and supporting reporting notes. |
| [scripts/](scripts) | Data pull, preparation, SQL export, workbook build, and workbook finalization scripts. |
| [data/](data) | Source extracts, assumptions, processed files, and Power BI exports. |

## Reproduce

Requires Python 3.11+. Desktop Excel on Windows is required for the final pivot-table and recalculation step.

```bash
git clone https://github.com/shalom-wu/public-service-ops-control-tower.git
cd public-service-ops-control-tower
pip install pandas pyarrow duckdb openpyxl requests

python scripts/pull_data.py
python scripts/prepare_data.py
python scripts/run_sql.py
python scripts/build_workbook.py
python scripts/finalize_workbook.py
```

Open [power-bi/public_service_ops_control_tower.pbix](power-bi/public_service_ops_control_tower.pbix) in Power BI Desktop to inspect the imported dashboard.

## Reporting Layer

SQL is the source of truth for full-population KPI definitions. Excel is the editable working model with a labeled sample, live formulas, pivots, and assumptions. Power BI is the dashboard layer using SQL exports and what-if style reporting views.

The three layers are designed to reconcile: SQL owns the official counts, Excel makes assumptions auditable, and Power BI presents the stakeholder dashboard.

## Limitations

- The dataset has no staffing or capacity fields.
- SLA targets are analyst assumptions because NYC does not publish per-type SLA targets in this dataset.
- "Closed" is a recorded status, not verified resolution.
- One quarter plus inherited backlog underrepresents seasonal categories.
- Excel uses a labeled 100K random sample for file-size reasons; full-population counts come from SQL and Power BI.

## License And Credit

MIT License. Copyright (c) 2026 Shalom Wu.

Data credit: City of New York, NYC Open Data 311 Service Requests dataset (`erm2-nwe9`). See [data-sources.md](data-sources.md) for source notes, fields, and usage caveats.
