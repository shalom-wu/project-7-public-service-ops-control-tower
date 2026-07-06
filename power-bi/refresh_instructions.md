# Refresh Instructions

## Refreshing the underlying data (new extract)

From the repo root:

```bash
# 1. Re-pull from NYC Open Data (adjust the window constants at the top
#    of the script for a new quarter; counts in the script are for the
#    2026-07-05 pull and only guard resume logic)
python scripts/pull_data.py

# 2. Re-prepare typed files + the Excel sample
python scripts/prepare_data.py

# 3. Re-run data-quality checks, KPI views and Power BI exports
python scripts/run_sql.py
```

Step 3 rewrites everything in `data/powerbi/` (the Parquet fact table, KPI
CSVs, and dimension tables). **Update the snapshot date** in two places when
you re-pull: `SNAPSHOT_DATE` in `scripts/prepare_data.py` and the
`snapshot_date` constant in `sql/create_tables.sql` — open-request ages are
measured against it.

## Refreshing Power BI

With the `.pbix` built (see `manual_build_instructions.md`):

1. Open the file in Power BI Desktop.
2. **Home → Refresh.** All queries point at `data/powerbi/`; if your repo
   lives at a different path, update the source once via
   Transform data → Data source settings → Change Source.
3. Verify the footer/snapshot text box still matches the new extract window.

## Refreshing the Excel workbook

Two options:

- **Scripted rebuild (exact reproduction):**
  `python scripts/build_workbook.py && python scripts/finalize_workbook.py`
- **In-place refresh:** replace the rows in `Cleaned_Data` with a new sample
  (`data/processed/excel_sample_100k.csv`), update `SnapshotDate` and
  `PopulationRows` on the Assumptions tab, then Data → Refresh All to update
  the pivot tables.

## Suggested cadence

| Rhythm | What |
|---|---|
| Weekly | steps 1–3 + Power BI refresh; review Executive Overview + Priority pages |
| Monthly | full rebuild including Excel; review trend pages and re-baseline SLA targets if misses are structural |
