"""Generate the 4-page report definition (report.json) for the PBIP project.

Uses the classic PBIP report format: sections -> visualContainers with
stringified per-visual config. Layout mirrors power-bi/dashboard_brief.md
and the mockups in power-bi/screenshots.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_pbip_model as bm

DARK, TEAL, RED, AMBER = "#26343F", "#1F7A8C", "#D64550", "#F4A259"
FACT = "fact_service_requests"
STRIP_UNSAFE_FORMATTING = True
_counter = [0]


def uid():
    _counter[0] += 1
    return f"vc{_counter[0]:04d}"


def lit(v):
    if isinstance(v, bool):
        return {"expr": {"Literal": {"Value": "true" if v else "false"}}}
    if isinstance(v, (int, float)):
        return {"expr": {"Literal": {"Value": f"{v}D"}}}
    return {"expr": {"Literal": {"Value": f"'{v}'"}}}


def src(entity, alias):
    return {"Name": alias, "Entity": entity, "Type": 0}


def col_expr(alias, prop):
    return {"Column": {"Expression": {"SourceRef": {"Source": alias}}, "Property": prop}}


def meas_expr(alias, prop):
    return {"Measure": {"Expression": {"SourceRef": {"Source": alias}}, "Property": prop}}


def select_col(entity, alias, prop):
    return {**col_expr(alias, prop), "Name": f"{entity}.{prop}",
            "NativeReferenceName": prop}


def select_meas(entity, alias, prop):
    return {**meas_expr(alias, prop), "Name": f"{entity}.{prop}",
            "NativeReferenceName": prop}


def container(x, y, w, h, z, config, filters=None):
    c = {"x": x, "y": y, "z": z, "width": w, "height": h,
         "config": json.dumps(config)}
    if filters and not STRIP_UNSAFE_FORMATTING:
        c["filters"] = json.dumps(filters)
    return c


def visual(vtype, x, y, w, h, z, projections, froms, selects, order_by=None,
           objects=None, vc_objects=None, filters=None):
    sv = {
        "visualType": vtype,
        "projections": projections,
        "prototypeQuery": {
            "Version": 2,
            "From": froms,
            "Select": selects,
            **({"OrderBy": order_by} if order_by else {}),
        },
        "drillFilterOtherVisuals": True,
    }
    if objects and not STRIP_UNSAFE_FORMATTING:
        sv["objects"] = objects
    if vc_objects and not STRIP_UNSAFE_FORMATTING:
        sv["vcObjects"] = vc_objects
    cfg = {"name": uid(),
           "layouts": [{"id": 0, "position": {"x": x, "y": y, "z": z,
                                              "width": w, "height": h}}],
           "singleVisual": sv}
    return container(x, y, w, h, z, cfg, filters)


def title_obj(text, size=10):
    return {"title": [{"properties": {
        "show": lit(True), "text": lit(text),
        "fontColor": {"solid": {"color": lit(DARK)}},
        "fontSize": lit(size), "bold": lit(True)}}]}


def textbox(x, y, w, h, z, runs, background=None, font_size=None):
    paragraphs = []
    for line in runs:
        tr = []
        for text, props in line:
            run = {"value": text}
            ts = dict(props or {})
            if font_size and "fontSize" not in ts:
                ts["fontSize"] = f"{font_size}pt"
            if ts:
                run["textStyle"] = ts
            tr.append(run)
        paragraphs.append({"textRuns": tr})
    sv = {"visualType": "textbox",
          "objects": {"general": [{"properties": {"paragraphs": paragraphs}}]},
          "drillFilterOtherVisuals": True}
    if background and not STRIP_UNSAFE_FORMATTING:
        sv["vcObjects"] = {"background": [{"properties": {
            "show": lit(True), "color": {"solid": {"color": lit(background)}},
            "transparency": lit(0)}}]}
    cfg = {"name": uid(),
           "layouts": [{"id": 0, "position": {"x": x, "y": y, "z": z,
                                              "width": w, "height": h}}],
           "singleVisual": sv}
    return container(x, y, w, h, z, cfg)


def header(title_text, subtitle):
    return [
        textbox(0, 0, 1280, 68, 0,
                [[(title_text, {"fontSize": "20pt", "fontWeight": "bold",
                                "color": DARK if STRIP_UNSAFE_FORMATTING else "#FFFFFF"})],
                 [(subtitle, {"fontSize": "10pt",
                              "color": "#41505B" if STRIP_UNSAFE_FORMATTING else "#9FB3BE"})]],
                background=DARK),
        textbox(0, 696, 1280, 24, 0,
                [[("Source: NYC Open Data — 311 Service Requests (erm2-nwe9) · snapshot 2026-07-05 · "
                   "SLA targets are analyst assumptions", {"fontSize": "8pt", "color": "#8896A0"})]]),
    ]


def card(entity, measure_name, x, y, w=160, h=90, z=100):
    a = entity[0]
    return visual("card", x, y, w, h, z,
                  {"Values": [{"queryRef": f"{entity}.{measure_name}"}]},
                  [src(entity, a)], [select_meas(entity, a, measure_name)],
                  objects={"labels": [{"properties": {"fontSize": lit(20)}}]},
                  vc_objects=title_obj(measure_name))


def slicer(entity, column, x, y, w=170, h=80, z=100, mode="Dropdown", title=None):
    a = entity[0]
    return visual("slicer", x, y, w, h, z,
                  {"Values": [{"queryRef": f"{entity}.{column}"}]},
                  [src(entity, a)], [select_col(entity, a, column)],
                  objects={"data": [{"properties": {"mode": lit(mode)}}]},
                  vc_objects=title_obj(title or column))


def bar(entity, cat, measure_entity, measure_name, x, y, w, h, z, title,
        vtype="clusteredBarChart", color=TEAL, filters=None, cat_entity=None):
    cat_entity = cat_entity or entity
    froms, aliases = [], {}
    for e in {cat_entity, measure_entity}:
        aliases[e] = f"t{len(froms)}"
        froms.append(src(e, aliases[e]))
    selects = [select_col(cat_entity, aliases[cat_entity], cat),
               select_meas(measure_entity, aliases[measure_entity], measure_name)]
    order = [{"Direction": 2,
              "Expression": meas_expr(aliases[measure_entity], measure_name)}]
    return visual(vtype, x, y, w, h, z,
                  {"Category": [{"queryRef": f"{cat_entity}.{cat}", "active": True}],
                   "Y": [{"queryRef": f"{measure_entity}.{measure_name}"}]},
                  froms, selects, order_by=order,
                  objects={"dataPoint": [{"properties": {
                      "defaultColor": {"solid": {"color": lit(color)}}}}]},
                  vc_objects=title_obj(title), filters=filters)


def line(cat_entity, cat, measure_entity, measures, x, y, w, h, z, title,
         vtype="lineChart"):
    froms, aliases = [], {}
    for e in dict.fromkeys([cat_entity, measure_entity]):
        aliases[e] = f"t{len(froms)}"
        froms.append(src(e, aliases[e]))
    selects = [select_col(cat_entity, aliases[cat_entity], cat)]
    selects += [select_meas(measure_entity, aliases[measure_entity], m)
                for m in measures]
    return visual(vtype, x, y, w, h, z,
                  {"Category": [{"queryRef": f"{cat_entity}.{cat}", "active": True}],
                   "Y": [{"queryRef": f"{measure_entity}.{m}"} for m in measures]},
                  froms, selects, vc_objects=title_obj(title))


def table_vis(entity, fields, x, y, w, h, z, title, filters=None, extra=None):
    """fields: list of (kind, entity, name) where kind is 'col'/'meas'."""
    froms, aliases = [], {}
    entities = dict.fromkeys([e for _, e, _ in fields])
    for e in entities:
        aliases[e] = f"t{len(froms)}"
        froms.append(src(e, aliases[e]))
    selects, refs = [], []
    for kind, e, nm in fields:
        if kind == "col":
            selects.append(select_col(e, aliases[e], nm))
        else:
            selects.append(select_meas(e, aliases[e], nm))
        refs.append({"queryRef": f"{e}.{nm}"})
    order = extra.get("order_by") if extra else None
    return visual("tableEx", x, y, w, h, z, {"Values": refs}, froms, selects,
                  order_by=order, vc_objects=title_obj(title), filters=filters)


def in_filter(entity, column, values, bool_literal=False):
    def vlit(v):
        if bool_literal:
            return {"Literal": {"Value": "true" if v else "false"}}
        return {"Literal": {"Value": f"'{v}'"}}
    return {
        "name": uid(),
        "expression": {"Column": {"Expression": {"SourceRef": {"Entity": entity}},
                                  "Property": column}},
        "filter": {"Version": 2, "From": [src(entity, "t")],
                   "Where": [{"Condition": {"In": {
                       "Expressions": [col_expr("t", column)],
                       "Values": [[vlit(v)] for v in values]}}}]},
        "type": "Categorical",
        "howCreated": 1,
    }


# ===========================================================================
# Page 1 — Executive Operations Overview
# ===========================================================================
p1 = header("Public Service Operations — SLA Control Tower",
            "Executive Operations Overview · NYC 311 · Q2 2026 activity + aged open backlog")
cards = ["Total Requests", "Open Requests", "Closed Requests", "Backlog Count",
         "SLA Miss Rate", "Average Closure Days"]
for i, m in enumerate(cards):
    p1.append(card(FACT, m, x=16 + i * 168, y=84, w=158, h=92, z=10 + i))
p1.append(line("dim_date", "week_start", FACT, ["Total Requests", "Closed Requests"],
               16, 192, 640, 260, 30, "Weekly demand vs closure"))
p1.append(bar("priority_scores", "complaint_type", "priority_scores",
              "Priority Score (Static)", 672, 192, 400, 260, 31,
              "Priority hotspots by complaint type", color=AMBER))
p1.append(slicer(FACT, "borough", 1088, 192, 176, 120, 32))
p1.append(slicer(FACT, "agency", 1088, 322, 176, 130, 33))
p1.append(textbox(16, 468, 1248, 216, 40, [
    [("Headline insight", {"fontSize": "12pt", "fontWeight": "bold", "color": DARK})],
    [("Q2 demand ran ~75K requests/week and rose through the quarter (Queens +11.0% then +6.5% MoM). "
      "Enforcement-type requests close in hours, but a structural backlog of ~168K open requests has built up — "
      "77% already older than 30 days, 36% older than 180 days — concentrated in parks/tree work (DPR), "
      "TLC complaint cases and housing conditions (HPD). All ~19K helicopter-noise requests are unclosed "
      "(reporting artifact): report that line separately so it doesn't distort citywide KPIs.",
      {"fontSize": "11pt", "color": "#41505B"})]], background="#FDF6EC"))

# ===========================================================================
# Page 2 — Demand & Complaint Patterns
# ===========================================================================
p2 = header("Demand & Complaint Patterns",
            "Where service demand concentrates: time, request type, agency, borough")
p2.append(line("dim_date", "date", FACT, ["Total Requests"],
               16, 84, 620, 250, 10, "Daily requests", vtype="columnChart"))
p2.append(bar(FACT, "complaint_type", FACT, "Total Requests",
              652, 84, 612, 400, 11, "Requests by complaint type (sorted; scroll for full list)"))
p2.append(bar(FACT, "agency", FACT, "Total Requests",
              16, 350, 300, 334, 12, "Requests by agency"))
p2.append(bar(FACT, "borough", FACT, "Total Requests",
              332, 350, 304, 334, 13, "Requests by borough",
              vtype="clusteredColumnChart"))
p2.append(visual("stackedAreaChart", 652, 500, 440, 184, 14,
                 {"Category": [{"queryRef": "dim_date.week_start", "active": True}],
                  "Series": [{"queryRef": f"{FACT}.borough"}],
                  "Y": [{"queryRef": f"{FACT}.Total Requests"}]},
                 [src("dim_date", "d"), src(FACT, "f")],
                 [select_col("dim_date", "d", "week_start"),
                  select_col(FACT, "f", "borough"),
                  select_meas(FACT, "f", "Total Requests")],
                 vc_objects=title_obj("Weekly demand mix by borough")))
p2.append(slicer(FACT, "created_month", 1108, 500, 156, 88, 15, title="month"))
p2.append(slicer(FACT, "open_data_channel_type", 1108, 596, 156, 88, 16, title="channel"))

# ===========================================================================
# Page 3 — SLA & Backlog Diagnostics
# ===========================================================================
p3 = header("SLA & Backlog Diagnostics",
            "Miss rates vs assumed targets · backlog aging · the oldest unresolved work")
p3.append(bar(FACT, "agency", FACT, "SLA Miss Rate",
              16, 84, 400, 300, 10, "SLA miss rate by agency", color=RED))
p3.append(bar(FACT, "complaint_type", FACT, "SLA Miss Rate",
              432, 84, 420, 300, 11, "SLA miss rate by complaint type", color=RED))
p3.append(bar(FACT, "aging_bucket", FACT, "Open Requests",
              868, 84, 396, 300, 12, "Backlog aging buckets",
              vtype="clusteredColumnChart", color=AMBER))
p3.append(bar(FACT, "complaint_type", FACT, "Median Closure Days",
              16, 400, 400, 284, 13, "Median closure days by complaint type"))
p3.append(table_vis(FACT,
                    [("col", FACT, "unique_key"), ("col", FACT, "complaint_type"),
                     ("col", FACT, "borough"), ("col", FACT, "agency"),
                     ("col", FACT, "status"), ("col", FACT, "age_days")],
                    432, 400, 660, 284, 14,
                    "High-risk backlog — open requests aged 180+ days (sorted oldest first)",
                    filters=[in_filter(FACT, "is_closed", [False], bool_literal=True),
                             in_filter(FACT, "aging_bucket", ["180+ days"])],
                    extra={"order_by": [{"Direction": 2,
                                         "Expression": col_expr("t0", "age_days")}]}))
p3.append(slicer(FACT, "aging_bucket", 1108, 400, 156, 130, 15))

# ===========================================================================
# Page 4 — Priority & Action View
# ===========================================================================
p4 = header("Priority & Action View",
            "Weighted priority score by complaint type × borough — what-if sliders re-rank live")
p4.append(visual("pivotTable", 16, 84, 560, 420, 10,
                 {"Rows": [{"queryRef": "priority_scores.complaint_type", "active": True}],
                  "Columns": [{"queryRef": "priority_scores.borough"}],
                  "Values": [{"queryRef": "priority_scores.Dynamic Priority Score"}]},
                 [src("priority_scores", "p")],
                 [select_col("priority_scores", "p", "complaint_type"),
                  select_col("priority_scores", "p", "borough"),
                  select_meas("priority_scores", "p", "Dynamic Priority Score")],
                 vc_objects=title_obj("Priority score matrix (complaint type × borough)")))
p4.append(table_vis("priority_scores",
                    [("col", "priority_scores", "complaint_type"),
                     ("col", "priority_scores", "borough"),
                     ("col", "priority_scores", "agency"),
                     ("meas", "priority_scores", "Dynamic Priority Score"),
                     ("meas", "priority_scores", "Dynamic Priority Rank")],
                    592, 84, 672, 300, 11, "Hotspots ranked (drag sliders to re-rank)",
                    extra={"order_by": [{"Direction": 1, "Expression":
                                         meas_expr("t0", "Dynamic Priority Rank")}]}))
for i, wt in enumerate(["W Volume", "W Backlog", "W Miss", "W Aged"]):
    p4.append(slicer(wt, wt, 592 + i * 170, 400, 160, 90, 20 + i,
                     mode="Between", title=f"{wt} weight"))
p4.append(textbox(16, 520, 1248, 164, 30, [
    [("Recommended next actions", {"fontSize": "12pt", "fontWeight": "bold", "color": DARK})],
    [("1. DPR parks/tree aging review — close-or-escalate items older than 90 days.   "
      "2. TLC case-throughput review; validate the 30-day assumed SLA against case policy.   "
      "3. Resolve the helicopter-noise recording artifact with EDC before treating it as the #1 problem.   "
      "4. Clear aged HEAT/HOT WATER residue before the October heat season.   "
      "5. Track 'Unspecified borough' share monthly (data hygiene).",
      {"fontSize": "11pt", "color": "#41505B"})]], background="#FDF6EC"))

report = {
    "config": json.dumps({"version": "5.43", "themeCollection": {}}),
    "layoutOptimization": 0,
    "sections": [
        {"name": "page1", "displayName": "Executive Operations Overview",
         "displayOption": 1, "width": 1280, "height": 720, "config": "{}",
         "visualContainers": p1, "ordinal": 0},
        {"name": "page2", "displayName": "Demand & Complaint Patterns",
         "displayOption": 1, "width": 1280, "height": 720, "config": "{}",
         "visualContainers": p2, "ordinal": 1},
        {"name": "page3", "displayName": "SLA & Backlog Diagnostics",
         "displayOption": 1, "width": 1280, "height": 720, "config": "{}",
         "visualContainers": p3, "ordinal": 2},
        {"name": "page4", "displayName": "Priority & Action View",
         "displayOption": 1, "width": 1280, "height": 720, "config": "{}",
         "visualContainers": p4, "ordinal": 3},
    ],
}

if __name__ == "__main__":
    bm.write_project(report)
    print("report.json: 4 pages,",
          sum(len(s["visualContainers"]) for s in report["sections"]), "visuals")
