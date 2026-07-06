"""Render design mockups of the four Power BI pages from the real data.

These are LAYOUT MOCKUPS (matplotlib), not Power BI screenshots — each image
is labeled as such. They exist so the dashboard can be reviewed and rebuilt
faithfully (power-bi/manual_build_instructions.md) without Power BI Desktop
installed.
"""

from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PBI = ROOT / "data" / "powerbi"
OUT = ROOT / "power-bi" / "screenshots"

DARK, TEAL, RED, AMBER, LIGHT = "#26343F", "#1F7A8C", "#D64550", "#F4A259", "#F2F6F8"

mpl.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Segoe UI", "Arial", "DejaVu Sans"],
    "figure.facecolor": "white", "axes.facecolor": "white",
    "axes.edgecolor": "#D5DBDF", "axes.grid": True, "grid.color": "#E8ECEF",
    "axes.spines.top": False, "axes.spines.right": False,
    "font.size": 9, "axes.titlesize": 11, "axes.titleweight": "bold",
    "axes.titlelocation": "left", "savefig.dpi": 130,
})

fact = pd.read_parquet(PBI / "fact_service_requests.parquet")
weekly = pd.read_csv(PBI / "kpi_weekly.csv", parse_dates=["created_week"])
by_agency = pd.read_csv(PBI / "kpi_by_agency.csv")
by_type = pd.read_csv(PBI / "kpi_by_complaint_type.csv")
by_borough = pd.read_csv(PBI / "kpi_by_borough.csv")
aging = pd.read_csv(PBI / "backlog_aging.csv")
prio = pd.read_csv(PBI / "priority_scores.csv")

TOTAL = len(fact)
OPEN = int((~fact["is_closed"]).sum())
CLOSED = TOTAL - OPEN
MISSED = int(fact["sla_status"].isin(["Missed", "Open Past SLA"]).sum())
KNOWN = int((fact["sla_status"] != "Open Within SLA").sum())
MISS_RATE = MISSED / KNOWN
AVG_CLOSE = fact["closure_days"].mean()
BUCKET_ORDER = ["0-7 days", "8-30 days", "31-90 days", "91-180 days", "180+ days"]


def new_page(title, subtitle):
    fig = plt.figure(figsize=(12.8, 7.2))
    band = fig.add_axes([0, 0.915, 1, 0.085])
    band.set_facecolor(DARK)
    band.set_xticks([]), band.set_yticks([])
    for s in band.spines.values():
        s.set_visible(False)
    band.text(0.012, 0.58, title, color="white", fontsize=15, fontweight="bold",
              va="center", transform=band.transAxes)
    band.text(0.012, 0.18, subtitle, color="#9FB3BE", fontsize=8.5,
              va="center", transform=band.transAxes)
    band.text(0.988, 0.5, "DESIGN MOCKUP — not a Power BI screenshot\nbuild via manual_build_instructions.md",
              color=AMBER, fontsize=7.5, ha="right", va="center",
              fontstyle="italic", transform=band.transAxes)
    fig.text(0.012, 0.012, "Source: NYC Open Data — 311 Service Requests (erm2-nwe9) · snapshot 2026-07-05 · "
             "SLA targets are analyst assumptions · full extract n=1,070,818",
             fontsize=7.5, color="#8896A0")
    return fig


def kpi_card(fig, x, y, w, h, value, label, color=DARK):
    ax = fig.add_axes([x, y, w, h])
    ax.set_facecolor(LIGHT)
    ax.set_xticks([]), ax.set_yticks([])
    ax.grid(False)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.text(0.5, 0.62, value, ha="center", va="center", fontsize=17,
            fontweight="bold", color=color, transform=ax.transAxes)
    ax.text(0.5, 0.2, label, ha="center", va="center", fontsize=8,
            color="#5B6B76", transform=ax.transAxes)


# ===========================================================================
# Page 1 — Executive Operations Overview
# ===========================================================================
fig = new_page("Public Service Operations — SLA Control Tower",
               "Executive Operations Overview · NYC 311 · Q2 2026 activity + aged open backlog")
