"""Clone a repo, run Sentinel analysis, return results. No DB."""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path
from subprocess import run
from urllib.parse import urlparse


def _git(repo: Path, *args: str) -> None:
    """Run a git command in the given repo."""
    run(["git", "-C", str(repo), *args], check=True, capture_output=True)


def _parse_repo_url(url: str) -> tuple[str, str]:
    """Extract owner and name from a GitHub URL or 'owner/name' string."""
    url = url.strip().rstrip("/")
    url = url.removesuffix(".git")

    parsed = urlparse(url)
    if parsed.path:
        parts = parsed.path.strip("/").split("/")
        if len(parts) >= 2:
            return parts[0], parts[1]

    if "/" in url:
        parts = url.split("/")
        return parts[-2], parts[-1]

    raise ValueError(f"Cannot parse repo URL: {url}")


async def run_analysis(repo_url: str, branch: str = "main") -> dict:
    """Clone repo, run analysis, return results dict."""
    owner, name = _parse_repo_url(repo_url)
    clone_url = f"https://github.com/{owner}/{name}.git"

    tmp_dir = Path(tempfile.mkdtemp(prefix="sentinel_"))
    repo_dir = tmp_dir / "repo"

    try:
        _git(tmp_dir, "clone", "--depth=1", "--branch", branch, clone_url, str(repo_dir))

        manifest_path = repo_dir / "sentinel.yaml"
        manifest = None
        if manifest_path.exists():
            from sentinel.manifest.loader import load_manifest

            manifest = load_manifest(manifest_path)

        from sentinel.analyzers.coupling import coupling_scores
        from sentinel.violation_engine import analyze_repository

        analysis_result = analyze_repository(repo_dir, manifest, git_root=repo_dir)

        graph = analysis_result.graph
        nodes = len(graph.nodes())
        edges_count = sum(len(graph.dependencies_of(n)) for n in graph.nodes())
        coupling = coupling_scores(graph)
        avg_coupling = sum(coupling.values()) / len(coupling) if coupling else 0.0

        cycles = sum(1 for v in analysis_result.violations if v.kind.value == "circular_dependency")

        violations = [
            {
                "rule": v.rule,
                "kind": v.kind.value,
                "severity": v.severity.value,
                "evidence": v.evidence,
                "components": list(v.components),
                "impact": v.impact,
                "recommendation": v.recommendation,
                "commit_sha": v.commit,
            }
            for v in analysis_result.violations
        ]

        total = len(violations)
        errors = sum(1 for v in violations if v["severity"] == "error")
        warnings = sum(1 for v in violations if v["severity"] == "warning")
        info = sum(1 for v in violations if v["severity"] == "info")

        return {
            "repo_owner": owner,
            "repo_name": name,
            "branch": branch,
            "status": "done",
            "total_violations": total,
            "total_errors": errors,
            "total_warnings": warnings,
            "total_info": info,
            "drift_score": analysis_result.drift,
            "violations": violations,
            "metrics": {
                "nodes": nodes,
                "edges": edges_count,
                "cycles": cycles,
                "avg_coupling": round(avg_coupling, 2),
            },
        }

    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)
