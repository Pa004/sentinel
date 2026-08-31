"""Sentinel CLI entrypoint."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

from sentinel.analyzers.dependency_extractor import build_dependency_graph
from sentinel.parsers.registry import source_files
from sentinel.reports.json import serialize
from sentinel.violation_engine import analyze_repository_from_manifest

app = typer.Typer(help="Architecture erosion detector — intended vs observed.")
console = Console()


@app.command()
def analyze(
    repo: Path = typer.Argument(..., help="Repository path to analyze"),  # noqa: B008
    manifest: Path = typer.Option(  # noqa: B008
        ...,
        "--manifest",
        "-m",
        help="Architecture manifest YAML path",
    ),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),  # noqa: B008
) -> None:
    """Analyze a repository and report architectural violations."""
    result = analyze_repository_from_manifest(repo, manifest)
    if json_output:
        console.print(serialize(result))
    else:
        from sentinel.reports.console import render_console

        render_console(result, console)


@app.command()
def graph(
    repo: Path = typer.Argument(..., help="Repository path"),  # noqa: B008
) -> None:
    """Print the dependency graph for a repository."""
    files = source_files(repo)
    graph = build_dependency_graph(files)
    for node in graph.nodes():
        for dep in graph.dependencies_of(node):
            console.print(f"{dep.source} -> {dep.target}  ({dep.evidence})")


if __name__ == "__main__":
    app()
