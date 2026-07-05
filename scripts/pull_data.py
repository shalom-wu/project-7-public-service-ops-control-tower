"""Pull the NYC 311 extract from NYC Open Data (Socrata API).

Support script only — all analysis lives in Excel, SQL, and Power BI.

Two slices are pulled into data/raw/:
  1. activity window  : every request CREATED in the analysis quarter
  2. aged open backlog: requests created before the window (back to
                        2025-01-01) that were still not Closed at pull time

Dataset: "311 Service Requests from 2010 to Present" (erm2-nwe9)
         https://data.cityofnewyork.us/Social-Services/311-Service-Requests-from-2010-to-Present/erm2-nwe9
No API key required; unauthenticated requests are throttled but work.
"""

import csv
import io
import sys
import time
from pathlib import Path

import requests

BASE = "https://data.cityofnewyork.us/resource/erm2-nwe9.csv"
COLS = ("unique_key,created_date,closed_date,agency,agency_name,"
        "complaint_type,descriptor,location_type,incident_zip,borough,"
        "status,open_data_channel_type")
PAGE = 50_000

WINDOW_START = "2026-04-01T00:00:00"
WINDOW_END = "2026-07-01T00:00:00"      # exclusive
BACKLOG_START = "2025-01-01T00:00:00"

RAW = Path(__file__).resolve().parents[1] / "data" / "raw"


def existing_rows(path: Path) -> int:
    """Rows already pulled (minus header) so an interrupted pull resumes."""
    if not path.exists():
        return 0
    with open(path, "rb") as f:
        return max(0, sum(1 for _ in f) - 1)


def pull(where: str, out_name: str, expected: int) -> int:
    out = RAW / out_name
    total = existing_rows(out)
    if total >= expected:
        print(f"  {out_name}: already complete ({total:,} rows)", flush=True)
        return total
    # resume only from clean page boundaries; otherwise restart the file
    if total % PAGE != 0:
        total = 0
    offset = total
    if total:
        print(f"  resuming {out_name} at {total:,} rows", flush=True)
    mode = "a" if total else "w"
    with open(out, mode, newline="", encoding="utf-8") as f:
        while True:
            params = {
                "$select": COLS,
                "$where": where,
                "$order": "unique_key",
                "$limit": PAGE,
                "$offset": offset,
            }
            for attempt in range(5):
                try:
                    r = requests.get(BASE, params=params, timeout=180)
                    r.raise_for_status()
                    break
                except Exception as e:  # retry with backoff on throttle/timeouts
                    wait = 15 * (attempt + 1)
                    print(f"  retry {attempt+1} after error: {e} (sleep {wait}s)",
                          flush=True)
                    time.sleep(wait)
            else:
                raise RuntimeError(f"giving up on offset {offset}")

            text = r.content.decode("utf-8")
            reader = list(csv.reader(io.StringIO(text)))
            header, rows = reader[0], reader[1:]
            if offset == 0 and total == 0:
                csv.writer(f).writerow(header)
            csv.writer(f).writerows(rows)
            total += len(rows)
            print(f"  {out_name}: {total:,} rows", flush=True)
            if len(rows) < PAGE:
                break
            offset += PAGE
    return total


if __name__ == "__main__":
    RAW.mkdir(parents=True, exist_ok=True)
    print("Slice 1: activity window (created in analysis quarter)", flush=True)
    n1 = pull(
        f"created_date >= '{WINDOW_START}' AND created_date < '{WINDOW_END}'",
        "raw_requests_2026q2.csv",
        expected=968_993,   # count verified via SoQL count() on 2026-07-05
    )
    print("Slice 2: aged open backlog (older, still not Closed)", flush=True)
    n2 = pull(
        f"created_date >= '{BACKLOG_START}' AND created_date < '{WINDOW_START}'"
        " AND status != 'Closed'",
        "raw_backlog_open.csv",
        expected=101_825,   # count verified via SoQL count() on 2026-07-05
    )
    print(f"DONE. activity={n1:,} backlog={n2:,}", flush=True)
    sys.exit(0)