cards = [(f"{TOTAL/1e6:.2f}M", "Total requests"), (f"{OPEN/1e3:,.0f}K", "Open requests"),
         (f"{CLOSED/1e6:.2f}M", "Closed requests"), (f"{OPEN/1e3:,.0f}K", "Backlog count"),
         (f"{MISS_RATE:.1%}", "SLA miss rate"), (f"{AVG_CLOSE:.1f}", "Avg closure days")]
for i, (v, l) in enumerate(cards):
    kpi_card(fig, 0.03 + i * 0.158, 0.76, 0.14, 0.12, v, l,
             color=RED if l in ("SLA miss rate", "Backlog count") else DARK)

ax = fig.add_axes([0.05, 0.36, 0.52, 0.33])
ax.plot(weekly["created_week"], weekly["requests_created"], color=TEAL, lw=2.2,
        marker="o", ms=3.5, label="Created")
ax.plot(weekly["created_week"], weekly["eventually_closed"], color="#9AA5B1",
        lw=1.8, marker="o", ms=3, label="Closed by snapshot")
ax.set_title("Weekly demand vs closure (activity window; final week is partial)")
ax.legend(frameon=False, fontsize=8)
ax.yaxis.set_major_formatter(lambda v, _: f"{v/1e3:.0f}K")

top5 = prio.nsmallest(5, "priority_rank").iloc[::-1]
ax = fig.add_axes([0.66, 0.36, 0.30, 0.33])
labels = top5["complaint_type"].str.slice(0, 22) + " · " + top5["borough"]
ax.barh(labels, top5["priority_score"], color=AMBER)
ax.set_title("Top 5 priority hotspots")
ax.set_xlim(0, 1.05)
for i, v in enumerate(top5["priority_score"]):
    ax.text(v + 0.02, i, f"{v:.2f}", va="center", fontsize=8, color=DARK)

ax = fig.add_axes([0.05, 0.07, 0.91, 0.2])
ax.set_facecolor("#FDF6EC")
ax.set_xticks([]), ax.set_yticks([])
ax.grid(False)
ax.text(0.012, 0.82, "Headline insight", fontweight="bold", fontsize=10,
        color=DARK, transform=ax.transAxes, va="top")
ax.text(0.012, 0.55,
        "Q2 demand ran ~75K requests/week and rose through the quarter (Queens +11.0% then +6.5% MoM). Enforcement-type requests close in\n"
        "hours, but a structural backlog of ~168K open requests has built up — 77% already older than 30 days, 36% older than 180 days —\n"
        "concentrated in parks/tree work (DPR), TLC complaint cases and housing conditions (HPD). All ~19K helicopter-noise requests are\n"
        "unclosed (reporting artifact): report that line separately so it doesn't distort citywide KPIs.",
        fontsize=9, color="#41505B", transform=ax.transAxes, va="top", linespacing=1.5)
fig.savefig(OUT / "page1_executive_overview.png")
plt.close(fig)

# ===========================================================================
# Page 2 — Demand & Complaint Patterns
# ===========================================================================
fig = new_page("Demand & Complaint Patterns",
               "Where service demand concentrates: time, request type, agency, borough")

daily = (fact.loc[fact["slice"] == "activity_q2_2026", "created_date"]
         .dt.floor("D").value_counts().sort_index())
ax = fig.add_axes([0.05, 0.55, 0.44, 0.30])
ax.fill_between(daily.index, daily.values, color=TEAL, alpha=0.25, lw=0)
ax.plot(daily.index, daily.values, color=TEAL, lw=1.2)
ax.set_title("Daily requests (activity window)")
ax.yaxis.set_major_formatter(lambda v, _: f"{v/1e3:.0f}K")

t15 = by_type.nlargest(15, "total_requests").iloc[::-1]
ax = fig.add_axes([0.56, 0.13, 0.40, 0.72])
ax.barh(t15["complaint_type"].str.slice(0, 28), t15["total_requests"], color=TEAL)
ax.set_title("Top 15 complaint types")
ax.xaxis.set_major_formatter(lambda v, _: f"{v/1e3:.0f}K")

