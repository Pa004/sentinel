"""Tests for the interactive HTML report generator."""

from __future__ import annotations

import json
from pathlib import Path

from sentinel.domain.violations import Severity, Violation, ViolationKind
from sentinel.reports.html_report import render_report, write_report

VIOLATIONS = [
    Violation(
        rule="layer_violation",
        kind=ViolationKind.LAYER_VIOLATION,
        evidence="ui/App.ts imports domain/User.ts",
        components=("ui", "domain"),
        impact="presentation layer bypasses application layer",
        recommendation="route through application layer",
        severity=Severity.ERROR,
        commit="abc12345",
    ),
    Violation(
        rule="circular_dependency",
        kind=ViolationKind.CIRCULAR_DEPENDENCY,
        evidence="a.ts -> b.ts -> a.ts",
        components=("a", "b"),
        impact="tight coupling, hard to test",
        recommendation="extract shared interface",
        severity=Severity.WARNING,
        commit="abc12345",
    ),
    Violation(
        rule="high_coupling",
        kind=ViolationKind.HIGH_COUPLING,
        evidence="hub.ts fan-in=8",
        components=("hub",),
        impact="change magnet",
        recommendation="split hub module",
        severity=Severity.INFO,
        commit=None,
    ),
]

TREND = [
    {"commit": "abc12345", "counts": {"layer_violation": 1, "circular_dependency": 1}},
    {
        "commit": "def67890",
        "counts": {"layer_violation": 1, "circular_dependency": 1, "high_coupling": 1},
    },
]


def _extract_violations_json(html: str) -> list[dict]:
    marker = "const violationsData = "
    start = html.index(marker) + len(marker)
    end = html.index(";", start)
    return json.loads(html[start:end])


def test_render_report_contains_cards_and_controls() -> None:
    html = render_report(violations=VIOLATIONS, trend_data=TREND, meta="test repo")
    assert "Total Violations" in html
    assert "Errors" in html
    assert "Warnings" in html
    assert "Info" in html
    assert 'id="violationsTable"' in html
    assert 'id="filterSeverity"' in html
    assert 'id="filterKind"' in html
    assert 'id="searchInput"' in html
    assert 'id="exportCsv"' in html


def test_render_report_violations_json_data() -> None:
    html = render_report(violations=VIOLATIONS, trend_data=TREND)
    data = _extract_violations_json(html)
    assert len(data) == 3
    assert data[0]["rule"] == "layer_violation"
    assert data[0]["severity"] == "error"
    assert data[0]["commit"] == "abc12345"
    assert data[1]["kind"] == "circular_dependency"
    assert data[2]["commit"] == "n/a"
    assert "ui" in data[0]["components"]


def test_render_report_severity_in_json() -> None:
    html = render_report(violations=VIOLATIONS, trend_data=TREND)
    data = _extract_violations_json(html)
    severities = [v["severity"] for v in data]
    assert severities.count("error") == 1
    assert severities.count("warning") == 1
    assert severities.count("info") == 1


def test_render_report_embebs_trend_json() -> None:
    html = render_report(violations=VIOLATIONS, trend_data=TREND)
    assert "abc12345" in html
    assert "def67890" in html
    assert '"layer_violation"' in html


def test_render_report_empty_violations() -> None:
    html = render_report(violations=[], trend_data=[])
    assert "Total Violations" in html
    assert 'id="violationsTable"' in html
    assert "trendData = []" in html
    data = _extract_violations_json(html)
    assert data == []


def test_render_report_no_trend() -> None:
    html = render_report(violations=VIOLATIONS, trend_data=None)
    assert "trendData = []" in html


def test_write_report_creates_file(tmp_path: Path) -> None:
    output = tmp_path / "report.html"
    write_report(
        output,
        violations=VIOLATIONS,
        trend_data=TREND,
        meta="unit test",
    )
    assert output.exists()
    content = output.read_text(encoding="utf-8")
    assert "<!DOCTYPE html>" in content
    data = _extract_violations_json(content)
    assert any(v["rule"] == "layer_violation" for v in data)


def test_render_report_meta_shown() -> None:
    html = render_report(violations=VIOLATIONS, trend_data=TREND, meta="repo: sentinel")
    assert "repo: sentinel" in html


def test_render_report_escapes_html_in_violations() -> None:
    xss_violation = Violation(
        rule="<script>alert(1)</script>",
        kind=ViolationKind.LAYER_VIOLATION,
        evidence='<img onerror="alert(1)" src=x>',
        components=("<b>xss</b>",),
        impact="<script>alert(1)</script>",
        recommendation="<a href=javascript:alert(1)>click</a>",
        severity=Severity.ERROR,
        commit=None,
    )
    html = render_report(violations=[xss_violation], trend_data=[], meta="<b>repo</b>")
    # Raw XSS strings must not appear in the HTML
    assert "<script>alert(1)</script>" not in html
    # The malicious data is in violationsData JSON, with </ escaped to <\/
    data = _extract_violations_json(html)
    assert data[0]["rule"] == "<script>alert(1)</script>"
    assert data[0]["evidence"] == '<img onerror="alert(1)" src=x>'
    # </script> breakout is prevented
    assert "</script><script>" not in html
    assert "<\\/script>" in html


def test_render_report_escapes_script_in_trend() -> None:
    malicious_trend = [{"commit": "</script><script>alert(1)</script>", "counts": {}}]
    html = render_report(violations=[], trend_data=malicious_trend)
    assert "</script><script>" not in html
    assert "<\\/script>" in html


def test_render_report_has_kind_breakdown() -> None:
    html = render_report(violations=VIOLATIONS, trend_data=TREND)
    assert 'id="kindBreakdown"' in html
    assert 'id="donutChart"' in html


def test_render_report_has_drift() -> None:
    html = render_report(violations=VIOLATIONS, trend_data=TREND, drift=0.75)
    assert "0.75" in html
    assert "drift-red" in html
