# Dashboard Brief — Public Service Operations SLA Control Tower

## Audience & purpose

A weekly/monthly decision-support view for a service-operations lead. The
dashboard answers three questions in under two minutes:

1. **How much demand is coming in, and are we keeping up?**
2. **Where is SLA risk and aged backlog concentrating?**
3. **What should the team focus on this week?**

Data: NYC Open Data 311 Service Requests (dataset `erm2-nwe9`) — every
request created 2026-04-01 → 2026-06-30 plus all older still-open requests
back to 2025-01-01 (1,070,818 records, snapshot 2026-07-05). This is public
city service-request data; staffing and internal agency capacity are not in
the dataset and are not shown.

## Headline insight (as of the 2026-07-05 snapshot)

> Q2 demand ran ~75K requests/week and rose through the quarter (Queens +11%
> and +6.5% MoM). Closure keeps pace for enforcement-type requests (NYPD
> closes in hours), but a structural backlog of ~168K open requests has
> accumulated — **77% of it already older than 30 days, 36% older than 180
> days** — concentrated in parks/tree work (DPR), TLC complaint cases, and
> HPD housing conditions. One reporting artifact matters: all ~19K
> helicopter-noise requests are unclosed, which inflates citywide backlog
> KPIs unless reported separately.

## Pages

### 1 — Executive Operations Overview
KPI cards: Total Requests, Open Requests, Closed Requests, Backlog Count,
SLA Miss Rate, Avg Closure Days. Top-5 priority hotspots (bar), weekly
created-vs-closed trend, and the headline insight as a text callout.
*Slicers: borough, agency.*

### 2 — Demand & Complaint Patterns
Requests by week/day (line + column), top complaint types (bar), agency mix
(bar), borough mix (column), complaint mix over time (100% stacked area of
top 5 types). *Slicers: month, borough, channel.*

### 3 — SLA & Backlog Diagnostics
SLA miss rate by agency and by complaint type (bars vs target line), backlog
aging buckets (column), closure-time distribution (histogram), high-risk
backlog table (oldest open, priority-hotspot members first).
*Slicers: agency, complaint type, aging bucket.*

### 4 — Priority & Action View
Priority-score matrix (complaint type × borough heatmap), top-10 hotspot
table with score components, recommended next actions (text tiles), and
**what-if weight sliders** (volume / backlog / SLA miss / aging) that
recompute the priority score live so stakeholders can stress-test the
ranking. *The 30/25/25/20 base weights match the Excel Assumptions tab and
the SQL layer.*

## Design language

- Palette: dark slate `#26343F` header band, teal `#1F7A8C` for healthy/
  volume series, red `#D64550` for SLA misses & aged backlog, amber
  `#F4A259` for priority highlights, light grey `#F2F6F8` card background.
- KPI cards top-left → narrative left-to-right, top-to-bottom.
- Every page carries the source + snapshot-date footer:
  *"NYC Open Data 311 (erm2-nwe9) · snapshot 2026-07-05 · SLA targets are
  analyst assumptions".*
