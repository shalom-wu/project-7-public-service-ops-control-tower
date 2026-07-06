# Explain It to Me: The SLA Control Tower, No Jargon Required

Plain-English guide to the whole project — what it is, how each piece works,
and how to talk about it. Technical terms are **bolded and defined on first
use**; there's a [glossary](#glossary) at the end.

## The 30-second explanation

"New York's 311 line takes about 75,000 service requests a week — noise,
broken heating, fallen trees, illegal parking. I built the monitoring system
an operations team would need to run that: a dashboard and workbook showing
how much work is coming in, whether it's getting closed fast enough, and
what's quietly rotting in the backlog. The headline: a million-plus requests
analyzed, and the problem isn't volume — half of all demand gets closed
within hours — it's that 168,000 open requests have piled up, and
three-quarters of them are already more than a month old, concentrated in a
handful of very specific workflows the model points at by name."

## The 2-minute explanation

Add these beats:

- "I used real public data — NYC's 311 service requests, 1.07 million
  records from 2026 — deliberately framed as an operations problem, not a
  data-science one. It's the same shape as a customer-support queue or a
  field-service operation: tickets come in, teams close them, some age out."
- "The build mirrors how analyst teams actually work. **SQL** validates the
  data and defines every metric once — nine data-quality checks caught
  things like 20,000 records where the status field and the closure date
  disagree. **Excel** holds the working model: every assumption — service
  targets, aging thresholds, priority weights — is an editable cell, and
  the whole workbook recalculates. **Power BI** is the executive view with
  scenario sliders."
- "Since NYC doesn't publish response-time targets per request type, I set
  them myself and labeled them clearly as assumptions — each with a
  rationale, all adjustable in one place. When something misses an assumed
  target 99% of the time, the finding isn't 'they failed' — it's 'this
  target is fiction; go agree a real one.'"
- "The priority model is deliberately simple: each request-type-and-borough
  cell gets a weighted score from volume, open backlog, target misses, and
  aging. Simple enough to explain to a room; the weights are sliders, so if
  leadership cares more about aging than volume, the ranking re-sorts live."

## The 5-minute explanation

