"""Light file preparation: raw 311 pulls -> analysis-ready files.

Deliberately minimal — this script only fixes types, normalizes a few text
fields, and produces right-sized files for each tool. All analytical logic
(SLA flags, aging buckets, priority scores) lives in the SQL layer and the
Excel workbook, where a reviewer can see it.

Outputs
-------
data/processed/service_requests.parquet   full extract (~1.07M rows), typed
data/processed/excel_sample_100k.csv      random 100K-row sample for Excel
data/processed/raw_preview_2k.csv         2,000 raw rows for the workbook's
                                          Raw_Data_Sample tab
data/processed/extract_metadata.txt       pull window, snapshot date, counts
"""

from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"

SNAPSHOT_DATE = date(2026, 7, 5)   # date the extract was pulled
SAMPLE_SIZE = 100_000
SEED = 42

BOROUGH_FIX = {"": "Unspecified", "UNSPECIFIED": "Unspecified"}


def load_slice(name: str, slice_label: str) -> pd.DataFrame:
    df = pd.read_csv(RAW / name, dtype=str)
    df["slice"] = slice_label
    return df


def main() -> None:
    PROCESSED.mkdir(parents=True, exist_ok=True)

    activity = load_slice("raw_requests_2026q2.csv", "activity_q2_2026")
    backlog = load_slice("raw_backlog_open.csv", "aged_open_backlog")

    # keep 2,000 raw activity rows untouched for the workbook's raw-sample tab
    activity.head(2000).to_csv(PROCESSED / "raw_preview_2k.csv", index=False)

    df = pd.concat([activity, backlog], ignore_index=True)

    # --- type fixes ---------------------------------------------------------
    for col in ("created_date", "closed_date"):
        df[col] = pd.to_datetime(df[col], errors="coerce")

    # --- light text normalization ------------------------------------------
    df["borough"] = (df["borough"].fillna("").str.strip().str.upper()
                     .replace(BOROUGH_FIX))
    df["borough"] = df["borough"].str.title().replace({"": "Unspecified"})
    for col in ("agency", "status", "complaint_type", "descriptor",
                "agency_name", "location_type", "open_data_channel_type"):
        df[col] = df[col].fillna("").str.strip()
    df["incident_zip"] = df["incident_zip"].fillna("").str.strip().str[:5]

    df = df.drop_duplicates(subset="unique_key")

    df.to_parquet(PROCESSED / "service_requests.parquet", index=False)

    # --- Excel-sized random sample (proportional across slices) -------------
    rng = np.random.default_rng(SEED)
    idx = rng.choice(len(df), size=SAMPLE_SIZE, replace=False)
    sample = df.iloc[np.sort(idx)]
    sample.to_csv(PROCESSED / "excel_sample_100k.csv", index=False)

    meta = (
        f"Extract pulled: {SNAPSHOT_DATE.isoformat()}\n"
        f"Dataset: NYC Open Data erm2-nwe9 (311 Service Requests 2010-Present)\n"
        f"Activity window: created 2026-04-01 .. 2026-06-30 -> {len(activity):,} rows\n"
        f"Aged open backlog: created 2025-01-01 .. 2026-03-31, not Closed -> {len(backlog):,} rows\n"
        f"Total after de-dup: {len(df):,} rows\n"
        f"Excel sample: {SAMPLE_SIZE:,} rows, seed {SEED} "
        f"(scaling factor {len(df)/SAMPLE_SIZE:.4f})\n"
    )
    (PROCESSED / "extract_metadata.txt").write_text(meta)
    print(meta)


if __name__ == "__main__":
    main()
