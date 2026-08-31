# ruff: noqa: E501
"""Generate self-contained HTML reports from analysis results."""

from __future__ import annotations

import html as _html
import json
from pathlib import Path

_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Sentinel Report</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4"></script>
<style>
  :root {{ --bg: #0d1117; --fg: #c9d1d9; --card: #161b22; --border: #30363d;
          --err: #f85149; --warn: #d29922; --info: #58a6ff; --green: #3fb950; }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
         background: var(--bg); color: var(--fg); padding: 2rem; line-height: 1.5; }}
  h1 {{ font-size: 1.5rem; margin-bottom: .5rem; }}
  .meta {{ color: #8b949e; font-size: .85rem; margin-bottom: 1.5rem; }}
  .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
           gap: 1rem; margin-bottom: 2rem; }}
  .card {{ background: var(--card); border: 1px solid var(--border); border-radius: 8px;
           padding: 1rem; text-align: center; }}
  .card .num {{ font-size: 2rem; font-weight: 700; }}
  .card .label {{ font-size: .8rem; color: #8b949e; }}
  table {{ width: 100%; border-collapse: collapse; margin-bottom: 2rem; }}
  th, td {{ text-align: left; padding: .6rem .8rem; border-bottom: 1px solid var(--border); }}
  th {{ color: #8b949e; font-size: .8rem; text-transform: uppercase; }}
  .sev-error {{ color: var(--err); }}
  .sev-warning {{ color: var(--warn); }}
  .sev-info {{ color: var(--info); }}
  .chart-box {{ background: var(--card); border: 1px solid var(--border); border-radius: 8px;
                padding: 1rem; margin-bottom: 2rem; max-width: 700px; }}
  canvas {{ max-height: 300px; }}
</style>
</head>
<body>
<h1>Sentinel — Architecture Report</h1>
<p class="meta">{meta}</p>

<div class="grid">
  <div class="card"><div class="num">{total}</div><div class="label">Total Violations</div></div>
  <div class="card"><div class="num" style="color:var(--err)">{errors}</div><div class="label">Errors</div></div>
  <div class="card"><div class="num" style="color:var(--warn)">{warnings}</div><div class="label">Warnings</div></div>
  <div class="card"><div class="num" style="color:var(--info)">{infos}</div><div class="label">Info</div></div>
</div>

<h2 style="margin-bottom:.5rem">Violations</h2>
<table>
  <thead><tr><th>Rule</th><th>Severity</th><th>Evidence</th><th>Impact</th><th>Recommendation</th></tr></thead>
  <tbody>{violations_rows}</tbody>
</table>

<div class="chart-box"><canvas id="trendChart"></canvas></div>

<script>
const trendData = {trend_json};
const ctx = document.getElementById('trendChart').getContext('2d');
const labels = trendData.map(d => d.commit.substring(0, 8));
const datasets = [];
const kinds = [...new Set(trendData.flatMap(d => Object.keys(d.counts)))];
const palette = ['#f85149','#d29922','#58a6ff','#3fb950'];
kinds.forEach((k, i) => {{
  datasets.push({{
    label: k,
    data: trendData.map(d => d.counts[k] || 0),
    borderColor: palette[i % palette.length],
    backgroundColor: palette[i % palette.length] + '33',
    fill: true,
    tension: 0.3
  }});
}});
new Chart(ctx, {{
  type: 'line',
  data: {{ labels, datasets }},
  options: {{
    responsive: true,
    plugins: {{ title: {{ display: true, text: 'Violations Over Time', color: '#c9d1d9' }},
               legend: {{ labels: {{ color: '#c9d1d9' }} }} }},
    scales: {{
      x: {{ ticks: {{ color: '#8b949e' }}, grid: {{ color: '#30363d' }} }},
      y: {{ ticks: {{ color: '#8b949e', stepSize: 1 }}, grid: {{ color: '#30363d' }}, beginAtZero: true }}
    }}
  }}
}});
</script>
</body>
</html>
"""


def render_report(
    *,
    violations: list,
    trend_data: list[dict] | None = None,
    meta: str = "",
) -> str:
    """Return a self-contained HTML report string."""
    errors = sum(1 for v in violations if v.severity.value == "error")
    warnings = sum(1 for v in violations if v.severity.value == "warning")
    infos = sum(1 for v in violations if v.severity.value == "info")
    total = len(violations)

    rows = []
    for v in violations:
        sev_cls = f"sev-{v.severity.value}"
        rows.append(
            f"<tr><td>{_html.escape(v.rule)}</td>"
            f"<td class=\"{sev_cls}\">{_html.escape(v.severity.value)}</td>"
            f"<td>{_html.escape(v.evidence)}</td>"
            f"<td>{_html.escape(v.impact)}</td>"
            f"<td>{_html.escape(v.recommendation)}</td></tr>"
        )

    trend_json = json.dumps(trend_data or []).replace("</", "<\\/")
    return _TEMPLATE.format(
        meta=_html.escape(meta),
        total=total,
        errors=errors,
        warnings=warnings,
        infos=infos,
        violations_rows="\n".join(rows),
        trend_json=trend_json,
    )


def write_report(
    output: Path,
    *,
    violations: list,
    trend_data: list[dict] | None = None,
    meta: str = "",
) -> None:
    """Write an HTML report to `output`."""
    html = render_report(
        violations=violations, trend_data=trend_data, meta=meta
    )
    output.write_text(html, encoding="utf-8")
