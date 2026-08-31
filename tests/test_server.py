"""Tests for the Sentinel lightweight HTTP server."""

from __future__ import annotations

import json
import threading
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

import pytest

from sentinel.persistence.store import ArchitectureStore
from sentinel.server import SentinelHandler

FIXTURES = Path(__file__).parent / "fixtures"
MANIFEST = FIXTURES / "manifest.yaml"
GOOD_REPO = FIXTURES / "GOOD"
BAD_REPO = FIXTURES / "BAD"


def _start_server(db_path: Path, repo: Path = GOOD_REPO) -> tuple[ThreadingHTTPServer, int]:
    """Start a Sentinel server on an ephemeral port and return it."""
    SentinelHandler.repo = repo
    SentinelHandler.manifest_path = MANIFEST
    SentinelHandler.db = db_path
    server = ThreadingHTTPServer(("127.0.0.1", 0), SentinelHandler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, port


def _get(port: int, path: str) -> tuple[int, str]:
    """Hit a local endpoint and return (status_code, body)."""
    url = f"http://127.0.0.1:{port}{path}"
    try:
        with urllib.request.urlopen(url, timeout=30) as resp:
            return resp.status, resp.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8")


def _seed_db(db_path: Path, repo: Path = BAD_REPO) -> None:
    """Save a run so the DB has data."""
    from sentinel.domain.manifest import ArchitectureManifest
    from sentinel.manifest.loader import load_manifest
    from sentinel.violation_engine import analyze_repository

    man: ArchitectureManifest = load_manifest(MANIFEST)
    result = analyze_repository(repo, man, git_root=repo)
    store = ArchitectureStore(db_path)
    try:
        store.save_run(
            repo_path=repo,
            commit="deadbeef12345678",
            manifest_hash="abc123def456",
            violations=result.violations,
        )
    finally:
        store.close()


@pytest.fixture()
def db_empty(tmp_path: Path) -> Path:
    return tmp_path / "test.db"


@pytest.fixture()
def db_seeded(tmp_path: Path) -> Path:
    db_path = tmp_path / "test.db"
    _seed_db(db_path)
    return db_path


@pytest.fixture()
def server_empty(db_empty: Path):
    srv, port = _start_server(db_empty)
    yield port
    srv.shutdown()


@pytest.fixture()
def server_seeded(db_seeded: Path):
    srv, port = _start_server(db_seeded)
    yield port
    srv.shutdown()


@pytest.fixture()
def server_bad(db_seeded: Path):
    srv, port = _start_server(db_seeded, repo=BAD_REPO)
    yield port
    srv.shutdown()


class TestIndex:
    def test_returns_html(self, server_empty: int) -> None:
        status, body = _get(server_empty, "/")
        assert status == 200
        assert 'id="violationsTable"' in body

    def test_contains_doctype(self, server_empty: int) -> None:
        status, body = _get(server_empty, "/")
        assert status == 200
        assert "<!DOCTYPE html>" in body


class TestApiRuns:
    def test_empty_database(self, server_empty: int) -> None:
        status, body = _get(server_empty, "/api/runs")
        assert status == 200
        data = json.loads(body)
        assert data == []

    def test_no_database_file(self, server_empty: int, db_empty: Path) -> None:
        db_empty.unlink(missing_ok=True)
        status, body = _get(server_empty, "/api/runs")
        assert status == 200
        data = json.loads(body)
        assert data == []

    def test_seeded_database(self, server_seeded: int) -> None:
        status, body = _get(server_seeded, "/api/runs")
        assert status == 200
        data = json.loads(body)
        assert len(data) == 1
        run = data[0]
        assert run["id"] == 1
        assert run["commit_sha"] == "deadbeef12345678"
        assert isinstance(run["counts"], dict)


class TestApiRunDetail:
    def test_existing_run(self, server_seeded: int) -> None:
        status, body = _get(server_seeded, "/api/runs/1")
        assert status == 200
        data = json.loads(body)
        assert data["id"] == 1
        assert isinstance(data["violations"], list)

    def test_violation_shape(self, server_seeded: int) -> None:
        status, body = _get(server_seeded, "/api/runs/1")
        assert status == 200
        data = json.loads(body)
        if data["violations"]:
            v = data["violations"][0]
            for key in ("rule", "kind", "severity", "evidence", "impact", "recommendation"):
                assert key in v

    def test_nonexistent_run(self, server_seeded: int) -> None:
        status, body = _get(server_seeded, "/api/runs/999")
        assert status == 404
        data = json.loads(body)
        assert "error" in data

    def test_invalid_id(self, server_seeded: int) -> None:
        status, body = _get(server_seeded, "/api/runs/abc")
        assert status == 400
        data = json.loads(body)
        assert "error" in data


class TestApiReportJson:
    def test_returns_analysis(self, server_empty: int) -> None:
        status, body = _get(server_empty, "/api/report.json")
        assert status == 200
        data = json.loads(body)
        assert "violations" in data
        assert "total" in data
        assert "drift" in data


class TestMisc:
    def test_404_unknown_path(self, server_empty: int) -> None:
        status, body = _get(server_empty, "/nope")
        assert status == 404
        data = json.loads(body)
        assert "error" in data

    def test_favicon_204(self, server_empty: int) -> None:
        status, _ = _get(server_empty, "/favicon.ico")
        assert status == 204

    def test_bad_repo_serves_report(self, server_bad: int) -> None:
        status, body = _get(server_bad, "/")
        assert status == 200
        assert "violationsTable" in body
