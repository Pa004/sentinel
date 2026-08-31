"""Tests for SQLite persistence layer."""

from __future__ import annotations

from pathlib import Path

from sentinel.domain.manifest import ArchitectureManifest, Layer
from sentinel.persistence.store import ArchitectureStore
from sentinel.violation_engine import analyze_repository

MANIFEST = ArchitectureManifest(
    {
        "presentation": Layer("presentation", frozenset({"application"})),
        "application": Layer("application", frozenset({"domain"})),
        "domain": Layer("domain", frozenset()),
    }
)

MANIFEST2 = ArchitectureManifest(
    {
        "presentation": Layer("presentation", frozenset({"application", "domain"})),
        "application": Layer("application", frozenset()),
        "domain": Layer("domain", frozenset()),
    }
)


def _write_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    (repo / "presentation").mkdir(parents=True)
    (repo / "domain").mkdir()
    (repo / "presentation" / "App.ts").write_text(
        "import { db } from '../domain/db';\n", encoding="utf-8"
    )
    (repo / "domain" / "db.ts").write_text("export const db = {};\n", encoding="utf-8")
    return repo


def test_save_and_get_run(tmp_path: Path) -> None:
    repo = _write_repo(tmp_path)
    result = analyze_repository(repo, MANIFEST)
    store = ArchitectureStore(tmp_path / "test.db")
    try:
        run_id = store.save_run(
            repo_path=repo,
            commit="abc12345",
            manifest_hash="deadbeef",
            violations=result.violations,
        )
        assert run_id == 1
        run = store.get_run(run_id)
        assert run is not None
        assert run["commit_sha"] == "abc12345"
        assert run["manifest_hash"] == "deadbeef"
        assert len(run["violations"]) == len(result.violations)
    finally:
        store.close()


def test_list_runs_returns_all(tmp_path: Path) -> None:
    repo = _write_repo(tmp_path)
    result = analyze_repository(repo, MANIFEST)
    store = ArchitectureStore(tmp_path / "test.db")
    try:
        store.save_run(
            repo_path=repo, commit="aaa11111", manifest_hash="h1",
            violations=result.violations,
        )
        store.save_run(
            repo_path=repo, commit="bbb22222", manifest_hash="h2",
            violations=result.violations,
        )
        runs = store.list_runs()
        assert len(runs) == 2
        assert runs[0]["commit_sha"] == "aaa11111"
        assert runs[1]["commit_sha"] == "bbb22222"
    finally:
        store.close()


def test_counts_aggregated_per_kind(tmp_path: Path) -> None:
    repo = _write_repo(tmp_path)
    result = analyze_repository(repo, MANIFEST)
    store = ArchitectureStore(tmp_path / "test.db")
    try:
        run_id = store.save_run(
            repo_path=repo, commit="ccc33333", manifest_hash="h3", violations=result.violations
        )
        run = store.get_run(run_id)
        import json
        counts = json.loads(run["counts"])
        total = sum(counts.values())
        assert total == len(result.violations)
    finally:
        store.close()


def test_get_nonexistent_run_returns_none(tmp_path: Path) -> None:
    store = ArchitectureStore(tmp_path / "test.db")
    try:
        assert store.get_run(999) is None
    finally:
        store.close()


def test_delete_nonexistent_run_returns_false(tmp_path: Path) -> None:
    store = ArchitectureStore(tmp_path / "test.db")
    try:
        assert store.delete_run(999) is False
    finally:
        store.close()


def test_delete_run(tmp_path: Path) -> None:
    repo = _write_repo(tmp_path)
    result = analyze_repository(repo, MANIFEST)
    store = ArchitectureStore(tmp_path / "test.db")
    try:
        run_id = store.save_run(
            repo_path=repo, commit="ddd44444", manifest_hash="h4", violations=result.violations
        )
        assert store.delete_run(run_id) is True
        assert store.get_run(run_id) is None
        assert store.list_runs() == []
    finally:
        store.close()


def test_analyze_save_flag(tmp_path: Path) -> None:
    """Integration test: analyze_repository result can be persisted."""
    repo = _write_repo(tmp_path)
    manifest = tmp_path / "m.yaml"
    manifest.write_text(
        "layers:\n"
        "  presentation: { may_depend_on: [application] }\n"
        "  application: { may_depend_on: [domain] }\n"
        "  domain: {}\n",
        encoding="utf-8",
    )
    result = analyze_repository(repo, MANIFEST)
    db_path = tmp_path / ".sentinel" / "sentinel.db"
    store = ArchitectureStore(db_path)
    try:
        run_id = store.save_run(
            repo_path=repo, commit="eee55555", manifest_hash="h5", violations=result.violations
        )
        assert run_id == 1
        assert db_path.exists()
    finally:
        store.close()
