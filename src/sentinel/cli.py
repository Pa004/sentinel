"""Sentinel CLI entrypoint."""

from __future__ import annotations

import hashlib
from pathlib import Path

import typer
from rich.console import Console

from sentinel.analyzers.dependency_extractor import build_dependency_graph
from sentinel.parsers.registry import source_files
from sentinel.reports.json import serialize

app = typer.Typer(help="Architecture erosion detector — intended vs observed.")
console = Console()

DEFAULT_DB = ".sentinel/sentinel.db"


def _manifest_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


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
    save: bool = typer.Option(False, "--save", help="Persist results to .sentinel/sentinel.db"),  # noqa: B008
    db: Path | None = typer.Option(None, "--db", help="Override SQLite database path"),  # noqa: B008
) -> None:
    """Analyze a repository and report architectural violations."""
    from sentinel.domain.manifest import ArchitectureManifest
    from sentinel.git_origin import find_git_root, head_commit_sha
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

    if save:
        from sentinel.persistence.store import ArchitectureStore

        db_path = db if db is not None else repo / DEFAULT_DB
        commit = head_commit_sha(git_root) or "n/a"
        store = ArchitectureStore(db_path)
        try:
            run_id = store.save_run(
                repo_path=repo,
                commit=commit,
                manifest_hash=_manifest_hash(manifest),
                violations=result.violations,
            )
            console.print(f"\nSaved as run #{run_id} to {db_path}")
        finally:
            store.close()


@app.command()
def graph(
    repo: Path = typer.Argument(..., help="Repository path"),  # noqa: B008
) -> None:
    """Print the dependency graph for a repository."""
    files = source_files(repo)
    g = build_dependency_graph(files)
    for node in g.nodes():
        for dep in g.dependencies_of(node):
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


@app.command()
def history(
    repo: Path = typer.Argument(..., help="Repository path"),  # noqa: B008
    db: Path | None = typer.Option(None, "--db", help="Override SQLite database path"),  # noqa: B008
) -> None:
    """Show stored analysis runs for a repository."""
    from sentinel.persistence.store import ArchitectureStore

    db_path = db if db is not None else repo / DEFAULT_DB
    if not db_path.exists():
        console.print("No database found. Run `sentinel analyze --save` first.")
        return
    store = ArchitectureStore(db_path)
    try:
        import json as _json
        runs = store.list_runs()
        if not runs:
            console.print("No runs stored yet.")
            return
        console.print(f"{'Run':>5}  {'Commit':>8}  {'Date':>10}  Counts")
        console.print("-" * 60)
        for run in runs:
            counts = run["counts"]
            parts = ", ".join(f"{k}={v}" for k, v in sorted(_json.loads(counts).items()))
            date = run["ts"][:10]
            console.print(
                f"{run['id']:>5}  {run['commit_sha'][:8]:>8}  "
                f"{date:>10}  {parts or 'clean'}"
            )
    finally:
        store.close()


@app.command()
def report(
    repo: Path = typer.Argument(..., help="Repository path"),  # noqa: B008
    manifest: Path = typer.Option(  # noqa: B008
        ...,
        "--manifest",
        "-m",
        help="Architecture manifest YAML path",
    ),
    output: Path = typer.Option(  # noqa: B008
        Path("sentinel-report.html"),
        "--output",
        "-o",
        help="Output HTML file path",
    ),
    db: Path | None = typer.Option(None, "--db", help="Override SQLite database path"),  # noqa: B008
) -> None:
    """Generate a self-contained HTML report with violations and trend charts."""
    from sentinel.domain.manifest import ArchitectureManifest
    from sentinel.git_origin import find_git_root, head_commit_sha
    from sentinel.manifest.loader import load_manifest
    from sentinel.reports.html_report import write_report
    from sentinel.trend import build_trend
    from sentinel.violation_engine import analyze_repository

    man: ArchitectureManifest = load_manifest(manifest)
    git_root = find_git_root(repo)
    result = analyze_repository(repo, man, git_root=git_root)
    commit = head_commit_sha(git_root) or "n/a"

    # Build trend data from git history
    points = build_trend(repo, man)
    trend_data = [
        {"commit": p.commit, "counts": {k.value: v for k, v in p.counts.items()}}
        for p in points
    ]

    write_report(
        output,
        violations=result.violations,
        trend_data=trend_data,
        meta=f"Repo: {repo} | Commit: {commit[:8]} | Violations: {len(result.violations)}",
    )
    console.print(f"Report written to {output}")


if __name__ == "__main__":
    app()