Walk the pipeline end to end: the two-slice data pull (a full quarter of
activity plus every older still-open request, so the backlog picture is
honest); the data-quality gate and what it caught; how "closed", "age", and
"SLA miss" are defined precisely (ages measured to a fixed snapshot date so
results reproduce; open requests still inside their window excluded from
the miss rate because they haven't succeeded or failed yet); the
sample-vs-population design in Excel; the priority score arithmetic; the
top findings — parks and tree work, taxi-complaint case backlogs, the
helicopter-noise reporting artifact, the seasonal heat warning — and the
recommended weekly/monthly operating rhythm with escalation criteria. Close
with limitations: no staffing data, assumed targets, "closed" as a
recording fact.

## How the Excel workbook works

Ten tabs, designed to be opened by a stakeholder, not a programmer:

1. **README** — what it is, how to use it, color key (blue = editable
   input, black = formula, green = linked from another tab).
2. **Raw_Data_Sample** — 2,000 rows exactly as they came from NYC, so you
   can see what cleaning changed.
3. **Cleaned_Data** — the engine room: 100,000 randomly-sampled requests in
   a named table, with derived columns computed by live formulas — is it
   closed, how long did closure take, how old is it now, which service
   target applies (looked up with INDEX/MATCH against the Assumptions tab),
   did it meet that target, which aging bucket it falls in.
4. **Data_Dictionary** — every field defined, including which are raw,
   prepared, or formula-derived.
5. **Assumptions** — the control panel. Service targets per request type
   (with rationale), aging bucket boundaries, priority weights (with a red
   flag if they don't sum to 100%), the snapshot date, and the scaling
   factor from sample to full population. Change anything here and every
   downstream number updates.
6. **Pivot_Analysis** — six native pivot tables (by agency, request type,
   borough, month, week, SLA status) plus two pivot charts, all fed by the
   cleaned table.
7. **SLA_Analysis** — met/missed metrics by agency, borough, request type
   and month, built with COUNTIFS/AVERAGEIFS, with color scales flagging
   the worst rates.
8. **Backlog_Analysis** — open-request KPIs, an aging-bucket × borough
   matrix with data bars, weekly created-vs-closed flow with a chart, and a
   live "20 oldest open requests" list.
9. **Priority_Model** — the 75-cell scoring grid (top 15 request types ×
   5 boroughs) with every component visible: counts, miss rates,
   percentiles, weighted score, rank.
10. **Action_List** — top-10 hotspots pulled live from the model, four
    recommended focus areas in plain English, and the operating rhythm.

Why a sample? A million rows would make a sluggish 200MB workbook nobody
opens. A random 100K sample keeps every *rate* unbiased; volumes are
labeled and a scaling factor grosses them up; the SQL layer recomputes
everything on the full data as the cross-check (they agree to ~0.1pp).

## How the SQL layer works

Four scripts on **DuckDB** (a zero-install local database):
`create_tables.sql` loads the full extract and pins the snapshot date;
`data_quality_checks.sql` runs nine checks (duplicates, missing dates,
closed-before-created sequences, status disagreements...) each returning a
count and a note; `kpi_views.sql` defines every metric once — the same
definitions Excel and Power BI implement; `analysis_queries.sql` asks ten
operational questions (where demand concentrates, worst SLA performers,
oldest unresolved items, month-over-month change). A small Python runner
executes them and exports the Power BI tables. If a number in the workbook
and the dashboard ever disagreed, this layer is the referee.

## How the Power BI dashboard works

Four pages: Executive Overview (KPI cards, weekly trend, top-5 hotspots,
headline insight), Demand & Complaint Patterns, SLA & Backlog Diagnostics,
and Priority & Action View — where the interesting part lives: the four
priority weights are **what-if sliders**, so a leadership meeting can drag
"aging" up and watch the ranking re-sort live. One honest note: the build
environment had no Power BI Desktop, so the repo ships the complete build
kit — data model, every DAX measure, page mockups rendered from the real
data, and click-by-click instructions that rebuild the dashboard in about
40 minutes. The mockups are labeled as mockups; nothing pretends to be a
screenshot.

## Likely interview questions (spoken answers)

**"Why 311 data for an operations project?"**

> "Because it's the same machine as any service operation — a queue of
> tickets, teams closing them, backlog aging — at a scale you can't fake:
> 75,000 requests a week, dozens of request types, five boroughs. And it's
> public and verifiable, so an interviewer can check every number I claim."

**"Walk me through the priority score."**

> "Four ingredients per request-type-and-borough cell: how big it is —
> volume percentile; how much is sitting open — backlog percentile; how
> often it misses its target; and what share of its open work is already
> old. Weighted 30-25-25-20, and the weights are editable cells and
> dashboard sliders. Percentiles stop the giant categories from winning on
> size alone. Deliberately simple — a prioritization you can't explain in
> one breath doesn't survive its first leadership meeting."

**"What was the messiest data problem?"**

> "Status and closure date disagreeing — about 20,000 records marked
> in-progress but carrying a closure date, and 1,100 closed before they
> were created. I made closure logic depend on the date, documented the
> disagreement as a data-quality check with its exact count, and excluded
> impossible sequences from timing metrics. The rule I follow: measure the
> mess, don't hide it."

**"What's the single biggest caveat?"**

> "No staffing data. A 60,000-item aged backlog might mean process failure
> or might mean three people doing ten people's work — the data can't tell
> you which, so the project never claims to. It tells you *where* to look,
> not *who* to blame."

## Glossary

| Term | Plain-English meaning |
|---|---|
| **311** | NYC's non-emergency service line — potholes, noise, heating complaints. |
| **Service request** | One ticket: a resident reports a problem, an agency handles it. |
| **Agency** | The city department that owns the request (NYPD, Parks, Housing...). |
| **SLA (service-level agreement)** | A target for how fast something should be handled — "close noise complaints within 1 day." Assumed, not official, in this project. |
| **SLA miss rate** | Of requests whose outcome is known, the share that blew past their target. |
| **Backlog** | Requests still open at the snapshot date. |
| **Aging / aging bucket** | How long an open request has waited, grouped (0-7, 8-30, 31-90, 91-180, 180+ days). |
| **Snapshot date** | The fixed date (2026-07-05) ages are measured against, so results reproduce. |
| **Control tower** | A recurring monitoring view for running an operation — demand in, work out, risk flagged. |
| **Priority score** | The 0–1 weighted blend of volume, backlog, misses and aging that ranks hotspots. |
| **Percentile rank** | Where a value sits relative to all others (0.95 = bigger than 95% of them). |
| **Pivot table** | Excel's drag-and-drop summarizer — counts and averages by any category. |
| **COUNTIFS / AVERAGEIFS** | Excel formulas that count/average rows matching several conditions at once. |
| **Named table / named cell** | Excel ranges with readable names, so formulas say `SnapshotDate`, not `$C$5`. |
| **DuckDB** | A tiny local analytics database — runs SQL on files, no server needed. |
| **SQL view** | A saved query that defines a metric once, reusable everywhere. |
| **DAX** | Power BI's formula language for measures. |
| **What-if parameter** | A Power BI slider whose value feeds formulas — used here for the priority weights. |
| **Star schema** | A dashboard-friendly data layout: one big fact table ringed by small lookup tables. |
| **Reporting artifact** | A pattern created by how data is recorded, not by reality — like 19K helicopter-noise requests that never get marked closed. |
