"""Trend analysis: detect architectural regression across commits."""

from __future__ import annotations

import shutil
from pathlib import Path
from subprocess import run

from sentinel.domain.manifest import ArchitectureManifest
from sentinel.domain.trend import TrendPoint
from sentinel.domain.violations import ViolationKind
from sentinel.parsers.registry import parser_for
from sentinel.violation_engine import AnalysisResult, analyze_repository

SOURCE_SUFFIXES = (".ts", ".tsx", ".js", ".jsx", ".py")
SNAPSHOT_DIR = ".sentinel_snapshot"


def _git(repo: Path, *args: str) -> str:
    proc = run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {proc.stderr.strip()}")
    return proc.stdout


def list_commits(repo: Path, since: str | None, until: str | None) -> list[str]:
    """Return commit SHAs in the requested range, oldest first."""
    if since and until:
        ref = f"{since}..{until}"
    elif since:
        ref = f"{since}..HEAD"
    else:
        ref = "HEAD"
    stdout = _git(repo, "log", "--reverse", "--format=%H", ref)
    return [c for c in stdout.splitlines() if c]


def snapshot_source_files(repo: Path, commit: str) -> list[str]:
    """Relative paths of supported source files present at `commit`."""
    stdout = _git(repo, "ls-tree", "-r", "--name-only", commit)
    paths: list[str] = []
    for line in stdout.splitlines():
        if not line:
            continue
        p = Path(line)
        if p.suffix.lower() in SOURCE_SUFFIXES and parser_for(p) is not None:
            paths.append(line)
    return paths


def analyze_at_commit(repo: Path, commit: str, manifest: ArchitectureManifest) -> AnalysisResult:
    """Reconstruct `commit` into a temp dir and analyze it as a repository."""
    snapshot = Path(repo) / SNAPSHOT_DIR
    if snapshot.exists():
        shutil.rmtree(snapshot)
    snapshot.mkdir(parents=True)

    for rel in snapshot_source_files(repo, commit):
        content = _git(repo, "show", f"{commit}:{rel}")
        target = snapshot / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")

    result = analyze_repository(snapshot, manifest)
    shutil.rmtree(snapshot)
    return result


def build_trend(
    repo: Path,
    manifest: ArchitectureManifest,
    since: str | None = None,
    until: str | None = None,
) -> list[TrendPoint]:
    """Compute violation counts per commit across the requested range."""
    commits = list_commits(repo, since, until)
    points: list[TrendPoint] = []
    for sha in commits:
        result = analyze_at_commit(repo, sha, manifest)
        counts: dict[ViolationKind, int] = {}
        for v in result.violations:
            counts[v.kind] = counts.get(v.kind, 0) + 1
        points.append(TrendPoint(commit=sha, counts=counts))
    return points
