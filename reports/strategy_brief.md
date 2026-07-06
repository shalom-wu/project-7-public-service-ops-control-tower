# Strategy Brief — Public Service Operations SLA Control Tower

*Basis: NYC Open Data 311 Service Requests (`erm2-nwe9`) — all 968,993
requests created Apr 1 – Jun 30, 2026 plus 101,825 older still-open requests
(back to Jan 1, 2025). Snapshot date 2026-07-05. SLA targets are analyst-set
decision-support thresholds; NYC publishes no per-type SLA in this dataset.*

## 1. The problem

A service-operations team fielding ~75,000 requests a week cannot manage by
anecdote. It needs one recurring view that answers: how much demand is
coming in, are we closing it fast enough, what is silently aging in the
backlog, and where should this week's attention go? Public 311 data gives a
realistic, full-scale environment to build exactly that.

## 2. What the control tower does

- **Excel workbook** (`excel/public_service_ops_control_tower.xlsx`) — the
  analyst's working model: cleaned 100K-row sample, every assumption
  editable (SLA targets, aging buckets, priority weights), live pivot
  tables, SLA and backlog diagnostics, a transparent priority model, and a
  plain-English action list.
- **SQL layer** (`sql/`) — DuckDB scripts that validate the full 1.07M-row
  extract (9 data-quality checks) and compute every KPI once, as the
  reference definitions. Outputs feed both Excel and Power BI.
- **Power BI dashboard** (4 pages, build kit in `power-bi/`) — the
  stakeholder view: executive KPIs, demand patterns, SLA/backlog
  diagnostics, and a priority matrix with what-if weight sliders.

## 3. Key findings (snapshot 2026-07-05)

1. **Demand is high and rising.** ~969K requests in Q2; weekly volume grew
   from ~69K (early April) to ~78K (late June). Queens rose two months
   straight (+11.0%, then +6.5%).
2. **Closure is a tale of two operations.** Enforcement-type demand (NYPD:
   460K requests, 48% of Q2 volume) closes in hours. Inspection- and
   works-type demand (HPD, DPR, DOT, DOHMH) runs days-to-weeks, and that is
   where backlog accumulates.
3. **The backlog is old.** ~168K requests are open; **77% are already past
   30 days old and 36% past 180 days**. The aged core sits in parks/tree
   work (DPR — Overgrown Tree/Branches, Root/Sewer/Sidewalk, Maintenance or
   Facility), TLC taxi/FHV complaint cases, and HPD housing conditions.
4. **SLA misses are concentrated, not general.** Citywide miss rate is
   18.7% against the assumed targets, but the worst high-volume performers
   are structural: Taxi Complaint 99.6%, Root/Sewer/Sidewalk 99.5%,
   Overgrown Tree/Branches 88.5%, Street Light Condition 60.1%.
5. **One reporting artifact matters.** All ~19K helicopter-noise requests
   (EDC) in the window are unclosed. That is a recording/workflow artifact
   to resolve with the owning agency — but until then it should be reported
   as its own line so it doesn't distort citywide backlog KPIs.

## 4. The priority model

Each complaint-type × borough cell gets a transparent weighted score:

> **Priority = 30% × volume percentile + 25% × open-backlog percentile +
> 25% × SLA miss rate + 20% × aged share of open requests**

Percentiles keep giant categories from dominating on scale alone; the four
weights are editable in one place (Excel Assumptions tab, Power BI what-if
sliders, SQL view). Cells under 200 requests are excluded as noise.

**Current top priorities:** helicopter noise (Manhattan/Brooklyn/Queens —
pending the artifact check), Overgrown Tree/Branches (Brooklyn, Queens),
Taxi Complaint (Manhattan, Queens), Root/Sewer/Sidewalk Condition
(Brooklyn), For-Hire-Vehicle Complaint (Manhattan), with HEAT/HOT WATER
(Bronx) the highest-volume seasonal watch item.

## 5. Recommended operating rhythm

| Cadence | Ritual |
|---|---|
| **Weekly (30 min)** | Refresh extract → Executive Overview: demand vs closure, SLA miss drift, any new entrant to the top-10 hotspot list. Assign one owner per top-5 hotspot. |
| **Monthly (60 min)** | Trend review: complaint-mix shift, borough MoM, aging distribution. Re-baseline SLA targets that are structurally missed (a target missed 99% of the time is a fiction, not a target). |
| **Escalate when** | a hotspot's SLA miss rate exceeds 60%; its 31+ day open count grows two consecutive weeks; any single request crosses 180 days; or "Unspecified borough" share rises above 0.5%. |
| **One-time cleanups** | (a) close-or-escalate triage of the 180+ day backlog (~60K items), (b) resolve the helicopter-noise recording artifact, (c) clear aged HEAT/HOT WATER residue before the October heat season. |

## 6. Limitations — stated plainly

- **Staffing and capacity are invisible.** The dataset records requests and
  closures, not headcount, budgets, or workload per officer/inspector. High
  backlog ≠ negligence; it may equal under-resourcing. Nothing here claims
  otherwise.
- **SLA targets are assumptions.** Reasoned, documented, adjustable — but
  analyst-set. The right next step is replacing them with agency-agreed
  targets.
- **Closure quality depends on city recording practice.** "Closed" means
  closed in the 311 system; 1.9% of records have status/date disagreements
  (documented in SQL check #04) and closure ≠ resident satisfaction.
- **The window is one quarter plus its inherited backlog.** Seasonal
  patterns (winter heat complaints) are structurally underrepresented in a
  Q2 snapshot and flagged as such wherever relevant.
