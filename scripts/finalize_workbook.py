"""Finalize the workbook with real Excel (COM): native PivotTables and
PivotCharts on the Pivot_Analysis tab, a full recalculation, and a scan
proving zero formula errors. Requires desktop Excel on Windows.
"""

import sys
from pathlib import Path

import win32com.client as win32

ROOT = Path(__file__).resolve().parents[1]
XLSX = ROOT / "excel" / "public_service_ops_control_tower.xlsx"

XL_DATABASE = 1
XL_ROW, XL_COL, XL_DATA = 1, 2, 4
XL_COUNT, XL_AVERAGE = -4112, -4106
XL_PCT_OF_TOTAL = 8
XL_DESC = 2
XL_COLUMN_CLUSTERED = 51
XL_LINE_MARKERS = 65
XL_FORMULAS = -4123
XL_ERRORS = 16


def add_pivot(wb, ws, cache, dest, name, row_field, title,
              avg_closure=False, pct=True, number_fmt="#,##0",
              row_fmt=None, top15=False):
    title_cell = ws.Range(dest)
    title_cell.Value = title
    title_cell.Font.Bold = True
    title_cell.Font.Size = 12
    pt_dest = ws.Range(dest).Offset(2, 1)  # COM Offset is 1-based: same col, next row
    pt = cache.CreatePivotTable(TableDestination=pt_dest, TableName=name)
    pf = pt.PivotFields(row_field)
    pf.Orientation = XL_ROW
    df1 = pt.AddDataField(pt.PivotFields("Unique Key"), "Requests", XL_COUNT)
    df1.NumberFormat = number_fmt
    if pct:
        df2 = pt.AddDataField(pt.PivotFields("Unique Key"), "% of Total", XL_COUNT)
        df2.Calculation = XL_PCT_OF_TOTAL
        df2.NumberFormat = "0.0%"
    if avg_closure:
        df3 = pt.AddDataField(pt.PivotFields("Closure Days"),
                              "Avg Closure Days", XL_AVERAGE)
        df3.NumberFormat = "0.0"
    pf.AutoSort(XL_DESC, "Requests")
    if row_fmt:
        try:
            pf.NumberFormat = row_fmt
        except Exception:
            pass
    if top15:
        try:
            pf.PivotFilters.Add2(1, df1, 15)        # xlTopCount on Requests
        except Exception as e:
            print(f"  note: top-15 filter unavailable for {name}: {e}")
    pt.TableStyle2 = "PivotStyleLight15"
    pt.ColumnGrand = True
    pt.RowGrand = True
    return pt


def add_pivot_chart(ws, pt, chart_type, left_cell, title, w=420, h=240):
    anchor = ws.Range(left_cell)
    shape = ws.Shapes.AddChart2(201, chart_type, anchor.Left, anchor.Top, w, h)
    shape.Chart.SetSourceData(pt.TableRange1)
    shape.Chart.HasTitle = True
    shape.Chart.ChartTitle.Text = title
    try:
        shape.Chart.Legend.Delete()
    except Exception:
        pass
    return shape


def scan_errors(wb):
    problems = []
    for ws in wb.Worksheets:
        try:
            errs = ws.UsedRange.SpecialCells(XL_FORMULAS, XL_ERRORS)
            for cell in errs:
                problems.append(f"{ws.Name}!{cell.Address}={cell.Text}")
                if len(problems) > 20:
                    return problems
        except Exception:
            continue  # no error cells on this sheet
    return problems


def main():
    xl = win32.DispatchEx("Excel.Application")
    xl.Visible = False
    xl.DisplayAlerts = False
    try:
        wb = xl.Workbooks.Open(str(XLSX))
        ws = wb.Worksheets("Pivot_Analysis")

        # defensive: drop any pivots left over from a previous partial run
        for pt in list(ws.PivotTables()):
            pt.TableRange2.Clear()

        cache = wb.PivotCaches().Create(SourceType=XL_DATABASE,
                                        SourceData="tblClean")

        pt1 = add_pivot(wb, ws, cache, "A4", "ptAgency", "Agency",
                        "Requests by agency", avg_closure=True)
        pt2 = add_pivot(wb, ws, cache, "G4", "ptComplaint", "Complaint Type",
                        "Requests by complaint type (top 15 shown)",
                        avg_closure=True, top15=True)
        pt3 = add_pivot(wb, ws, cache, "M4", "ptBorough", "Borough",
                        "Requests by borough", avg_closure=True)
        pt4 = add_pivot(wb, ws, cache, "S4", "ptMonth", "Created Month",
                        "Requests by month created", row_fmt="mmm yyyy")
        pt5 = add_pivot(wb, ws, cache, "Y4", "ptWeek", "Created Week",
                        "Requests by week created", pct=False,
                        row_fmt="yyyy-mm-dd")
        pt6 = add_pivot(wb, ws, cache, "AE4", "ptSLA", "SLA Status",
                        "Open vs closed, through the SLA lens")

        add_pivot_chart(ws, pt3, XL_COLUMN_CLUSTERED, "A28",
                        "Requests by borough (sample)")
        add_pivot_chart(ws, pt5, XL_LINE_MARKERS, "G28",
                        "Weekly request volume (sample)")

        ws.Columns("A:Z").AutoFit()

        print("pivots created; recalculating...")
        xl.CalculateFullRebuild()
        xl.CalculateUntilAsyncQueriesDone()

        problems = scan_errors(wb)
        if problems:
            print("FORMULA ERRORS FOUND:")
            for p in problems:
                print("  " + p)
        else:
            print("zero formula errors across all sheets")

        wb.Worksheets("README").Activate()
        wb.Save()
        wb.Close(SaveChanges=False)
        return 1 if problems else 0
    finally:
        xl.Quit()


if __name__ == "__main__":
    sys.exit(main())
