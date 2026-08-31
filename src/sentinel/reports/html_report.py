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
  h2 {{ font-size: 1.1rem; margin: 1.5rem 0 .5rem; }}
  .meta {{ color: #8b949e; font-size: .85rem; margin-bottom: 1.5rem; }}
  .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
           gap: 1rem; margin-bottom: 2rem; }}
  .card {{ background: var(--card); border: 1px solid var(--border); border-radius: 8px;
           padding: 1rem; text-align: center; }}
  .card .num {{ font-size: 2rem; font-weight: 700; }}
  .card .label {{ font-size: .8rem; color: #8b949e; }}
  .drift-green {{ color: var(--green); }}
  .drift-yellow {{ color: var(--warn); }}
  .drift-red {{ color: var(--err); }}
  .controls {{ display: flex; gap: .75rem; flex-wrap: wrap; margin-bottom: 1rem; align-items: center; }}
  .controls select, .controls input {{ background: var(--card); color: var(--fg); border: 1px solid var(--border);
    border-radius: 6px; padding: .4rem .6rem; font-size: .85rem; }}
  .controls input {{ min-width: 220px; }}
  .controls button {{ background: var(--border); color: var(--fg); border: none; border-radius: 6px;
    padding: .4rem .8rem; font-size: .85rem; cursor: pointer; }}
  .controls button:hover {{ background: #3d444d; }}
  table {{ width: 100%; border-collapse: collapse; margin-bottom: 1rem; }}
  th, td {{ text-align: left; padding: .6rem .8rem; border-bottom: 1px solid var(--border); }}
  th {{ color: #8b949e; font-size: .8rem; text-transform: uppercase; cursor: pointer; user-select: none; }}
  th:hover {{ color: var(--fg); }}
  th .arrow {{ font-size: .7rem; margin-left: .3rem; }}
  .sev-error {{ color: var(--err); }}
  .sev-warning {{ color: var(--warn); }}
  .sev-info {{ color: var(--info); }}
  .empty-msg {{ color: #8b949e; padding: 2rem; text-align: center; }}
  .detail-row {{ display: none; }}
  .detail-row.open {{ display: table-row; }}
  .detail-cell {{ padding: .6rem .8rem; background: var(--card); font-size: .85rem; color: #8b949e; }}
  .detail-label {{ font-weight: 600; color: var(--fg); margin-right: .5rem; }}
  .commit-code {{ font-family: monospace; font-size: .8rem; background: var(--card); padding: .15rem .4rem;
    border-radius: 4px; cursor: pointer; border: 1px solid var(--border); }}
  .commit-code:hover {{ border-color: var(--info); }}
  .kind-bar {{ display: inline-block; height: 14px; border-radius: 3px; vertical-align: middle; margin-right: .4rem; }}
  .kind-row {{ display: flex; align-items: center; gap: .6rem; padding: .3rem 0; cursor: pointer; font-size: .9rem; }}
  .kind-row:hover {{ color: var(--fg); }}
  .kind-count {{ font-weight: 600; min-width: 24px; }}
  .charts-row {{ display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-bottom: 2rem; }}
  @media (max-width: 800px) {{ .charts-row {{ grid-template-columns: 1fr; }} }}
  .chart-box {{ background: var(--card); border: 1px solid var(--border); border-radius: 8px; padding: 1rem; }}
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
  <div class="card"><div class="num {drift_cls}">{drift}</div><div class="label">Drift</div></div>
</div>

<h2>By Kind</h2>
<div id="kindBreakdown"></div>

<h2>Violations</h2>
<div class="controls">
  <select id="runSelect" style="display:none"><option value="">Load stored run...</option></select>
  <select id="filterSeverity"><option value="">Severity: all</option>
    <option value="error">error</option><option value="warning">warning</option><option value="info">info</option></select>
  <select id="filterKind"><option value="">Kind: all</option></select>
  <input id="searchInput" type="text" placeholder="Search violations...">
  <button id="exportCsv">Export CSV</button>
</div>
<table id="violationsTable">
  <thead><tr>
    <th data-col="severity">Severity <span class="arrow"></span></th>
    <th data-col="rule">Rule <span class="arrow"></span></th>
    <th data-col="evidence">Evidence <span class="arrow"></span></th>
    <th data-col="commit">Commit <span class="arrow"></span></th>
    <th data-col="expand"></th>
  </tr></thead>
  <tbody id="violationsBody"></tbody>
</table>
<div id="emptyState" class="empty-msg" style="display:none">No violations match the current filters.</div>

<div class="charts-row">
  <div class="chart-box"><canvas id="trendChart"></canvas></div>
  <div class="chart-box"><canvas id="donutChart"></canvas></div>
</div>

<script>
const violationsData = {violations_json};
const trendData = {trend_json};

/* ── A5: Donut chart ── */
(function() {{
  const counts = {{}};
  violationsData.forEach(v => {{ counts[v.kind] = (counts[v.kind] || 0) + 1; }});
  const labels = Object.keys(counts);
  const palette = ['#f85149','#d29922','#58a6ff','#3fb950','#bc8cff','#f778ba'];
  if (labels.length) {{
    new Chart(document.getElementById('donutChart').getContext('2d'), {{
      type: 'doughnut',
      data: {{ labels, datasets: [{{ data: labels.map(k => counts[k]),
        backgroundColor: labels.map((_, i) => palette[i % palette.length]) }}] }},
      options: {{ responsive: true, plugins: {{ title: {{ display: true, text: 'By Kind', color: '#c9d1d9' }},
        legend: {{ labels: {{ color: '#c9d1d9' }} }} }} }}
    }});
  }}
}})();

/* ── Trend chart ── */
(function() {{
  const labels = trendData.map(d => d.commit.substring(0, 8));
  const datasets = [];
  const kinds = [...new Set(trendData.flatMap(d => Object.keys(d.counts)))];
  const palette = ['#f85149','#d29922','#58a6ff','#3fb950'];
  kinds.forEach((k, i) => {{
    datasets.push({{ label: k, data: trendData.map(d => d.counts[k] || 0),
      borderColor: palette[i % palette.length], backgroundColor: palette[i % palette.length] + '33',
      fill: true, tension: 0.3 }});
  }});
  if (labels.length) {{
    new Chart(document.getElementById('trendChart').getContext('2d'), {{
      type: 'line', data: {{ labels, datasets }},
      options: {{ responsive: true, plugins: {{ title: {{ display: true, text: 'Violations Over Time', color: '#c9d1d9' }},
        legend: {{ labels: {{ color: '#c9d1d9' }} }} }},
        scales: {{ x: {{ ticks: {{ color: '#8b949e' }}, grid: {{ color: '#30363d' }} }},
                   y: {{ ticks: {{ color: '#8b949e', stepSize: 1 }}, grid: {{ color: '#30363d' }}, beginAtZero: true }} }} }}
    }});
  }}
}})();

/* ── Table state ── */
let filteredData = violationsData.slice();
let sortCol = 'severity';
let sortAsc = true;
const sevOrder = {{ error: 0, warning: 1, info: 2 }};

function applyFilters() {{
  const sev = document.getElementById('filterSeverity').value;
  const kind = document.getElementById('filterKind').value;
  const q = document.getElementById('searchInput').value.toLowerCase();
  filteredData = violationsData.filter(v => {{
    if (sev && v.severity !== sev) return false;
    if (kind && v.kind !== kind) return false;
    if (q) {{
      const hay = (v.rule + ' ' + v.evidence + ' ' + v.impact + ' ' + v.recommendation + ' ' + v.components).toLowerCase();
      if (hay.indexOf(q) === -1) return false;
    }}
    return true;
  }});
  sortAndRender();
}}

function sortAndRender() {{
  filteredData.sort((a, b) => {{
    let va, vb;
    if (sortCol === 'severity') {{ va = sevOrder[a.severity] ?? 9; vb = sevOrder[b.severity] ?? 9; }}
    else if (sortCol === 'commit') {{ va = a.commit || 'zzz'; vb = b.commit || 'zzz'; }}
    else {{ va = a[sortCol] || ''; vb = b[sortCol] || ''; }}
    if (va < vb) return sortAsc ? -1 : 1;
    if (va > vb) return sortAsc ? 1 : -1;
    return 0;
  }});
  renderTable();
}}

function renderTable() {{
  const body = document.getElementById('violationsBody');
  const empty = document.getElementById('emptyState');
  body.innerHTML = '';
  if (!filteredData.length) {{ empty.style.display = 'block'; return; }}
  empty.style.display = 'none';
  filteredData.forEach((v, i) => {{
    const tr = document.createElement('tr');
    const sevTd = document.createElement('td');
    sevTd.className = 'sev-' + v.severity;
    sevTd.textContent = v.severity;
    tr.appendChild(sevTd);
    const ruleTd = document.createElement('td');
    ruleTd.textContent = v.rule;
    tr.appendChild(ruleTd);
    const evTd = document.createElement('td');
    evTd.textContent = v.evidence;
    tr.appendChild(evTd);
    const commitTd = document.createElement('td');
    if (v.commit && v.commit !== 'n/a') {{
      const code = document.createElement('span');
      code.className = 'commit-code';
      code.textContent = v.commit.substring(0, 8);
      code.title = v.commit;
      code.onclick = function() {{ navigator.clipboard.writeText(v.commit); }};
      commitTd.appendChild(code);
    }} else {{
      commitTd.textContent = 'n/a';
    }}
    tr.appendChild(commitTd);
    const expTd = document.createElement('td');
    const btn = document.createElement('button');
    btn.textContent = '+';
    btn.style.cssText = 'background:none;border:1px solid var(--border);color:var(--fg);border-radius:4px;cursor:pointer;padding:0 .4rem;';
    btn.onclick = function() {{ toggleDetail(i); }};
    expTd.appendChild(btn);
    tr.appendChild(expTd);
    body.appendChild(tr);
    const dr = document.createElement('tr');
    dr.className = 'detail-row';
    dr.id = 'detail-' + i;
    const dc = document.createElement('td');
    dc.className = 'detail-cell';
    dc.colSpan = 5;
    const parts = [];
    parts.push('<span class="detail-label">Impact:</span>' + v.impact);
    parts.push('<span class="detail-label">Recommendation:</span>' + v.recommendation);
    parts.push('<span class="detail-label">Components:</span>' + v.components);
    dc.innerHTML = parts.join(' &nbsp;|&nbsp; ');
    dr.appendChild(dc);
    body.appendChild(dr);
  }});
}}

function toggleDetail(i) {{
  const el = document.getElementById('detail-' + i);
  if (el) el.classList.toggle('open');
}}

/* ── Sort headers ── */
document.querySelectorAll('#violationsTable th[data-col]').forEach(th => {{
  th.onclick = function() {{
    const col = th.getAttribute('data-col');
    if (col === 'expand') return;
    if (sortCol === col) sortAsc = !sortAsc;
    else {{ sortCol = col; sortAsc = true; }}
    document.querySelectorAll('#violationsTable th .arrow').forEach(a => a.textContent = '');
    th.querySelector('.arrow').textContent = sortAsc ? '\\u25B2' : '\\u25BC';
    sortAndRender();
  }};
}});

/* ── Filter listeners ── */
document.getElementById('filterSeverity').onchange = applyFilters;
document.getElementById('filterKind').onchange = applyFilters;
document.getElementById('searchInput').oninput = applyFilters;

/* ── A2: Kind breakdown ── */
(function() {{
  const counts = {{}};
  const sevByKind = {{}};
  violationsData.forEach(v => {{
    counts[v.kind] = (counts[v.kind] || 0) + 1;
    sevByKind[v.kind] = sevByKind[v.kind] || {{}};
    sevByKind[v.kind][v.severity] = (sevByKind[v.kind][v.severity] || 0) + 1;
  }});
  const maxCount = Math.max(...Object.values(counts), 1);
  const container = document.getElementById('kindBreakdown');
  const selectKind = document.getElementById('filterKind');
  const palette = {{ error: '#f85149', warning: '#d29922', info: '#58a6ff' }};
  Object.keys(counts).sort((a,b) => counts[b] - counts[a]).forEach(kind => {{
    const opt = document.createElement('option');
    opt.value = kind; opt.textContent = kind;
    selectKind.appendChild(opt);
    const dominant = Object.keys(sevByKind[kind]).sort((a,b) => (sevByKind[kind][b]||0) - (sevByKind[kind][a]||0))[0];
    const color = palette[dominant] || '#8b949e';
    const pct = (counts[kind] / maxCount * 100);
    const row = document.createElement('div');
    row.className = 'kind-row';
    row.innerHTML = '<span class="kind-count">' + counts[kind] + '</span>'
      + '<span class="kind-bar" style="width:' + pct + '%;background:' + color + '"></span>'
      + '<span>' + kind + '</span>';
    row.onclick = function() {{
      const sel = document.getElementById('filterKind');
      sel.value = sel.value === kind ? '' : kind;
      applyFilters();
    }};
    container.appendChild(row);
  }});
}})();

/* ── A1: CSV export ── */
document.getElementById('exportCsv').onclick = function() {{
  const headers = ['rule','kind','severity','evidence','impact','recommendation','commit'];
  const esc = function(s) {{ return '"' + String(s).replace(/"/g, '""') + '"'; }};
  const lines = [headers.join(',')];
  filteredData.forEach(v => {{
    lines.push(headers.map(h => esc(v[h])).join(','));
  }});
  const blob = new Blob([lines.join('\\n')], {{ type: 'text/csv' }});
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = 'sentinel-violations.csv';
  a.click(); URL.revokeObjectURL(url);
}};

/* ── Initial render ── */
applyFilters();

/* ── Multirun: fetch /api/runs if served by sentinel serve ── */
(function() {{
  if (location.protocol === 'file:') return;
  var sel = document.getElementById('runSelect');
  fetch('/api/runs').then(function(r) {{ return r.json(); }}).then(function(runs) {{
    if (!runs.length) return;
    sel.style.display = '';
    runs.forEach(function(run) {{
      var o = document.createElement('option');
      o.value = run.id;
      o.textContent = 'Run #' + run.id + ' / ' + run.commit_sha.substring(0, 8) + ' / ' + run.ts.substring(0, 10);
      sel.appendChild(o);
    }});
    sel.onchange = function() {{
      var id = sel.value;
      if (!id) return;
      fetch('/api/runs/' + id).then(function(r) {{ return r.json(); }}).then(function(run) {{
        if (run.error) return;
        violationsData.length = 0;
        run.violations.forEach(function(v) {{
          violationsData.push({{
            rule: v.rule, kind: v.kind, severity: v.severity,
            evidence: v.evidence, impact: v.impact,
            recommendation: v.recommendation,
            commit: v.commit_sha || 'n/a',
            components: v.components || ''
          }});
        }});
        rebuildKindSelect();
        rebuildKindBreakdown();
        rebuildDonut();
        applyFilters();
      }});
    }};
  }}).catch(function() {{}});

  function rebuildKindSelect() {{
    var sel = document.getElementById('filterKind');
    var val = sel.value;
    sel.innerHTML = '<option value="">Kind: all</option>';
    var kinds = {{}};
    violationsData.forEach(function(v) {{ kinds[v.kind] = 1; }});
    Object.keys(kinds).sort().forEach(function(k) {{
      var o = document.createElement('option');
      o.value = k; o.textContent = k;
      sel.appendChild(o);
    }});
    sel.value = val;
  }}

  function rebuildKindBreakdown() {{
    var container = document.getElementById('kindBreakdown');
    container.innerHTML = '';
    var counts = {{}};
    var sevByKind = {{}};
    violationsData.forEach(function(v) {{
      counts[v.kind] = (counts[v.kind] || 0) + 1;
      sevByKind[v.kind] = sevByKind[v.kind] || {{}};
      sevByKind[v.kind][v.severity] = (sevByKind[v.kind][v.severity] || 0) + 1;
    }});
    var maxCount = Math.max.apply(null, Object.values(counts).concat([1]));
    var palette = {{ error: '#f85149', warning: '#d29922', info: '#58a6ff' }};
    Object.keys(counts).sort(function(a,b) {{ return counts[b] - counts[a]; }}).forEach(function(kind) {{
      var dominant = Object.keys(sevByKind[kind]).sort(function(a,b) {{ return (sevByKind[kind][b]||0) - (sevByKind[kind][a]||0); }})[0];
      var color = palette[dominant] || '#8b949e';
      var pct = (counts[kind] / maxCount * 100);
      var row = document.createElement('div');
      row.className = 'kind-row';
      row.innerHTML = '<span class="kind-count">' + counts[kind] + '</span>'
        + '<span class="kind-bar" style="width:' + pct + '%;background:' + color + '"></span>'
        + '<span>' + kind + '</span>';
      row.onclick = function() {{
        var sel = document.getElementById('filterKind');
        sel.value = sel.value === kind ? '' : kind;
        applyFilters();
      }};
      container.appendChild(row);
    }});
  }}

  function rebuildDonut() {{
    var oldChart = Chart.getChart('donutChart');
    if (oldChart) oldChart.destroy();
    var counts = {{}};
    violationsData.forEach(function(v) {{ counts[v.kind] = (counts[v.kind] || 0) + 1; }});
    var labels = Object.keys(counts);
    var palette = ['#f85149','#d29922','#58a6ff','#3fb950','#bc8cff','#f778ba'];
    if (labels.length) {{
      new Chart(document.getElementById('donutChart').getContext('2d'), {{
        type: 'doughnut',
        data: {{ labels: labels, datasets: [{{ data: labels.map(function(k) {{ return counts[k]; }}),
          backgroundColor: labels.map(function(_, i) {{ return palette[i % palette.length]; }}) }}] }},
        options: {{ responsive: true, plugins: {{ title: {{ display: true, text: 'By Kind', color: '#c9d1d9' }},
          legend: {{ labels: {{ color: '#c9d1d9' }} }} }} }}
      }});
    }}
  }}
}})();
</script>
</body>
</html>
"""


def _violation_to_dict(v: object) -> dict[str, object]:
    return {
        "rule": v.rule,
        "kind": v.kind.value,
        "severity": v.severity.value,
        "evidence": v.evidence,
        "impact": v.impact,
        "recommendation": v.recommendation,
        "commit": v.commit or "n/a",
        "components": ", ".join(v.components),
    }


def render_report(
    *,
    violations: list,
    trend_data: list[dict] | None = None,
    meta: str = "",
    drift: float = 0.0,
) -> str:
    """Return a self-contained HTML report string."""
    errors = sum(1 for v in violations if v.severity.value == "error")
    warnings = sum(1 for v in violations if v.severity.value == "warning")
    infos = sum(1 for v in violations if v.severity.value == "info")
    total = len(violations)
    drift_cls = "drift-green" if drift <= 0.3 else "drift-yellow" if drift <= 0.6 else "drift-red"

    violations_json = json.dumps([_violation_to_dict(v) for v in violations]).replace("</", "<\\/")

    trend_json = json.dumps(trend_data or []).replace("</", "<\\/")
    return _TEMPLATE.format(
        meta=_html.escape(meta),
        total=total,
        errors=errors,
        warnings=warnings,
        infos=infos,
        drift=f"{drift:.2f}",
        drift_cls=drift_cls,
        violations_json=violations_json,
        trend_json=trend_json,
    )


def write_report(
    output: Path,
    *,
    violations: list,
    trend_data: list[dict] | None = None,
    meta: str = "",
    drift: float = 0.0,
) -> None:
    """Write an HTML report to `output`."""
    html = render_report(violations=violations, trend_data=trend_data, meta=meta, drift=drift)
    output.write_text(html, encoding="utf-8")
