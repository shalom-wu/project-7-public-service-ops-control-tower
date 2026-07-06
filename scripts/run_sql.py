"""Run the SQL layer end to end and export Power BI-ready tables.

Plumbing only — every piece of logic lives in the .sql files.
Run from the repo root:  python scripts/run_sql.py
"""

from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]

# Views exported for Power BI (view name -> output file).
# The request-level fact ships as Parquet: Power BI Desktop reads it natively
# and it stays ~10x smaller than CSV (GitHub-friendly).
EXPORTS = {
    "v_requests_enriched": "fact_service_requests.parquet",
    "v_kpi_by_agency": "kpi_by_agency.csv",
    "v_kpi_by_complaint_type": "kpi_by_complaint_type.csv",
    "v_kpi_by_borough": "kpi_by_borough.csv",
    "v_kpi_weekly": "kpi_weekly.csv",
    "v_backlog_aging": "backlog_aging.csv",
    "v_priority_scores": "priority_scores.csv",
}


def run_file(con: duckdb.DuckDBPyConnection, name: str, show: bool) -> None:
    print(f"\n=== {name} ===")
    sql = (ROOT / "sql" / name).read_text()
    # Statements end with ';' at end-of-line — never split mid-string
    import re
    for stmt in [s.strip() for s in re.split(r";\s*(?:\n|$)", sql) if s.strip()]:
        result = con.execute(stmt)
        body = re.sub(r"^\s*(--[^\n]*\n)*", "", stmt).lstrip().upper()
        if show and body.startswith(("SELECT", "WITH")):
            print(result.df().to_string(index=False, max_rows=30))
            print()


def main() -> None:
    con = duckdb.connect()
    con.execute(f"SET file_search_path = '{ROOT.as_posix()}'")
    # DuckDB resolves relative paths from the process cwd; pin it to the root
    import os
    os.chdir(ROOT)

    run_file(con, "create_tables.sql", show=False)
    run_file(con, "data_quality_checks.sql", show=True)
    run_file(con, "kpi_views.sql", show=False)
    run_file(con, "analysis_queries.sql", show=True)

    out = ROOT / "data" / "powerbi"
    out.mkdir(parents=True, exist_ok=True)
    print("\n=== exports for Power BI ===")
    for view, fname in EXPORTS.items():
        target = out / fname
        try:
            if target.exists():
                target.unlink()
            if fname.endswith(".parquet"):
                con.execute(f"COPY (SELECT * FROM {view}) TO '{target.as_posix()}' "
                            f"(FORMAT PARQUET, COMPRESSION ZSTD)")
            else:
                con.execute(f"COPY (SELECT * FROM {view}) TO '{target.as_posix()}' "
                            f"(HEADER, DELIMITER ',')")
        except (PermissionError, duckdb.IOException):
            n = con.execute(f"SELECT COUNT(*) FROM {view}").fetchone()[0]
            print(f"  {fname}: kept existing locked file; expected {n:,} rows")
            continue
        n = con.execute(f"SELECT COUNT(*) FROM {view}").fetchone()[0]
        print(f"  {fname}: {n:,} rows")

    # the SLA assumptions and calendar helper also ship to Power BI
    try:
        target = out / "dim_sla_targets.csv"
        if target.exists():
            target.unlink()
        con.execute(f"COPY (SELECT * FROM sla_targets) TO "
                    f"'{target.as_posix()}' (HEADER, DELIMITER ',')")
        print("  dim_sla_targets.csv")
    except (PermissionError, duckdb.IOException):
        n = con.execute("SELECT COUNT(*) FROM sla_targets").fetchone()[0]
        print(f"  dim_sla_targets.csv: kept existing locked file; expected {n:,} rows")
    try:
        target = out / "dim_date.csv"
        if target.exists():
            target.unlink()
        con.execute(
            "COPY (SELECT r::DATE AS date, date_trunc('week', r)::DATE AS week_start, "
            "date_trunc('month', r)::DATE AS month_start, strftime(r, '%a') AS weekday "
            "FROM range(DATE '2025-01-01', DATE '2026-07-01', INTERVAL 1 DAY) t(r)) "
            f"TO '{target.as_posix()}' (HEADER, DELIMITER ',')")
        print("  dim_date.csv")
    except (PermissionError, duckdb.IOException):
        print("  dim_date.csv: kept existing locked file")


if __name__ == "__main__":
    main()
