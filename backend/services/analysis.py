"""Service to clone repos, run Sentinel analysis, and persist results."""

from __future__ import annotations

import json
import shutil
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from subprocess import run

from sqlalchemy import select

from backend.database import async_session
from backend.models import Analysis, Metrics, Violation


def _git(repo: Path, *args: str) -> None:
    """Run a git command in the given repo."""
    run(["git", "-C", str(repo), *args], check=True, capture_output=True)


async def run_analysis(analysis_id: int) -> None:
    """Clone a repo, run Sentinel, save results, and clean up."""
    async with async_session() as db:
        result = await db.execute(select(Analysis).where(Analysis.id == analysis_id))
        analysis = result.scalar_one_or_none()
        if analysis is None:
            return

        analysis.status = "running"
        await db.commit()

        tmp_dir = Path(tempfile.mkdtemp(prefix="sentinel_"))
        repo_dir = tmp_dir / "repo"

        try:
            # Shallow clone
            clone_url = f"https://github.com/{analysis.repo_owner}/{analysis.repo_name}.git"
            _git(
                tmp_dir, "clone", "--depth=1", "--branch", analysis.branch, clone_url, str(repo_dir)
            )

            # Find sentinel manifest
            manifest_path = repo_dir / "sentinel.yaml"
            manifest = None
            if manifest_path.exists():
                from sentinel.manifest.loader import load_manifest

                manifest = load_manifest(manifest_path)

            # Run analysis
            from sentinel.analyzers.coupling import coupling_scores
            from sentinel.violation_engine import analyze_repository

            git_root = repo_dir
            analysis_result = analyze_repository(repo_dir, manifest, git_root=git_root)

            # Compute metrics
            graph = analysis_result.graph
            nodes = len(graph.nodes())
            edges_count = sum(len(graph.dependencies_of(n)) for n in graph.nodes())
            coupling = coupling_scores(graph)
            avg_coupling = sum(coupling.values()) / len(coupling) if coupling else 0.0

            # Count cycles (from violations)
            cycles = sum(
                1 for v in analysis_result.violations if v.kind.value == "circular_dependency"
            )

            # Save violations
            for v in analysis_result.violations:
                db_violation = Violation(
                    analysis_id=analysis.id,
                    rule=v.rule,
                    kind=v.kind.value,
                    severity=v.severity.value,
                    evidence=v.evidence,
                    components=json.dumps(list(v.components)),
                    impact=v.impact,
                    recommendation=v.recommendation,
                    commit_sha=v.commit,
                )
                db.add(db_violation)

            # Save metrics
            db_metrics = Metrics(
                analysis_id=analysis.id,
                nodes=nodes,
                edges=edges_count,
                cycles=cycles,
                avg_coupling=round(avg_coupling, 2),
            )
            db.add(db_metrics)

            # Update analysis summary
            analysis.total_violations = len(analysis_result.violations)
            analysis.total_errors = sum(
                1 for v in analysis_result.violations if v.severity.value == "error"
            )
            analysis.total_warnings = sum(
                1 for v in analysis_result.violations if v.severity.value == "warning"
            )
            analysis.total_info = sum(
                1 for v in analysis_result.violations if v.severity.value == "info"
            )
            analysis.drift_score = analysis_result.drift
            analysis.status = "done"
            analysis.completed_at = datetime.now(UTC)

            await db.commit()

        except Exception as exc:
            analysis.status = "error"
            analysis.error_message = str(exc)[:500]
            analysis.completed_at = datetime.now(UTC)
            await db.commit()

        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)