a10 = by_agency.nlargest(10, "total_requests").iloc[::-1]
ax = fig.add_axes([0.05, 0.13, 0.20, 0.32])
ax.barh(a10["agency"], a10["total_requests"], color="#5FA3B4")
ax.set_title("Requests by agency (top 10)")
ax.xaxis.set_major_formatter(lambda v, _: f"{v/1e3:.0f}K")

bb = by_borough[by_borough["borough"] != "Unspecified"]
ax = fig.add_axes([0.31, 0.13, 0.18, 0.32])
ax.bar(bb["borough"].str.slice(0, 8), bb["total_requests"], color="#33879D")
ax.set_title("Requests by borough")
ax.tick_params(axis="x", labelsize=7.5, rotation=20)
ax.yaxis.set_major_formatter(lambda v, _: f"{v/1e3:.0f}K")
fig.savefig(OUT / "page2_demand_patterns.png")
plt.close(fig)

# ===========================================================================
# Page 3 — SLA & Backlog Diagnostics
# ===========================================================================
fig = new_page("SLA & Backlog Diagnostics",
               "Miss rates vs assumed targets · backlog aging pressure · the oldest unresolved work")

a12 = by_agency.nlargest(12, "total_requests").sort_values("sla_miss_rate")
ax = fig.add_axes([0.05, 0.52, 0.27, 0.33])
ax.barh(a12["agency"], a12["sla_miss_rate"], color=RED)
ax.axvline(MISS_RATE, color=DARK, lw=1.2, ls="--")
ax.set_title("SLA miss rate by agency (top 12 by volume)")
ax.xaxis.set_major_formatter(lambda v, _: f"{v:.0%}")

t_hi = (by_type[by_type["total_requests"] >= 5000]
        .nlargest(10, "sla_miss_rate").sort_values("sla_miss_rate"))
ax = fig.add_axes([0.40, 0.52, 0.27, 0.33])
ax.barh(t_hi["complaint_type"].str.slice(0, 26), t_hi["sla_miss_rate"], color=RED)
ax.set_title("Worst SLA miss — types with ≥5K requests")
ax.xaxis.set_major_formatter(lambda v, _: f"{v:.0%}")

ag = aging.groupby("aging_bucket")["open_requests"].sum().reindex(BUCKET_ORDER)
ax = fig.add_axes([0.75, 0.52, 0.21, 0.33])
ax.bar(range(5), ag.values, color=[TEAL, TEAL, AMBER, AMBER, RED])
ax.set_xticks(range(5), ["0-7", "8-30", "31-90", "91-180", "180+"], fontsize=8)
ax.set_title("Backlog aging (days, open)")
ax.yaxis.set_major_formatter(lambda v, _: f"{v/1e3:.0f}K")

cd = fact["closure_days"].dropna().clip(upper=60)
ax = fig.add_axes([0.05, 0.10, 0.27, 0.32])
ax.hist(cd, bins=30, color=TEAL)
ax.set_title("Closure-time distribution (capped at 60d)")
ax.set_xlabel("days to close", fontsize=8)
ax.yaxis.set_major_formatter(lambda v, _: f"{v/1e3:.0f}K")

oldest = (fact[~fact["is_closed"]].nlargest(8, "age_days")
          [["unique_key", "complaint_type", "borough", "agency", "age_days"]])
ax = fig.add_axes([0.40, 0.10, 0.56, 0.32])
ax.set_axis_off()
ax.set_title("High-risk backlog — oldest open requests", loc="left")
table = ax.table(
    cellText=[[str(r.unique_key), r.complaint_type[:30], r.borough, r.agency,
               f"{int(r.age_days)}d"] for r in oldest.itertuples()],
    colLabels=["Key", "Complaint type", "Borough", "Agency", "Age"],
    loc="upper left", cellLoc="left", colWidths=[0.12, 0.4, 0.16, 0.12, 0.1])
table.auto_set_font_size(False)
table.set_fontsize(8)
table.scale(1, 1.35)
for j in range(5):
    table[0, j].set_facecolor(DARK)
    table[0, j].set_text_props(color="white", fontweight="bold")
