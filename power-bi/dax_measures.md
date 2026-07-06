# DAX Measures

Copy-paste ready. All measures live on `fact_service_requests` unless noted.
Definitions mirror the SQL layer (`sql/kpi_views.sql`) and the Excel workbook
— one KPI logic, three tools.

## Core volumes

```dax
Total Requests = COUNTROWS ( fact_service_requests )

Closed Requests =
CALCULATE ( [Total Requests], fact_service_requests[is_closed] = TRUE () )

Open Requests =
CALCULATE ( [Total Requests], fact_service_requests[is_closed] = FALSE () )

Closure Rate = DIVIDE ( [Closed Requests], [Total Requests] )

Backlog Count = [Open Requests]
```

## Closure time

```dax
Average Closure Days = AVERAGE ( fact_service_requests[closure_days] )

Median Closure Days = MEDIAN ( fact_service_requests[closure_days] )
```

*(`closure_days` is null for open requests, so both aggregate over closed
requests only — no extra filter needed.)*

## SLA

```dax
SLA Missed =
CALCULATE (
    [Total Requests],
    fact_service_requests[sla_status] IN { "Missed", "Open Past SLA" }
)

SLA Outcomes Known =
CALCULATE (
    [Total Requests],
    fact_service_requests[sla_status] <> "Open Within SLA"
)

SLA Miss Rate = DIVIDE ( [SLA Missed], [SLA Outcomes Known] )
```

*Open requests still inside their SLA window are excluded from the
denominator — they have not succeeded or failed yet. SLA targets are analyst
assumptions (see `dim_sla_targets[rationale]`).*

## Backlog aging

```dax
Aging Backlog Count =
CALCULATE (
    [Open Requests],
    fact_service_requests[aging_bucket]
        IN { "31-90 days", "91-180 days", "180+ days" }
)

Aged Share of Backlog = DIVIDE ( [Aging Backlog Count], [Open Requests] )
```

## Shares & time comparison

```dax
Share of Total Requests =
DIVIDE (
    [Total Requests],
    CALCULATE ( [Total Requests], ALLSELECTED ( fact_service_requests ) )
)

Requests Previous Month =
CALCULATE ( [Total Requests], PREVIOUSMONTH ( dim_date[date] ) )

MoM Request Change % =
DIVIDE ( [Total Requests] - [Requests Previous Month], [Requests Previous Month] )
```

*(Requires the `fact → dim_date` relationship and `dim_date` marked as the
date table. Note: the extract window is Apr–Jun 2026 plus older open
backlog, so MoM is meaningful inside the activity window.)*

## Priority model (on `priority_scores`)

```dax
Priority Score (Static) = MAX ( priority_scores[priority_score] )
-- SQL-computed with base weights 30/25/25/20; matches Excel + kpi_views.sql

Dynamic Priority Score =
VAR w_vol  = SELECTEDVALUE ( 'W Volume'[W Volume], 0.30 )
VAR w_back = SELECTEDVALUE ( 'W Backlog'[W Backlog], 0.25 )
VAR w_miss = SELECTEDVALUE ( 'W Miss'[W Miss], 0.25 )
VAR w_aged = SELECTEDVALUE ( 'W Aged'[W Aged], 0.20 )
VAR wsum   = w_vol + w_back + w_miss + w_aged
RETURN
    DIVIDE (
          w_vol  * AVERAGE ( priority_scores[volume_percentile] )
        + w_back * AVERAGE ( priority_scores[backlog_percentile] )
        + w_miss * AVERAGE ( priority_scores[sla_miss_rate] )
        + w_aged * AVERAGE ( priority_scores[aged_share_of_open] ),
        wsum
    )
-- Normalized by the weight sum so sliders never need to total exactly 1.

Dynamic Priority Rank =
RANKX (
    ALLSELECTED ( priority_scores ),
    [Dynamic Priority Score],
    ,
    DESC,
    DENSE
)
```

## Formatting conventions

| Measure | Format |
|---|---|
| volumes / counts | `#,0` |
| rates / shares / MoM | `0.0%` |
| closure days | `0.0` |
| priority scores | `0.000` |
