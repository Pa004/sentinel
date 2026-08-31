"""End-to-end tests for the violation engine and CLI."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from sentinel.cli import app
from sentinel.violation_engine import analyze_repository_from_manifest

FIXTURES = Path(__file__).parent / "fixtures"


def test_good_fixture_has_no_violations() -> None:
    result = analyze_repository_from_manifest(FIXTURES / "GOOD", FIXTURES / "manifest.yaml")
    assert result.violations == []


def test_bad_fixture_detects_layer_violation() -> None:
    result = analyze_repository_from_manifest(FIXTURES / "BAD", FIXTURES / "manifest.yaml")
    kinds = {v.kind.value for v in result.violations}
    assert "layer_violation" in kinds


def test_cli_analyze_reports_violations() -> None:
    runner = CliRunner()
    result = runner.invoke(
        app,
        ["analyze", str(FIXTURES / "BAD"), "--manifest", str(FIXTURES / "manifest.yaml")],
    )
    assert result.exit_code == 0
    assert "Architectural Violations" in result.stdout


def test_cli_analyze_good_says_clean() -> None:
    runner = CliRunner()
    result = runner.invoke(
        app,
        ["analyze", str(FIXTURES / "GOOD"), "--manifest", str(FIXTURES / "manifest.yaml")],
    )
    assert result.exit_code == 0
    assert "No architectural violations" in result.stdout


def test_cli_graph_command_runs() -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["graph", str(FIXTURES / "GOOD")])
    assert result.exit_code == 0
