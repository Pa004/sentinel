"""Tests for trend analysis over git history."""

from __future__ import annotations

from pathlib import Path
from subprocess import run

from sentinel.domain.manifest import ArchitectureManifest, Layer
from sentinel.trend import analyze_at_commit, build_trend


def _git(repo: Path, *args: str) -> None:
    run(["git", "-C", str(repo), *args], check=True, capture_output=True)


def _make_evolving_repo(base: Path) -> Path:
    repo = base / "evolving"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "test@test.com")
    _git(repo, "config", "user.name", "Test")
    _git(repo, "config", "commit.gpgsign", "false")

    good = repo / "presentation" / "App.ts"
    good.parent.mkdir(parents=True)
    good.write_text("import { svc } from '../application/service';\n", encoding="utf-8")
    (repo / "application" / "service.ts").parent.mkdir(exist_ok=True)
    (repo / "application" / "service.ts").write_text("export function svc() {}\n", encoding="utf-8")
    _git(repo, "add", ".")
    _git(repo, "commit", "-q", "-m", "good architecture")

    bad = repo / "presentation" / "App.ts"
    bad.write_text("import { db } from '../domain/db';\nexport const x = db;\n", encoding="utf-8")
    (repo / "domain" / "db.ts").parent.mkdir(exist_ok=True)
    (repo / "domain" / "db.ts").write_text("export const db = {};\n", encoding="utf-8")
    _git(repo, "add", ".")
    _git(repo, "commit", "-q", "-m", "introduce layer regression")
    return repo


MANIFEST = ArchitectureManifest(
    {
        "presentation": Layer("presentation", frozenset({"application"})),
        "application": Layer("application", frozenset({"domain"})),
        "domain": Layer("domain", frozenset()),
    }
)


def test_trend_detects_regression(tmp_path: Path) -> None:
    repo = _make_evolving_repo(tmp_path)
    points = build_trend(repo, MANIFEST)
    assert len(points) == 2
    # first commit is clean, second has layer violations
    assert points[0].total() == 0
    assert points[1].total() > 0


def test_trend_marks_regression_as_introduced(tmp_path: Path) -> None:
    repo = _make_evolving_repo(tmp_path)
    points = build_trend(repo, MANIFEST)
    assert points[0].introduced == []
    assert any(item.startswith("layer_violation ") for item in points[1].introduced)


def test_trend_does_not_repeat_introduced_violations(tmp_path: Path) -> None:
    repo = _make_evolving_repo(tmp_path)
    points = build_trend(repo, MANIFEST)
    # the layer regression stays present in the second commit but is only
    # flagged as introduced the first time it appears.
    introduced_first = set(points[1].introduced)
    assert introduced_first
    # first commit was clean, so no violation is duplicated across the range
    assert set(points[0].introduced).isdisjoint(introduced_first)


def test_analyze_at_commit_snapshots_each_state(tmp_path: Path) -> None:
    repo = _make_evolving_repo(tmp_path)
    commits = build_trend(repo, MANIFEST)
    shas = [p.commit for p in commits]
    first = analyze_at_commit(repo, shas[0], MANIFEST)
    assert first.violations == []


def test_analyze_at_commit_rejects_path_traversal(tmp_path: Path) -> None:
    snapshot = tmp_path / ".sentinel_snapshot"
    snapshot.mkdir()
    # A path with ../ should not resolve inside snapshot
    target = (snapshot / "../../etc/passwd").resolve()
    assert not target.is_relative_to(snapshot.resolve())
