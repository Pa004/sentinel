"""Tests for git commit-origin attribution on violations."""

from __future__ import annotations

from pathlib import Path
from subprocess import run

from sentinel.domain.manifest import ArchitectureManifest, Layer
from sentinel.git_origin import find_git_root, source_path_from_evidence
from sentinel.violation_engine import analyze_repository

MANIFEST = ArchitectureManifest(
    {
        "presentation": Layer("presentation", frozenset({"application"})),
        "application": Layer("application", frozenset({"domain"})),
        "domain": Layer("domain", frozenset()),
    }
)


def _git(repo: Path, *args: str) -> None:
    run(["git", "-C", str(repo), *args], check=True, capture_output=True)


def _make_repo(base: Path, commit_msg: str) -> Path:
    repo = base / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "test@test.com")
    _git(repo, "config", "user.name", "Test")
    _git(repo, "config", "commit.gpgsign", "false")
    bad = repo / "presentation" / "App.ts"
    bad.parent.mkdir(parents=True)
    bad.write_text("import { db } from '../domain/db';\nexport const x = db;\n", encoding="utf-8")
    (repo / "domain" / "db.ts").parent.mkdir(exist_ok=True)
    (repo / "domain" / "db.ts").write_text("export const db = {};\n", encoding="utf-8")
    _git(repo, "add", ".")
    _git(repo, "commit", "-q", "-m", commit_msg)
    return repo


def test_analyze_reports_origin_commit(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path, "introduce layer regression")
    result = analyze_repository(repo, MANIFEST, git_root=repo)
    assert result.violations
    layer_violations = [v for v in result.violations if v.rule == "layer-violation"]
    assert layer_violations
    assert layer_violations[0].commit is not None


def test_analyze_without_git_leaves_commit_none(tmp_path: Path) -> None:
    repo = tmp_path / "no_git"
    repo.mkdir()
    (repo / "presentation").mkdir()
    (repo / "presentation" / "App.ts").write_text(
        "import { db } from '../domain/db';\n", encoding="utf-8"
    )
    (repo / "domain").mkdir()
    (repo / "domain" / "db.ts").write_text("export const db = {};\n", encoding="utf-8")
    result = analyze_repository(repo, MANIFEST, git_root=None)
    layer_violations = [v for v in result.violations if v.rule == "layer-violation"]
    assert layer_violations
    assert layer_violations[0].commit is None


def test_find_git_root_walks_up(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path, "base")
    deep = repo / "application" / "nested"
    deep.mkdir(parents=True)
    assert find_git_root(deep) == repo.resolve()


def test_source_path_from_evidence(tmp_path: Path) -> None:
    evidence = rf"{tmp_path}\src\App.ts:3 -> {tmp_path}\domain\db.ts (x)"
    path = source_path_from_evidence(evidence)
    assert path is not None
    assert path.name == "App.ts"
