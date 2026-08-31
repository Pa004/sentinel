"""Console rendering of an analysis result via rich."""

from __future__ import annotations

from rich.console import Console
from rich.table import Table

from sentinel.violation_engine import AnalysisResult


def render_console(result: AnalysisResult, console: Console | None = None) -> None:
    console = console or Console()
    if not result.violations:
        console.print("[green]No architectural violations detected.[/green]")
        return

    counts: dict[str, int] = {}
    for v in result.violations:
        counts[v.rule] = counts.get(v.rule, 0) + 1

    table = Table(title="Architectural Violations")
    table.add_column("Severity", style="bold")
    table.add_column("Rule")
    table.add_column("Evidence")
    table.add_column("Impact")
    table.add_column("Recommendation")
    table.add_column("Origin commit")

    severity_color = {"error": "red", "warning": "yellow", "info": "cyan"}
    for v in result.violations:
        color = severity_color.get(v.severity.value, "white")
        origin = f"{v.commit[:8]}" if v.commit else "n/a"
        table.add_row(
            f"[{color}]{v.severity.value}[/{color}]",
            v.rule,
            v.evidence,
            v.impact,
            v.recommendation,
            origin,
        )
    console.print(table)
    drift_color = "green" if result.drift <= 0.3 else "yellow" if result.drift <= 0.6 else "red"
    console.print(f"Total: [bold]{len(result.violations)}[/bold] violations")
    console.print(f"Drift: [{drift_color}]{result.drift:.2f}[/{drift_color}]")
    if result.metrics:
        m = result.metrics
        console.print(
            f"Graph: {m.node_count} nodes, {m.edge_count} edges, avg coupling {m.avg_coupling:.1f}"
        )
        console.print(
            f"Cycles: {m.cycle_count} | Layers: {m.layer_violation_count} | "
            f"God modules: {m.god_module_count} | High coupling: {m.high_coupling_count}"
        )
