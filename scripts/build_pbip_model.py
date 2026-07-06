"""Generate the Power BI project (PBIP) semantic model for the control tower.

Emits power-bi/public_service_ops_control_tower.pbip plus the
.SemanticModel (model.bim, TMSL) and .Report folders. Open the .pbip in
Power BI Desktop, refresh, and save as .pbix.

The model mirrors power-bi/data_model.md and dax_measures.md exactly:
tables load from data/powerbi via a DataFolder parameter, one relationship
(fact -> dim_date), all documented measures, and four what-if parameters.
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PBI_DIR = ROOT / "power-bi"
NAME = "public_service_ops_control_tower"
DATA_FOLDER = str((ROOT / "data" / "powerbi").resolve())


def m_csv(filename, types):
    """M expression for a typed CSV load."""
    tlist = ", ".join(f'{{"{c}", {t}}}' for c, t in types)
    return [
        "let",
        f'    Source = Csv.Document(File.Contents(DataFolder & "\\{filename}"),'
        "[Delimiter=\",\", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),",
        "    Promoted = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),",
        f"    Typed = Table.TransformColumnTypes(Promoted, {{{tlist}}})",
        "in",
        "    Typed",
    ]


def col(name, dtype, fmt=None, summarize_none=True, hidden=False, extended=None):
    c = {"name": name, "dataType": dtype, "sourceColumn": name}
    if fmt:
        c["formatString"] = fmt
    if summarize_none:
        c["summarizeBy"] = "none"
    if hidden:
        c["isHidden"] = True
    if extended:
        c["extendedProperties"] = extended
    return c


def measure(name, expression, fmt=None, folder=None):
    m = {"name": name, "expression": expression}
    if fmt:
        m["formatString"] = fmt
    if folder:
        m["displayFolder"] = folder
    return m


PCT, NUM, F1, F3 = "0.0%", "#,0", "0.0", "0.000"

# ---------------------------------------------------------------------------
# fact table
# ---------------------------------------------------------------------------
fact_m = [
    "let",
    '    Source = Parquet.Document(File.Contents(DataFolder & "\\fact_service_requests.parquet")),',
    '    WithDateOnly = Table.AddColumn(Source, "created_date_only", each Date.From([created_date]), type date)',
    "in",
    "    WithDateOnly",
]
fact_cols = [
    col("unique_key", "string"),
    col("created_date", "dateTime"),
    col("closed_date", "dateTime"),
    col("agency", "string"),
    col("agency_name", "string"),
    col("complaint_type", "string"),
    col("descriptor", "string"),
    col("location_type", "string"),
    col("incident_zip", "string"),
    col("borough", "string"),
    col("status", "string"),
    col("open_data_channel_type", "string"),
    col("slice", "string"),
    col("is_closed", "boolean"),
    col("closure_days", "double", fmt=F1),
    col("age_days", "double", fmt=NUM),
    col("sla_days", "int64", fmt=NUM),
    col("sla_status", "string"),
    col("aging_bucket", "string"),
    col("created_week", "dateTime", fmt="yyyy-mm-dd"),
    col("created_month", "dateTime", fmt="mmm yyyy"),
    col("created_date_only", "dateTime", fmt="yyyy-mm-dd"),
]
fact_measures = [
    measure("Total Requests", "COUNTROWS ( fact_service_requests )", NUM),
    measure("Closed Requests",
            "CALCULATE ( [Total Requests], fact_service_requests[is_closed] = TRUE () )", NUM),
    measure("Open Requests",
            "CALCULATE ( [Total Requests], fact_service_requests[is_closed] = FALSE () )", NUM),
    measure("Closure Rate", "DIVIDE ( [Closed Requests], [Total Requests] )", PCT),
    measure("Backlog Count", "[Open Requests]", NUM),
    measure("Average Closure Days", "AVERAGE ( fact_service_requests[closure_days] )", F1),
    measure("Median Closure Days", "MEDIAN ( fact_service_requests[closure_days] )", F1),
    measure("SLA Missed",
            'CALCULATE ( [Total Requests], fact_service_requests[sla_status] IN { "Missed", "Open Past SLA" } )', NUM),
    measure("SLA Outcomes Known",
            'CALCULATE ( [Total Requests], fact_service_requests[sla_status] <> "Open Within SLA" )', NUM),
    measure("SLA Miss Rate", "DIVIDE ( [SLA Missed], [SLA Outcomes Known] )", PCT),
    measure("Aging Backlog Count",
            'CALCULATE ( [Open Requests], fact_service_requests[aging_bucket] IN { "31-90 days", "91-180 days", "180+ days" } )', NUM),
    measure("Aged Share of Backlog", "DIVIDE ( [Aging Backlog Count], [Open Requests] )", PCT),
    measure("Share of Total Requests",
            "DIVIDE ( [Total Requests], CALCULATE ( [Total Requests], ALLSELECTED ( fact_service_requests ) ) )", PCT),
    measure("Requests Previous Month",
            "CALCULATE ( [Total Requests], PREVIOUSMONTH ( dim_date[date] ) )", NUM),
    measure("MoM Request Change %",
            "DIVIDE ( [Total Requests] - [Requests Previous Month], [Requests Previous Month] )", PCT),
]

# ---------------------------------------------------------------------------
# dimension / aggregate tables
# ---------------------------------------------------------------------------
dim_date_cols = [
    col("date", "dateTime", fmt="yyyy-mm-dd"),
    col("week_start", "dateTime", fmt="yyyy-mm-dd"),
    col("month_start", "dateTime", fmt="mmm yyyy"),
    col("weekday", "string"),
]
dim_sla_cols = [
    col("complaint_type", "string"),
    col("sla_days", "int64", fmt=NUM),
    col("rationale", "string"),
]
prio_cols = [
    col("complaint_type", "string"),
    col("borough", "string"),
    col("agency", "string"),
    col("total_requests", "int64", fmt=NUM),
    col("open_requests", "int64", fmt=NUM),
    col("sla_miss_rate", "double", fmt=PCT),
    col("aged_share_of_open", "double", fmt=PCT),
    col("volume_percentile", "double", fmt=PCT),
    col("backlog_percentile", "double", fmt=PCT),
    col("priority_score", "double", fmt=F3),
    col("priority_rank", "int64", fmt="0"),
]
prio_measures = [
    measure("Priority Score (Static)", "MAX ( priority_scores[priority_score] )", F3),
    measure("Dynamic Priority Score", "\n".join([
        "VAR w_vol  = [W Volume Value]",
        "VAR w_back = [W Backlog Value]",
        "VAR w_miss = [W Miss Value]",
        "VAR w_aged = [W Aged Value]",
        "VAR wsum   = w_vol + w_back + w_miss + w_aged",
        "RETURN",
        "    DIVIDE (",
        "          w_vol  * AVERAGE ( priority_scores[volume_percentile] )",
        "        + w_back * AVERAGE ( priority_scores[backlog_percentile] )",
        "        + w_miss * AVERAGE ( priority_scores[sla_miss_rate] )",
        "        + w_aged * AVERAGE ( priority_scores[aged_share_of_open] ),",
        "        wsum",
        "    )"]), F3),
    measure("Dynamic Priority Rank",
            "RANKX ( ALLSELECTED ( priority_scores ), [Dynamic Priority Score], , DESC, DENSE )", "0"),
]

kpi_weekly_cols = [
    col("created_week", "dateTime", fmt="yyyy-mm-dd"),
    col("requests_created", "int64", fmt=NUM),
    col("eventually_closed", "int64", fmt=NUM),
    col("still_open", "int64", fmt=NUM),
    col("avg_closure_days", "double", fmt=F1),
    col("sla_miss_rate", "double", fmt=PCT),
]
backlog_aging_cols = [
    col("aging_bucket", "string"),
    col("borough", "string"),
    col("open_requests", "int64", fmt=NUM),
    col("avg_age_days", "double", fmt=NUM),
]


def whatif_table(name, default):
    """A what-if parameter table + value measure, as Desktop would create."""
    return {
        "name": name,
        "columns": [{
            "name": name,
            "dataType": "double",
            "sourceColumn": f"[{name}]",
            "type": "calculatedTableColumn",
            "summarizeBy": "none",
            "extendedProperties": [{
                "name": "ParameterMetadata",
                "type": "json",
                "value": json.dumps({"version": 3, "kind": 2}),
            }],
        }],
        "partitions": [{
            "name": name,
            "mode": "import",
            "source": {
                "type": "calculated",
                "expression": f"SELECTCOLUMNS ( GENERATESERIES ( 0, 1, 0.05 ), \"{name}\", [Value] )",
            },
        }],
        "measures": [measure(f"{name} Value",
                             f"SELECTEDVALUE ( '{name}'[{name}], {default} )", "0.00")],
    }


def table(name, m_lines, columns, measures=None):
    return {
        "name": name,
        "columns": columns,
        "partitions": [{
            "name": name,
            "mode": "import",
            "source": {"type": "m", "expression": m_lines},
        }],
        **({"measures": measures} if measures else {}),
    }


model = {
    "name": "SemanticModel",
    "compatibilityLevel": 1567,
    "model": {
        "culture": "en-US",
        "defaultPowerBIDataSourceVersion": "powerBI_V3",
        "sourceQueryCulture": "en-US",
        "expressions": [{
            "name": "DataFolder",
            "kind": "m",
            "expression": [
                f'"{DATA_FOLDER}" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]'
            ],
            "annotations": [{"name": "PBI_ResultType", "value": "Text"}],
        }],
        "tables": [
            table("fact_service_requests", fact_m, fact_cols, fact_measures),
            table("dim_date", m_csv("dim_date.csv", [
                ("date", "type date"), ("week_start", "type date"),
                ("month_start", "type date"), ("weekday", "type text")]),
                dim_date_cols),
            table("dim_sla_targets", m_csv("dim_sla_targets.csv", [
                ("complaint_type", "type text"), ("sla_days", "Int64.Type"),
                ("rationale", "type text")]), dim_sla_cols),
            table("priority_scores", m_csv("priority_scores.csv", [
                ("complaint_type", "type text"), ("borough", "type text"),
                ("agency", "type text"), ("total_requests", "Int64.Type"),
                ("open_requests", "Int64.Type"), ("sla_miss_rate", "type number"),
                ("aged_share_of_open", "type number"),
                ("volume_percentile", "type number"),
                ("backlog_percentile", "type number"),
                ("priority_score", "type number"),
                ("priority_rank", "Int64.Type")]), prio_cols, prio_measures),
            table("kpi_weekly", m_csv("kpi_weekly.csv", [
                ("created_week", "type date"), ("requests_created", "Int64.Type"),
                ("eventually_closed", "Int64.Type"), ("still_open", "Int64.Type"),
                ("avg_closure_days", "type number"),
                ("sla_miss_rate", "type number")]), kpi_weekly_cols),
            table("backlog_aging", m_csv("backlog_aging.csv", [
                ("aging_bucket", "type text"), ("borough", "type text"),
                ("open_requests", "Int64.Type"),
                ("avg_age_days", "type number")]), backlog_aging_cols),
            whatif_table("W Volume", 0.30),
            whatif_table("W Backlog", 0.25),
            whatif_table("W Miss", 0.25),
            whatif_table("W Aged", 0.20),
        ],
        "relationships": [{
            "name": "fact_to_date",
            "fromTable": "fact_service_requests",
            "fromColumn": "created_date_only",
            "toTable": "dim_date",
            "toColumn": "date",
        }],
        "annotations": [
            {"name": "PBI_QueryOrder",
             "value": json.dumps(["DataFolder", "fact_service_requests", "dim_date",
                                  "dim_sla_targets", "priority_scores", "kpi_weekly",
                                  "backlog_aging"])},
            {"name": "__PBI_TimeIntelligenceEnabled", "value": "0"},
        ],
    },
}


def write_project(report_json):
    sm = PBI_DIR / f"{NAME}.SemanticModel"
    rp = PBI_DIR / f"{NAME}.Report"
    sm.mkdir(parents=True, exist_ok=True)
    rp.mkdir(parents=True, exist_ok=True)

    (PBI_DIR / f"{NAME}.pbip").write_text(json.dumps({
        "version": "1.0",
        "artifacts": [{"report": {"path": f"{NAME}.Report"}}],
        "settings": {"enableAutoRecovery": True},
    }, indent=2))

    (sm / "definition.pbism").write_text(json.dumps({"version": "1.0", "settings": {}}, indent=2))
    (sm / "model.bim").write_text(json.dumps(model, indent=2))
    (sm / ".platform").write_text(json.dumps({
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json",
        "metadata": {"type": "SemanticModel", "displayName": NAME},
        "config": {"version": "2.0", "logicalId": "11111111-1111-1111-1111-111111111111"},
    }, indent=2))

    (rp / "definition.pbir").write_text(json.dumps({
        "version": "1.0",
        "datasetReference": {"byPath": {"path": f"../{NAME}.SemanticModel"}},
    }, indent=2))
    (rp / "report.json").write_text(json.dumps(report_json, indent=2))
    (rp / ".platform").write_text(json.dumps({
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json",
        "metadata": {"type": "Report", "displayName": NAME},
        "config": {"version": "2.0", "logicalId": "22222222-2222-2222-2222-222222222222"},
    }, indent=2))
    print(f"PBIP written to {PBI_DIR}")


if __name__ == "__main__":
    # skeleton report: one empty page (visuals added by build_pbip_report.py)
    skeleton = {
        "config": json.dumps({"version": "5.43", "themeCollection": {}}),
        "layoutOptimization": 0,
        "sections": [{
            "name": "page1",
            "displayName": "Executive Operations Overview",
            "displayOption": 1,
            "width": 1280,
            "height": 720,
            "config": "{}",
            "visualContainers": [],
        }],
    }
    write_project(skeleton)
