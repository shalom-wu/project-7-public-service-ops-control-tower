# Data Manifest

This Excel + SQL + Power BI project is self-contained. The repo includes the raw NYC Open Data extracts, processed parquet, Excel sample, assumptions, and dashboard-ready tables.

| File | Type | Shape / size | Used by | Notes |
|---|---|---:|---|---|
| `raw/raw_requests_2026q2.csv` | Real raw public extract | 968,993 x 12, 160.6 MB | SQL, processing | NYC Open Data 311 extract, Q2 2026 activity slice. |
| `raw/raw_backlog_open.csv` | Real raw public extract | 101,825 x 12, 15.1 MB | SQL, processing | Open backlog extract used for aging analysis. |
| `processed/service_requests.parquet` | Real processed extract | 1,070,818 x 13, 20.8 MB | SQL, Power BI build | Typed and lightly standardized request table. |
| `processed/excel_sample_100k.csv` | Real sample/extract | 100,000 x 13, 17.3 MB | Excel | Workbook-friendly sample; full-population KPIs stay in SQL/Power BI. |
| `processed/raw_preview_2k.csv` | Real preview sample | 2,000 x 13, 372.5 KB | Excel/readme review | Small preview for workbook/readme inspection. |
| `assumptions/sla_targets.csv` | Assumed | 31 x 3, 1.6 KB | Excel, SQL, Power BI | Analyst-defined SLA targets by complaint type. |
| `powerbi/fact_service_requests.parquet` | Derived | 1,070,818 x 21, 13.6 MB | Power BI | Dashboard fact table with SLA, age, and calendar fields. |
| `powerbi/dim_date.csv` | Derived | 546 x 4, 19.8 KB | Power BI | Date helper table. |
| `powerbi/dim_sla_targets.csv` | Assumed | 31 x 3, 1.6 KB | Power BI | Same SLA target table used by Excel and SQL. |
| `powerbi/kpi_by_agency.csv` | Derived aggregate | 15 x 9, 1.2 KB | Power BI | Agency-level volume, closure, SLA, and backlog metrics. |
| `powerbi/kpi_by_borough.csv` | Derived aggregate | 6 x 7, <1 KB | Power BI | Borough-level operating metrics. |
| `powerbi/kpi_by_complaint_type.csv` | Derived aggregate | 188 x 9, 9.4 KB | Power BI | Complaint-type operating metrics. |
| `powerbi/kpi_weekly.csv` | Derived aggregate | 14 x 6, <1 KB | Power BI | Weekly demand and SLA trend. |
| `powerbi/backlog_aging.csv` | Derived aggregate | 30 x 4, <1 KB | Power BI | Aging bucket by borough. |
| `powerbi/priority_scores.csv` | Derived + assumed | 369 x 11, 26.8 KB | Power BI | Priority score using documented weights and SLA/backlog metrics. |

The source is real public NYC 311 data. SLA targets and priority weights are analyst assumptions, not official city service standards unless separately verified.
