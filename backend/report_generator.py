"""
Harris Farm Hub — Report Generator
Converts analysis result dicts into multiple export formats:
Markdown, HTML, CSV, JSON.
"""

from datetime import datetime


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

def _format_currency(value):
    """Format a number as AUD currency."""
    if value is None:
        return "$0"
    if abs(value) >= 1_000_000:
        return "${:,.0f}".format(value)
    if abs(value) >= 1_000:
        return "${:,.0f}".format(value)
    return "${:.2f}".format(value)


def _format_evidence_table_md(table):
    """Convert an evidence table dict to markdown."""
    cols = table.get("columns", [])
    rows = table.get("rows", [])
    if not cols:
        return ""

    lines = []
    lines.append("| " + " | ".join(str(c) for c in cols) + " |")
    lines.append("| " + " | ".join("---" for _ in cols) + " |")
    for row in rows:
        cells = [str(c) if c is not None else "" for c in row]
        # Pad or truncate to match columns
        while len(cells) < len(cols):
            cells.append("")
        lines.append("| " + " | ".join(cells[:len(cols)]) + " |")

    return "\n".join(lines)


def _format_evidence_table_html(table):
    """Convert an evidence table dict to an HTML <table>."""
    cols = table.get("columns", [])
    rows = table.get("rows", [])
    if not cols:
        return ""

    parts = ['<table class="evidence-table">']
    parts.append("<thead><tr>")
    for c in cols:
        parts.append("<th>{}</th>".format(_html_escape(str(c))))
    parts.append("</tr></thead>")
    parts.append("<tbody>")
    for row in rows:
        parts.append("<tr>")
        cells = [str(c) if c is not None else "" for c in row]
        while len(cells) < len(cols):
            cells.append("")
        for cell in cells[:len(cols)]:
            parts.append("<td>{}</td>".format(_html_escape(cell)))
        parts.append("</tr>")
    parts.append("</tbody></table>")
    return "\n".join(parts)


