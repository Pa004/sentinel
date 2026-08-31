"""Trend analysis: detect architectural regression across commits."""

from __future__ import annotations

import shutil
from pathlib import Path
from subprocess import run

from sentinel.domain.manifest import ArchitectureManifest
from sentinel.domain.trend import TrendPoint
from sentinel.domain.violations import Violation, ViolationKind
from sentinel.git_origin import source_path_from_evidence
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

    try:
        for rel in snapshot_source_files(repo, commit):
            content = _git(repo, "show", f"{commit}:{rel}")
            target = (snapshot / rel).resolve()
            if not target.is_relative_to(snapshot.resolve()):
                raise RuntimeError(f"Path traversal attempt: {rel}")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")

        return analyze_repository(snapshot, manifest)
    finally:
        if snapshot.exists():
            shutil.rmtree(snapshot)


def _stable_key(violation: Violation, snapshot_dir: Path) -> str:
    """A stable identity for a violation, independent of the temp snapshot path."""
    source = source_path_from_evidence(violation.evidence)
    if source is None:
        return f"{violation.kind.value} <rule:{violation.rule}>"
    try:
        rel = source.relative_to(snapshot_dir)
        return f"{violation.kind.value} {rel.as_posix()}"
    except ValueError:
        return f"{violation.kind.value} {source}"


def build_trend(
    repo: Path,
    manifest: ArchitectureManifest,
    since: str | None = None,
    until: str | None = None,
) -> list[TrendPoint]:
    """Compute violation counts per commit and flag architectural regression.

    A violation counts as introduced (regression) at a commit when its stable
    identity was absent from the immediately preceding commit in the range.
    """
    commits = list_commits(repo, since, until)
    snapshot_dir = Path(repo) / SNAPSHOT_DIR
    points: list[TrendPoint] = []
    prev_keys: set[str] = set()
    for sha in commits:
        result = analyze_at_commit(repo, sha, manifest)
        counts: dict[ViolationKind, int] = {}
        introduced: list[str] = []
        keys: set[str] = set()
        for v in result.violations:
            counts[v.kind] = counts.get(v.kind, 0) + 1
            key = _stable_key(v, snapshot_dir)
            keys.add(key)
            if key not in prev_keys:
                introduced.append(key)
        points.append(
            TrendPoint(
                commit=sha,
                counts=counts,
                introduced=sorted(introduced),
                drift=result.drift,
            )
        )
        prev_keys = keys
    return points