fig.savefig(OUT / "page3_sla_backlog.png")
plt.close(fig)

# ===========================================================================
# Page 4 — Priority & Action View
# ===========================================================================
fig = new_page("Priority & Action View",
               "Weighted priority score by complaint type × borough · what-if weight sliders re-rank live")

top_types = (prio.groupby("complaint_type")["priority_score"].max()
             .nlargest(10).index)
mat = (prio[prio["complaint_type"].isin(top_types)]
       .pivot_table(index="complaint_type", columns="borough",
                    values="priority_score")
       .reindex(top_types))
ax = fig.add_axes([0.145, 0.13, 0.345, 0.70])
im = ax.imshow(mat.values, cmap="YlOrRd", vmin=0, vmax=1, aspect="auto")
ax.set_xticks(range(mat.shape[1]), [c[:9] for c in mat.columns], fontsize=8)
ax.set_yticks(range(mat.shape[0]), [t[:24] for t in mat.index], fontsize=8)
ax.set_title("Priority score heatmap (base weights 30/25/25/20)")
ax.grid(False)
for i in range(mat.shape[0]):
    for j in range(mat.shape[1]):
        v = mat.values[i, j]
        if not np.isnan(v):
            ax.text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=7,
                    color="white" if v > 0.6 else DARK)

t10 = prio.nsmallest(10, "priority_rank")
ax = fig.add_axes([0.53, 0.45, 0.43, 0.38])
ax.set_axis_off()
ax.set_title("Top 10 hotspots — score components", loc="left")
table = ax.table(
    cellText=[[int(r.priority_rank), r.complaint_type[:24], r.borough[:9],
               f"{int(r.open_requests):,}", f"{r.sla_miss_rate:.0%}",
               f"{r.priority_score:.2f}"] for r in t10.itertuples()],
    colLabels=["#", "Complaint type", "Borough", "Open", "Miss", "Score"],
    loc="upper left", cellLoc="left", colWidths=[0.05, 0.38, 0.15, 0.13, 0.1, 0.11])
table.auto_set_font_size(False)
table.set_fontsize(7.5)
table.scale(1, 1.28)
for j in range(6):
    table[0, j].set_facecolor(DARK)
    table[0, j].set_text_props(color="white", fontweight="bold")

ax = fig.add_axes([0.53, 0.28, 0.43, 0.12])
ax.set_facecolor(LIGHT)
ax.set_xticks([]), ax.set_yticks([])
ax.grid(False)
ax.text(0.02, 0.72, "Priority weight scenario (what-if sliders)", fontsize=9,
        fontweight="bold", color=DARK, transform=ax.transAxes)
for i, (nm, v) in enumerate([("Volume", 0.30), ("Backlog", 0.25),
                             ("SLA miss", 0.25), ("Aged", 0.20)]):
    x = 0.04 + i * 0.24
    ax.plot([x, x + 0.16], [0.35, 0.35], color="#B9C4CC", lw=3,
            transform=ax.transAxes, solid_capstyle="round")
    ax.plot(x + 0.16 * v / 0.4, 0.35, "o", color=TEAL, ms=8, transform=ax.transAxes)
    ax.text(x, 0.1, f"{nm}: {v:.2f}", fontsize=7.5, transform=ax.transAxes)

ax = fig.add_axes([0.53, 0.10, 0.43, 0.15])
ax.set_facecolor("#FDF6EC")
ax.set_xticks([]), ax.set_yticks([])
ax.grid(False)
ax.text(0.02, 0.8, "Recommended next actions", fontsize=9, fontweight="bold",
        color=DARK, transform=ax.transAxes, va="top")
ax.text(0.02, 0.52, "1. DPR parks/tree aging review — close-or-escalate items >90d   "
                    "2. TLC case-throughput review\n3. Resolve helicopter-noise recording artifact   "
                    "4. Clear aged HEAT/HOT WATER residue before October",
        fontsize=8, color="#41505B", transform=ax.transAxes, va="top", linespacing=1.6)
fig.savefig(OUT / "page4_priority_action.png")
plt.close(fig)

print("mockups written to", OUT)
