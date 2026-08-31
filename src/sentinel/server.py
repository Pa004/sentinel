"""Lightweight stdlib HTTP server for Sentinel analysis reports."""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from sentinel.persistence.store import ArchitectureStore


def _json_response(handler: BaseHTTPRequestHandler, payload: dict, status: int) -> None:
    body = json.dumps(payload, indent=2).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Cache-Control", "no-store")
    handler.end_headers()
    handler.wfile.write(body)


def _html_response(handler: BaseHTTPRequestHandler, html: str) -> None:
    body = html.encode("utf-8")
    handler.send_response(200)
    handler.send_header("Content-Type", "text/html; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def _run_list_item(row: dict) -> dict[str, Any]:
    return {
        "id": row["id"],
        "commit_sha": row["commit_sha"],
        "ts": row["ts"],
        "repo_path": row["repo_path"],
        "counts": json.loads(row["counts"]) if row.get("counts") else {},
    }


def _violation_dict(v: dict) -> dict[str, Any]:
    return {
        "rule": v["rule"],
        "kind": v["kind"],
        "severity": v["severity"],
        "evidence": v["evidence"],
        "impact": v["impact"],
        "recommendation": v["recommendation"],
        "commit_sha": v.get("commit_sha", "n/a"),
    }


class SentinelHandler(BaseHTTPRequestHandler):
    """Routes requests to JSON API endpoints or the HTML report."""

    repo: Path
    manifest_path: Path
    db: Path
    react_dist: Path | None = None

    def _store(self) -> ArchitectureStore:
        return ArchitectureStore(self.db)

    def _report_html(self) -> str:
        from sentinel.domain.manifest import ArchitectureManifest
        from sentinel.manifest.loader import load_manifest
        from sentinel.reports.html_report import render_report
        from sentinel.violation_engine import analyze_repository

        man: ArchitectureManifest = load_manifest(self.manifest_path)
        result = analyze_repository(self.repo, man, git_root=self.repo)
        trend_data: list[dict] = []
        try:
            from sentinel.trend import build_trend

            points = build_trend(self.repo, man)
            trend_data = [
                {
                    "commit": p.commit,
                    "counts": {k.value: v for k, v in p.counts.items()},
                    "drift": p.drift,
                }
                for p in points
            ]
        except (RuntimeError, OSError):
            pass
        meta = (
            f"Repo: {self.repo}"
            f" | Violations: {len(result.violations)}"
        )
        return render_report(
            violations=result.violations,
            trend_data=trend_data,
            meta=meta,
            drift=result.drift,
        )

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"

        if path == "/":
            self._handle_index()
        elif path == "/api/runs":
            self._handle_runs_list()
        elif path.startswith("/api/runs/"):
            self._handle_run_detail(path)
        elif path == "/api/report.json":
            self._handle_report_json()
        elif path == "/favicon.ico":
            self.send_response(204)
            self.send_header("Content-Length", "0")
            self.end_headers()
        elif self.react_dist is not None:
            self._serve_static(path)
        else:
            _json_response(self, {"error": "Not found"}, 404)

    def _handle_index(self) -> None:
        if self.react_dist is not None:
            self._serve_static("/")
            return
        try:
            html = self._report_html()
            _html_response(self, html)
        except Exception as exc:  # noqa: BLE001
            _json_response(self, {"error": f"Failed to generate report: {exc}"}, 500)

    _MIME_TYPES: dict[str, str] = {
        ".html": "text/html; charset=utf-8",
        ".js": "application/javascript; charset=utf-8",
        ".css": "text/css; charset=utf-8",
        ".json": "application/json; charset=utf-8",
        ".png": "image/png",
        ".svg": "image/svg+xml",
        ".ico": "image/x-icon",
    }

    def _serve_static(self, path: str) -> None:
        """Serve a file from react_dist, falling back to index.html for SPA routing."""
        if self.react_dist is None:
            _json_response(self, {"error": "React dist not configured"}, 500)
            return
        file_path = self.react_dist / path.lstrip("/")
        if not file_path.is_file():
            # SPA fallback: serve index.html for client-side routing
            file_path = self.react_dist / "index.html"
        if not file_path.is_file():
            _json_response(self, {"error": "Not found"}, 404)
            return
        suffix = file_path.suffix
        content_type = self._MIME_TYPES.get(suffix, "application/octet-stream")
        try:
            body = file_path.read_bytes()
        except OSError as exc:
            _json_response(self, {"error": str(exc)}, 500)
            return
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _handle_runs_list(self) -> None:
        if not self.db.exists():
            _json_response(self, [], 200)
            return
        try:
            store = self._store()
            try:
                runs = store.list_runs()
            finally:
                store.close()
            _json_response(self, [_run_list_item(r) for r in runs], 200)
        except Exception as exc:  # noqa: BLE001
            _json_response(self, {"error": str(exc)}, 500)

    def _handle_run_detail(self, path: str) -> None:
        id_str = path.split("/")[-1]
        if not self.db.exists():
            _json_response(self, {"error": "No database found"}, 404)
            return
        try:
            run_id = int(id_str)
        except ValueError:
            _json_response(self, {"error": "Invalid run id"}, 400)
            return
        try:
            store = self._store()
            try:
                run = store.get_run(run_id)
            finally:
                store.close()
            if run is None:
                _json_response(self, {"error": f"Run {run_id} not found"}, 404)
                return
            violations = [_violation_dict(v) for v in run.pop("violations", [])]
            result = _run_list_item(run)
            result["violations"] = violations
            _json_response(self, result, 200)
        except Exception as exc:  # noqa: BLE001
            _json_response(self, {"error": str(exc)}, 500)

    def _handle_report_json(self) -> None:
        try:
            from sentinel.domain.manifest import ArchitectureManifest
            from sentinel.manifest.loader import load_manifest
            from sentinel.reports.json import serialize
            from sentinel.violation_engine import analyze_repository

            man: ArchitectureManifest = load_manifest(self.manifest_path)
            result = analyze_repository(self.repo, man, git_root=self.repo)
            body = serialize(result).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)
        except Exception as exc:  # noqa: BLE001
            _json_response(self, {"error": str(exc)}, 500)

    def log_message(self, fmt: str, *args: object) -> None:
        """Suppress default stderr logging for clean server output."""
        pass


def run_server(
    repo: Path,
    manifest_path: Path,
    host: str,
    port: int,
    db: Path,
    react: bool = False,
) -> None:
    """Start the Sentinel HTTP server."""
    SentinelHandler.repo = repo
    SentinelHandler.manifest_path = manifest_path
    SentinelHandler.db = db
    if react:
        dist = repo.parent / "frontend" / "dist"
        if not dist.is_dir():
            print(f"Warning: --react specified but {dist} does not exist.")
            print("Run 'cd frontend && npm install && npm run build' first.")
            SentinelHandler.react_dist = None
        else:
            SentinelHandler.react_dist = dist
            print(f"Serving React dashboard from {dist}")
    else:
        SentinelHandler.react_dist = None

    with ThreadingHTTPServer((host, port), SentinelHandler) as server:
        print(f"Sentinel server running at http://{host}:{port}")
        print("Press Ctrl+C to stop.")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nStopped.")
