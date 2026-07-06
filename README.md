# Public Service Operations - SLA Control Tower

This repository builds an operations control tower from public NYC 311 service-request data. It includes SQL KPI definitions, an Excel workbook, and a Power BI dashboard for request volume, closure performance, SLA misses, backlog aging, and priority scoring.
**Data:** [NYC Open Data — 311 Service Requests](https://data.cityofnewyork.us/Social-Services/311-Service-Requests-from-2010-to-Present/erm2-nwe9)
(dataset `erm2-nwe9`): every request created Apr–Jun 2026 (968,993) plus all
older still-open requests back to Jan 2025 (101,825), snapshot 2026-07-05.
This is **public city service-request data, not private company operations
data** — staffing and true agency capacity are not in the dataset and are
never claimed. Full citation, field list and reproduction steps:
[data-sources.md](data-sources.md).

## Key findings (snapshot 2026-07-05)

| # | Finding | Number |
|---|---|---|
| 1 | Q2 request volume, and rising through the quarter (Queens +11.0% then +6.5% MoM) | **969K** (~75K/week) |
| 2 | Open backlog at snapshot | **~168K** requests |
| 3 | Share of open backlog already older than 30 / 180 days | **77% / 36%** |
| 4 | Citywide SLA miss rate vs assumed targets | **18.7%** |
| 5 | Worst high-volume SLA performers: Taxi Complaint, Root/Sewer/Sidewalk, Overgrown Tree/Branches | **99.6% / 99.5% / 88.5%** miss |
| 6 | NYPD share of Q2 demand — closed in hours (enforcement vs works-type demand is the operational fault line) | **48%**, 0.2-day avg closure |
| 7 | Helicopter-noise requests unclosed (reporting artifact, flagged not hidden) | **~19K, 100% open** |

![Power BI dashboard — Executive Operations Overview (actual Desktop capture)](power-bi/screenshots/pbix_page1_executive_overview.png)

## Repository contents

| Layer | Deliverable |
|---|---|
| **Excel** | [`excel/public_service_ops_control_tower.xlsx`](excel/public_service_ops_control_tower.xlsx) — 10 tabs: README, raw sample, 100K-row cleaned table with live formula columns, data dictionary, editable assumptions (SLA targets, aging buckets, priority weights), native pivot tables + pivot charts, SLA analysis, backlog analysis, priority model, action list. Zero formula errors; verified by full recalculation in Excel. |
| **SQL** | [`sql/`](sql) — DuckDB scripts: 9 data-quality checks, KPI views (the reference definitions), 10 analysis queries, priority scoring. [`sql/README.md`](sql/README.md) documents every definition. |
| **Power BI** | [`power-bi/public_service_ops_control_tower.pbix`](power-bi/public_service_ops_control_tower.pbix) — the working 4-page dashboard with the full 1.07M-row extract imported: executive KPIs, demand patterns, SLA/backlog diagnostics, and a priority matrix with what-if weight sliders. Authored as code (the PBIP semantic-model + report source is committed alongside), documented in [`power-bi/`](power-bi) with model docs, DAX reference, and real Desktop screenshots. |
| **Strategy** | [`reports/strategy_brief.md`](reports/strategy_brief.md) — findings, the priority model, a weekly/monthly operating rhythm, escalation criteria, limitations. |

## How the three tools work together

**SQL is the source of truth** — every KPI (closure, SLA miss, aging,
priority score) is defined once in `sql/kpi_views.sql` against the full
1.07M-row extract. **Excel is the working model** — a 100K-row random sample
with the same definitions as live formulas, so every assumption (SLA
targets, weights, buckets) is editable and everything recalculates.
**Power BI is the dashboard layer** — the SQL exports load into a star
schema with what-if weight sliders on the priority model. Rates agree across
all three; volumes in Excel are labeled as sample-based with a scaling
factor.

## How to use it

**Just exploring?** Open the Excel workbook (start at its README tab), or
read the [strategy brief](reports/strategy_brief.md) and the
[dashboard mockups](power-bi/screenshots).

**Reproducing from scratch:**

```bash
pip install pandas pyarrow duckdb openpyxl requests   # pywin32 for the Excel pivot step
python scripts/pull_data.py        # ~10 min: pulls the 1.07M-row extract from NYC Open Data
python scripts/prepare_data.py     # typing + normalization + Excel sample
python scripts/run_sql.py          # DQ checks, KPI views, Power BI exports
python scripts/build_workbook.py   # workbook structure + formulas
python scripts/finalize_workbook.py  # pivot tables + recalc (needs desktop Excel on Windows)
```

**Opening the Power BI dashboard:** open
[`power-bi/public_service_ops_control_tower.pbix`](power-bi/public_service_ops_control_tower.pbix)
in the free Power BI Desktop — data is already imported. To rebuild from
scratch instead, follow
[`power-bi/manual_build_instructions.md`](power-bi/manual_build_instructions.md).

## Limitations

- **No staffing/capacity data** — high backlog may mean under-resourcing,
  not negligence; this project never equates the two.
- **SLA targets are analyst assumptions**, reasoned and documented in
  [`data/assumptions/sla_targets.csv`](data/assumptions/sla_targets.csv),
  adjustable in one place. NYC publishes no per-type SLA in this dataset.
- **"Closed" is a recording fact, not verified resolution.** 1.9% of records
  have status/date disagreements — measured, documented (SQL check #04) and
  handled explicitly.
- **One quarter + inherited backlog** — winter-seasonal types (heat/hot
  water) are underrepresented; flagged wherever it matters.
- The Excel workbook runs on a labeled 100K random sample for file-size
  sanity; rates are unbiased, volumes carry a scaling factor, and
  full-population numbers come from SQL/Power BI.

## Author

Shalom Wu ([@shalom-wu](https://github.com/shalom-wu)). Data: City of New
York, NYC Open Data (`erm2-nwe9`). MIT licensed.