def _html_escape(text):
    """Basic HTML escaping."""
    return (str(text)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;"))


def _format_recommendations_md(recs):
    """Format recommendations list as markdown table."""
    if not recs:
        return "_No recommendations._"

    lines = []
    lines.append("| # | Action | Owner | Timeline | Priority |")
    lines.append("| --- | --- | --- | --- | --- |")
    for i, r in enumerate(recs, 1):
        lines.append("| {} | {} | {} | {} | {} |".format(
            i,
            r.get("action", ""),
            r.get("owner", ""),
            r.get("timeline", ""),
            r.get("priority", "").upper(),
        ))
    return "\n".join(lines)


def _format_recommendations_html(recs):
    """Format recommendations list as HTML table."""
    if not recs:
        return "<p><em>No recommendations.</em></p>"

    parts = ['<table class="recommendations-table">']
    parts.append("<thead><tr><th>#</th><th>Action</th><th>Owner</th>"
                 "<th>Timeline</th><th>Priority</th></tr></thead>")
    parts.append("<tbody>")
    for i, r in enumerate(recs, 1):
        priority = r.get("priority", "").upper()
        color = {"HIGH": "#e74c3c", "MEDIUM": "#f39c12", "LOW": "#27ae60"}.get(
            priority, "#666")
        parts.append(
            '<tr><td>{}</td><td>{}</td><td>{}</td><td>{}</td>'
            '<td style="color:{}; font-weight:bold">{}</td></tr>'.format(
                i,
                _html_escape(r.get("action", "")),
                _html_escape(r.get("owner", "")),
                _html_escape(r.get("timeline", "")),
                color, priority,
            ))
    parts.append("</tbody></table>")
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# MARKDOWN REPORT
# ---------------------------------------------------------------------------

def generate_markdown_report(result):
    """Generate a complete markdown report from an analysis result dict."""
    sections = []

    # Title
    title = result.get("title", "Analysis Report")
    sections.append("# {}".format(title))
    sections.append("")

    # Metadata line
    generated = result.get("generated_at", "")
    analysis_type = result.get("analysis_type", "")
    confidence = result.get("confidence_level", 0)
    sections.append("_Generated: {} | Type: {} | Confidence: {:.0%}_".format(
        generated[:19] if generated else "N/A",
        analysis_type.replace("_", " ").title(),
        confidence,
    ))
    sections.append("")

    # Executive Summary
    sections.append("## Executive Summary")
    sections.append("")
    sections.append(result.get("executive_summary", "No summary available."))
    sections.append("")

    # Evidence Tables
    evidence_tables = result.get("evidence_tables", [])
    if evidence_tables:
        sections.append("## Evidence")
        sections.append("")
        for table in evidence_tables:
            name = table.get("name", "Data")
            sections.append("### {}".format(name))
            sections.append("")
            sections.append(_format_evidence_table_md(table))
            sections.append("")

    # Financial Impact
    impact = result.get("financial_impact", {})
    if impact:
        sections.append("## Financial Impact")
        sections.append("")
        annual = impact.get("estimated_annual_value", 0)
        conf = impact.get("confidence", "unknown")
        basis = impact.get("basis", "")
        sections.append("- **Estimated Annual Value:** {}".format(
            _format_currency(annual)))
        sections.append("- **Confidence:** {}".format(conf.title()))
        if basis:
            sections.append("- **Basis:** {}".format(basis))
        sections.append("")

    # Recommendations
    recs = result.get("recommendations", [])
    if recs:
        sections.append("## Recommendations")
        sections.append("")
        sections.append(_format_recommendations_md(recs))
        sections.append("")

    # Methodology
    method = result.get("methodology", {})
    if method:
        sections.append("## Methodology")
        sections.append("")
        if method.get("data_source"):
            sections.append("- **Data Source:** {}".format(
                method["data_source"]))
        if method.get("query_window"):
            sections.append("- **Query Window:** {}".format(
                method["query_window"]))
        if method.get("records_analyzed") is not None:
            sections.append("- **Records Analyzed:** {:,}".format(
                method["records_analyzed"]))
        if method.get("sql_used"):
            sections.append("- **SQL Approach:** {}".format(
                method["sql_used"]))

        limitations = method.get("limitations", [])
        if limitations:
            sections.append("")
            sections.append("### Limitations")
            sections.append("")
            for lim in limitations:
                sections.append("- {}".format(lim))

    sections.append("")
    sections.append("---")
    sections.append("_Harris Farm Hub | AI Centre of Excellence_")

    return "\n".join(sections)


# ---------------------------------------------------------------------------
# HTML REPORT
# ---------------------------------------------------------------------------

_HTML_STYLE = """
<style>
    body {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        max-width: 900px;
        margin: 40px auto;
        padding: 0 20px;
        color: #333;
        line-height: 1.6;
    }
    .header {
        border-bottom: 3px solid #2e7d32;
        padding-bottom: 15px;
        margin-bottom: 25px;
    }
    .header h1 {
        color: #2e7d32;
        margin-bottom: 5px;
    }
    .meta {
        color: #666;
        font-size: 0.9em;
    }
    .summary-box {
        background: #f1f8e9;
        border-left: 4px solid #2e7d32;
        padding: 15px 20px;
        margin: 20px 0;
        border-radius: 0 4px 4px 0;
    }
    .impact-box {
        background: #fff3e0;
        border-left: 4px solid #f57c00;
        padding: 15px 20px;
        margin: 20px 0;
        border-radius: 0 4px 4px 0;
    }
    .impact-value {
        font-size: 1.4em;
        font-weight: bold;
        color: #e65100;
    }
    h2 {
        color: #2e7d32;
        border-bottom: 1px solid #ddd;
        padding-bottom: 5px;
    }
    h3 { color: #555; }
    table.evidence-table, table.recommendations-table {
        width: 100%;
        border-collapse: collapse;
        margin: 15px 0;
        font-size: 0.9em;
    }
    table.evidence-table th, table.recommendations-table th {
        background: #2e7d32;
        color: white;
        padding: 8px 10px;
        text-align: left;
    }
    table.evidence-table td, table.recommendations-table td {
        padding: 6px 10px;
        border-bottom: 1px solid #eee;
    }
    table.evidence-table tr:nth-child(even),
    table.recommendations-table tr:nth-child(even) {
        background: #f9f9f9;
    }
    .methodology {
        background: #f5f5f5;
        padding: 15px;
        border-radius: 4px;
        margin: 20px 0;
        font-size: 0.9em;
    }
    .limitations { color: #666; font-size: 0.85em; }
    .footer {
        border-top: 1px solid #ddd;
        margin-top: 30px;
        padding-top: 10px;
        color: #999;
        font-size: 0.85em;
        text-align: center;
    }
</style>
"""


def generate_html_report(result):
    """Generate a standalone HTML report with Harris Farm branding."""
    title = _html_escape(result.get("title", "Analysis Report"))
    generated = result.get("generated_at", "")[:19]
    analysis_type = result.get("analysis_type", "").replace("_", " ").title()
    confidence = result.get("confidence_level", 0)

    parts = []
    parts.append("<!DOCTYPE html>")
    parts.append("<html lang='en'>")
    parts.append("<head>")
    parts.append("<meta charset='UTF-8'>")
    parts.append("<meta name='viewport' content='width=device-width, initial-scale=1.0'>")
    parts.append("<title>{}</title>".format(title))
    parts.append(_HTML_STYLE)
    parts.append("</head>")
    parts.append("<body>")

    # Header
    parts.append('<div class="header">')
    parts.append("<h1>{}</h1>".format(title))
    parts.append('<p class="meta">Generated: {} | Type: {} | '
                 'Confidence: {:.0%}</p>'.format(generated, analysis_type, confidence))
    parts.append("</div>")

    # Executive Summary
    parts.append("<h2>Executive Summary</h2>")
    parts.append('<div class="summary-box">')
    parts.append("<p>{}</p>".format(
        _html_escape(result.get("executive_summary", "No summary available."))))
    parts.append("</div>")

    # Evidence Tables
    evidence_tables = result.get("evidence_tables", [])
    if evidence_tables:
        parts.append("<h2>Evidence</h2>")
        for table in evidence_tables:
            name = table.get("name", "Data")
            parts.append("<h3>{}</h3>".format(_html_escape(name)))
            parts.append(_format_evidence_table_html(table))

    # Financial Impact
    impact = result.get("financial_impact", {})
    if impact:
        annual = impact.get("estimated_annual_value", 0)
        parts.append("<h2>Financial Impact</h2>")
        parts.append('<div class="impact-box">')
        parts.append('<p class="impact-value">Estimated Annual Value: '
                     '{}</p>'.format(_format_currency(annual)))
        parts.append("<p><strong>Confidence:</strong> {} | "
                     "<strong>Basis:</strong> {}</p>".format(
                         impact.get("confidence", "unknown").title(),
                         _html_escape(impact.get("basis", "")),
                     ))
        parts.append("</div>")

    # Recommendations
    recs = result.get("recommendations", [])
    if recs:
        parts.append("<h2>Recommendations</h2>")
        parts.append(_format_recommendations_html(recs))

    # Methodology
    method = result.get("methodology", {})
    if method:
        parts.append("<h2>Methodology</h2>")
        parts.append('<div class="methodology">')
        if method.get("data_source"):
            parts.append("<p><strong>Data Source:</strong> {}</p>".format(
                _html_escape(method["data_source"])))
        if method.get("query_window"):
            parts.append("<p><strong>Query Window:</strong> {}</p>".format(
                _html_escape(method["query_window"])))
        if method.get("records_analyzed") is not None:
            parts.append("<p><strong>Records Analyzed:</strong> {:,}</p>".format(
                method["records_analyzed"]))
        if method.get("sql_used"):
            parts.append("<p><strong>SQL Approach:</strong> {}</p>".format(
                _html_escape(method["sql_used"])))

        limitations = method.get("limitations", [])
        if limitations:
            parts.append('<div class="limitations">')
            parts.append("<p><strong>Limitations:</strong></p><ul>")
            for lim in limitations:
                parts.append("<li>{}</li>".format(_html_escape(lim)))
            parts.append("</ul></div>")
        parts.append("</div>")

    # Footer
    parts.append('<div class="footer">')
    parts.append("<p>Harris Farm Hub | AI Centre of Excellence | "
                 "{}</p>".format(generated))
    parts.append("</div>")

    parts.append("</body>")
    parts.append("</html>")

    return "\n".join(parts)


# ---------------------------------------------------------------------------
# CSV EXPORT
# ---------------------------------------------------------------------------

def generate_csv_export(result):
    """Export evidence tables as CSV text."""
    import csv
    import io

    output = io.StringIO()
    writer = csv.writer(output)

    # Header info
    writer.writerow(["Report", result.get("title", "")])
    writer.writerow(["Analysis Type", result.get("analysis_type", "")])
    writer.writerow(["Generated", result.get("generated_at", "")])
    writer.writerow(["Confidence", "{:.0%}".format(
        result.get("confidence_level", 0))])
    writer.writerow([])

    # Executive Summary
    writer.writerow(["Executive Summary"])
    writer.writerow([result.get("executive_summary", "")])
    writer.writerow([])

    # Evidence tables
    for table in result.get("evidence_tables", []):
        writer.writerow(["Table: {}".format(table.get("name", "Data"))])
        cols = table.get("columns", [])
        if cols:
            writer.writerow(cols)
        for row in table.get("rows", []):
            cells = [str(c) if c is not None else "" for c in row]
            writer.writerow(cells)
        writer.writerow([])

    # Financial Impact
    impact = result.get("financial_impact", {})
    if impact:
        writer.writerow(["Financial Impact"])
        writer.writerow(["Estimated Annual Value",
                          _format_currency(impact.get("estimated_annual_value", 0))])
        writer.writerow(["Confidence", impact.get("confidence", "")])
        writer.writerow(["Basis", impact.get("basis", "")])
        writer.writerow([])

    # Recommendations
    recs = result.get("recommendations", [])
    if recs:
        writer.writerow(["Recommendations"])
        writer.writerow(["Action", "Owner", "Timeline", "Priority"])
        for r in recs:
            writer.writerow([
                r.get("action", ""),
                r.get("owner", ""),
                r.get("timeline", ""),
                r.get("priority", ""),
            ])

    return output.getvalue()


# ---------------------------------------------------------------------------
# JSON EXPORT
# ---------------------------------------------------------------------------

def generate_json_export(result):
    """Export the full result dict as formatted JSON."""
    import json
    return json.dumps(result, indent=2, default=str)
