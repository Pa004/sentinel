"""Sentinel CLI entrypoint."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

from sentinel.analyzers.dependency_extractor import build_dependency_graph
from sentinel.parsers.registry import source_files
from sentinel.reports.json import serialize

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
    from sentinel.domain.manifest import ArchitectureManifest
    from sentinel.git_origin import find_git_root
    from sentinel.manifest.loader import load_manifest
    from sentinel.violation_engine import analyze_repository

    man: ArchitectureManifest = load_manifest(manifest)
    git_root = find_git_root(repo)
    result = analyze_repository(repo, man, git_root=git_root)
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


@app.command()
def trend(
    repo: Path = typer.Argument(..., help="Repository path"),  # noqa: B008
    manifest: Path = typer.Option(  # noqa: B008
        ...,
        "--manifest",
        "-m",
        help="Architecture manifest YAML path",
    ),
    since: str | None = typer.Option(None, "--from", help="Start commit SHA"),  # noqa: B008
    until: str | None = typer.Option(None, "--to", help="End commit SHA"),  # noqa: B008
) -> None:
    """Report architectural regression across a commit range."""
    from sentinel.domain.manifest import ArchitectureManifest
    from sentinel.manifest.loader import load_manifest
    from sentinel.trend import build_trend

    man: ArchitectureManifest = load_manifest(manifest)
    points = build_trend(repo, man, since=since, until=until)
    if not points:
        console.print("No commits in range to analyze.")
        return
    for point in points:
        joined = ", ".join(f"{kind.value}={count}" for kind, count in point.counts.items())
        parts = joined or "clean"
        console.print(f"{point.commit[:8]}  {parts}")
        if point.introduced:
            for item in point.introduced:
                console.print(f"      introduced: {item}")


if __name__ == "__main__":
    app()
