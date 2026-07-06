# Manual Build Instructions — recreate the .pbix in ~30–45 minutes

Prerequisite: free [Power BI Desktop](https://www.microsoft.com/en-us/download/details.aspx?id=58494)
on Windows. All file paths below are relative to the repo root; data is
regenerated at any time by `python scripts/run_sql.py`.

## 1. Load the data (5 min)

1. **Get Data → Parquet** → `data/powerbi/fact_service_requests.parquet`
   → rename the query `fact_service_requests`.
2. **Get Data → Text/CSV** for each of (rename to match file name, minus
   extension): `dim_date.csv`, `dim_sla_targets.csv`, `priority_scores.csv`,
   `kpi_weekly.csv`, `backlog_aging.csv`.
3. In Power Query, on `fact_service_requests` add a column for the date key:
   **Add Column → Custom Column** → name `created_date_only`, formula
   `Date.From([created_date])`, type Date.
4. Check types: `is_closed` = TRUE/FALSE; `closure_days`, `age_days`,
   `sla_days` = number; both date columns = date/datetime. **Close & Apply.**

## 2. Model (5 min)

1. Model view: drag `fact_service_requests[created_date_only]` onto
   `dim_date[date]` (many-to-one, single).
2. Leave `dim_sla_targets`, `priority_scores`, `kpi_weekly`, `backlog_aging`
   disconnected (reference/aggregate tables — see `data_model.md`).
3. Select `dim_date` → **Table tools → Mark as date table** → column `date`.
4. **Modeling → New parameter → Numeric range** four times:
   `W Volume` (0–1, 0.05, default 0.30), `W Backlog` (…, 0.25),
   `W Miss` (…, 0.25), `W Aged` (…, 0.20). Tick "Add slicer to this page"
   while on page 4 later, or move the slicers there.
5. Create every measure from `dax_measures.md` (copy-paste; put them in a
   dedicated measure table if you like: Home → Enter data → name `_Measures`).
6. Apply the format strings from the bottom of `dax_measures.md`.

## 3. Page 1 — Executive Operations Overview (8 min)

Layout reference: `screenshots/page1_executive_overview.png` (mockup).

1. Page background: white; add a rectangle band across the top, fill
   `#26343F`; title text "Public Service Operations — SLA Control Tower"
   (white, 20pt) + subtitle "NYC 311 · Q2 2026 + aged open backlog ·
   snapshot 2026-07-05" (10pt).
2. Six **Card** visuals across the top: `Total Requests`, `Open Requests`,
   `Closed Requests`, `Backlog Count`, `SLA Miss Rate`, `Average Closure
   Days`.
3. **Line chart**: X = `dim_date[week_start]`, Y = `Total Requests` —
   weekly demand. (Optional second line: `Closed Requests`.)
4. **Bar chart** "Top 5 priority hotspots": table `priority_scores`,
   Y-axis = `complaint_type` & `borough`, X = `priority_score`, filter
   Top N = 5 by `priority_score`. Color `#F4A259`.
5. **Text box** with the headline insight from `dashboard_brief.md`.
6. **Slicers**: `borough`, `agency` (dropdown style, top right).
7. Footer text box: "Source: NYC Open Data 311 (erm2-nwe9) · SLA targets are
   analyst assumptions · see data-sources.md".

## 4. Page 2 — Demand & Complaint Patterns (7 min)

Reference: `screenshots/page2_demand_patterns.png`.

1. **Column chart**: X = `dim_date[date]`, Y = `Total Requests` (daily).
2. **Bar chart**: Y = `complaint_type`, X = `Total Requests`, Top N = 15.
3. **Bar chart**: Y = `agency`, X = `Total Requests`, Top N = 10.
4. **Column chart**: X = `borough`, Y = `Total Requests`.
5. **100% stacked area**: X = `dim_date[week_start]`, Y = `Total Requests`,
   Legend = `complaint_type` filtered Top 5 by `Total Requests` — the
   complaint-mix-over-time view.
6. Slicers: `created_month`, `borough`, `open_data_channel_type`.

## 5. Page 3 — SLA & Backlog Diagnostics (8 min)

Reference: `screenshots/page3_sla_backlog.png`.

1. **Bar chart**: Y = `agency`, X = `SLA Miss Rate` (Top 12 agencies by
   `Total Requests` via visual-level filter), data color `#D64550`; add a
   constant line at the citywide `SLA Miss Rate` value.
2. **Bar chart**: Y = `complaint_type`, X = `SLA Miss Rate`, visual filter
   `Total Requests` ≥ 5000 (mirrors sql/analysis_queries.sql Q6).
3. **Column chart**: X = `aging_bucket` (sort by bucket order via
   Sort by column if desired), Y = `Open Requests`.
4. **Histogram of closure time**: column chart, X = `closure_days` with
   binning (right-click field → New group → Bin size 5 days), Y =
   `Closed Requests`.
5. **Table** "High-risk backlog": `unique_key`, `complaint_type`, `borough`,
   `agency`, `created_date`, `age_days`, `status`; filter `is_closed` =
   FALSE and `aging_bucket` = "180+ days"; sort `age_days` descending;
   conditional formatting (background) on `age_days`, red scale.
6. Slicers: `agency`, `complaint_type`, `aging_bucket`.

## 6. Page 4 — Priority & Action View (7 min)

Reference: `screenshots/page4_priority_action.png`.

1. **Matrix**: Rows = `priority_scores[complaint_type]`, Columns =
   `priority_scores[borough]`, Values = `Dynamic Priority Score`;
   conditional formatting → background color scale white → `#F4A259`.
2. **Table** "Top 10 hotspots": `complaint_type`, `borough`, `agency`,
   `total_requests`, `open_requests`, `sla_miss_rate`,
   `Dynamic Priority Score`, `Dynamic Priority Rank`; filter
   `Dynamic Priority Rank` ≤ 10; sort by rank.
3. Add the four **what-if slicers** (`W Volume`, `W Backlog`, `W Miss`,
   `W Aged`) in a labeled group "Priority weight scenario" — moving them
   re-scores and re-ranks the matrix and table live.
4. **Text boxes** for recommended actions (copy the five focus areas from
   `../reports/strategy_brief.md` §5, or keep them synced with the Excel
   Action_List tab).
5. Footer as on page 1.

## 7. Finish

- Theme colors (optional): View → Themes → Customize — set the palette from
  `dashboard_brief.md`.
- **File → Save As** → `power-bi/public_service_ops_control_tower.pbix`.
- Sanity-check against the Excel workbook: citywide totals, SLA miss rate
  and top hotspots should match `sql/analysis_queries.sql` output (full
  population) — the Excel workbook shows the same rates on its 100K sample.
