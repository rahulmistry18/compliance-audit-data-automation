# BI exports (Tableau Public / Power BI)

This folder has two ready-to-import files, generated from the same audit run as the rest of the repo by `python build_bi_exports.py`:

- `audit_results.csv` - one row per check, plain column names, no cleanup needed.
- `compliance_audit_workbook.xlsx` - the same data plus three extra tabs: a Rule Summary sheet with live formulas (COUNTIFS), a Data Dictionary, and a Data Source disclosure sheet.

Neither Tableau Public nor Power BI accept an arbitrary uploaded dashboard file from outside their own apps - both require you to open the data in the actual Tableau Desktop (Public) or Power BI Desktop application and build/publish from there. That's the normal workflow for both platforms, not a limitation of this project. The steps below take about five minutes.

## Tableau Public

1. Install Tableau Public Desktop (free) from Tableau's website.
2. Open it, choose Connect, then Text File (for the CSV) or Microsoft Excel (for the .xlsx).
3. Select `audit_results.csv` or `compliance_audit_workbook.xlsx`.
4. On a new worksheet, drag `Applies To` to Columns and `Result` to Rows, then choose a bar chart - that recreates the "Findings by domain" chart from the HTML dashboard.
5. Make a second worksheet: drag `Result` to Color and use a pie chart for the pass/fail split.
6. Make a third worksheet as a simple table of the `Needs Review` = "Yes" rows.
7. Create a new Dashboard, drag all three worksheets onto it.
8. File, then Save to Tableau Public. Sign in (or create a free account) and it publishes to a public URL you can link from your portfolio.

## Power BI Desktop

1. Install Power BI Desktop (free) from Microsoft's website.
2. Home, then Get Data, then choose Text/CSV or Excel workbook.
3. Select `audit_results.csv` or `compliance_audit_workbook.xlsx`, then Load.
4. Add a Card visual for total checks, a Stacked Column Chart (`Applies To` on axis, `Result` as legend), and a Donut Chart for the pass/fail split.
5. Add a Table visual filtered to `Needs Review` = "Yes" for the escalation list.
6. File, then Publish, then Publish to Power BI (requires a free Power BI account). This publishes to a workspace in the Power BI service.
7. To get a public link, open the report in the Power BI service, then File, then Publish to web - this generates a public embeddable/shareable URL, similar to Tableau Public.

## A note on the data

Every figure in these files traces back to the same synthetic sample data and rule engine as the rest of this repo - see the Data Source tab in `docs/index.html`, or the Data Source sheet in the .xlsx, for exactly what's real (the regulatory rules) and what's fabricated (the individual trade and contract records).
