"""Tests for the HTML report generator."""

from __future__ import annotations

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


def test_render_report_contains_table_and_cards() -> None:
    html = render_report(violations=VIOLATIONS, trend_data=TREND, meta="test repo")
    assert "Total Violations" in html
    assert "Errors" in html
    assert "Warnings" in html
    assert "Info" in html
    assert "<table>" in html
    assert "layer_violation" in html
    assert "circular_dependency" in html
    assert "high_coupling" in html


def test_render_report_counts_by_severity() -> None:
    html = render_report(violations=VIOLATIONS, trend_data=TREND)
    assert html.count('class="sev-error"') == 1
    assert html.count('class="sev-warning"') == 1
    assert html.count('class="sev-info"') == 1


def test_render_report_embebs_trend_json() -> None:
    html = render_report(violations=VIOLATIONS, trend_data=TREND)
    assert "abc12345" in html
    assert "def67890" in html
    assert '"layer_violation"' in html


def test_render_report_empty_violations() -> None:
    html = render_report(violations=[], trend_data=[])
    assert "Total Violations" in html
    assert "<table>" in html
    assert "trendData = []" in html


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
    assert "layer_violation" in content


def test_render_report_meta_shown() -> None:
    html = render_report(violations=VIOLATIONS, trend_data=TREND, meta="repo: sentinel")
    assert "repo: sentinel" in html
