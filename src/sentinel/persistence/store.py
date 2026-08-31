"""SQLite persistence layer for architecture analysis runs."""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

_SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    ts            TEXT    NOT NULL,
    repo_path     TEXT    NOT NULL,
    commit_sha    TEXT    NOT NULL,
    manifest_hash TEXT    NOT NULL,
    counts        TEXT    NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS violations (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id         INTEGER NOT NULL REFERENCES runs(id),
    kind           TEXT    NOT NULL,
    rule           TEXT    NOT NULL,
    severity       TEXT    NOT NULL DEFAULT 'warning',
    evidence       TEXT    NOT NULL,
    impact         TEXT    NOT NULL,
    recommendation TEXT    NOT NULL,
    commit_sha     TEXT    NOT NULL DEFAULT 'n/a'
);
"""


class ArchitectureStore:
    """Append-only store for analysis runs and their violations."""

    def __init__(self, path: Path) -> None:
        self._path = path
        self._conn: sqlite3.Connection | None = None

    def _connect(self) -> sqlite3.Connection:
        if self._conn is None:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            self._conn = sqlite3.connect(str(self._path))
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("PRAGMA foreign_keys=ON")
            self._conn.row_factory = sqlite3.Row
            self._conn.executescript(_SCHEMA)
        return self._conn

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def save_run(
        self,
        *,
        repo_path: Path,
        commit: str,
        manifest_hash: str,
        violations: list,
    ) -> int:
        """Insert a run with its violations. Returns the run id."""
        conn = self._connect()
        counts: dict[str, int] = {}
        for v in violations:
            counts[v.kind.value] = counts.get(v.kind.value, 0) + 1
        ts = datetime.now(UTC).isoformat()
        cur = conn.execute(
            "INSERT INTO runs (ts, repo_path, commit_sha, manifest_hash, counts) "
            "VALUES (?, ?, ?, ?, ?)",
            (ts, str(repo_path), commit, manifest_hash, json.dumps(counts)),
        )
        run_id = cur.lastrowid
        if run_id is None:
            raise RuntimeError("Failed to insert run into database")
        for v in violations:
            conn.execute(
                "INSERT INTO violations "
                "(run_id, kind, rule, severity, evidence, impact, "
                "recommendation, commit_sha) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    run_id,
                    v.kind.value,
                    v.rule,
                    v.severity.value,
                    v.evidence,
                    v.impact,
                    v.recommendation,
                    v.commit or "n/a",
                ),
            )
        conn.commit()
        return run_id

    def list_runs(self) -> list[dict]:
        conn = self._connect()
        rows = conn.execute("SELECT * FROM runs ORDER BY id").fetchall()
        return [dict(r) for r in rows]

    def get_run(self, run_id: int) -> dict | None:
        conn = self._connect()
        row = conn.execute("SELECT * FROM runs WHERE id = ?", (run_id,)).fetchone()
        if row is None:
            return None
        result = dict(row)
        vrows = conn.execute(
            "SELECT * FROM violations WHERE run_id = ? ORDER BY id", (run_id,)
        ).fetchall()
        result["violations"] = [dict(v) for v in vrows]
        return result

    def delete_run(self, run_id: int) -> bool:
        conn = self._connect()
        conn.execute("DELETE FROM violations WHERE run_id = ?", (run_id,))
        cur = conn.execute("DELETE FROM runs WHERE id = ?", (run_id,))
        conn.commit()
        return cur.rowcount > 0
