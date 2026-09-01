"""Analysis routes — trigger and query repository analyses."""

from __future__ import annotations

import json
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.dependencies import get_current_user
from backend.models import Analysis, User
from backend.services.analysis import run_analysis

router = APIRouter(prefix="/api/v1/analyses", tags=["analyses"])


class AnalysisRequest(BaseModel):
    repo_owner: str
    repo_name: str
    branch: str = "main"


class AnalysisResponse(BaseModel):
    id: int
    repo_owner: str
    repo_name: str
    branch: str
    status: str
    total_violations: int
    total_errors: int
    total_warnings: int
    total_info: int
    drift_score: float
    error_message: str | None
    created_at: datetime
    completed_at: datetime | None

    model_config = {"from_attributes": True}


class ViolationResponse(BaseModel):
    rule: str
    kind: str
    severity: str
    evidence: str
    components: list[str]
    impact: str
    recommendation: str
    commit_sha: str | None

    model_config = {"from_attributes": True}


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_analysis(
    request: AnalysisRequest,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AnalysisResponse:
    """Start a new repository analysis in the background."""
    analysis = Analysis(
        user_id=user.id,
        repo_owner=request.repo_owner,
        repo_name=request.repo_name,
        branch=request.branch,
        status="pending",
    )
    db.add(analysis)
    await db.commit()
    await db.refresh(analysis)

    background_tasks.add_task(run_analysis, analysis.id)

    return AnalysisResponse.model_validate(analysis)


@router.get("")
async def list_analyses(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[AnalysisResponse]:
    """List all analyses for the current user."""
    result = await db.execute(
        select(Analysis).where(Analysis.user_id == user.id).order_by(Analysis.created_at.desc())
    )
    analyses = result.scalars().all()
    return [AnalysisResponse.model_validate(a) for a in analyses]


@router.get("/{analysis_id}")
async def get_analysis(
    analysis_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get a single analysis with its violations."""
    result = await db.execute(
        select(Analysis).where(Analysis.id == analysis_id, Analysis.user_id == user.id)
    )
    analysis = result.scalar_one_or_none()

    if analysis is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis not found")

    violations = [
        ViolationResponse(
            rule=v.rule,
            kind=v.kind,
            severity=v.severity,
            evidence=v.evidence,
            components=json.loads(v.components) if v.components else [],
            impact=v.impact,
            recommendation=v.recommendation,
            commit_sha=v.commit_sha,
        )
        for v in analysis.violations
    ]

    metrics = None
    if analysis.metrics:
        metrics = {
            "nodes": analysis.metrics.nodes,
            "edges": analysis.metrics.edges,
            "cycles": analysis.metrics.cycles,
            "avg_coupling": analysis.metrics.avg_coupling,
        }

    return {
        "id": analysis.id,
        "repo_owner": analysis.repo_owner,
        "repo_name": analysis.repo_name,
        "branch": analysis.branch,
        "status": analysis.status,
        "total_violations": analysis.total_violations,
        "total_errors": analysis.total_errors,
        "total_warnings": analysis.total_warnings,
        "total_info": analysis.total_info,
        "drift_score": analysis.drift_score,
        "error_message": analysis.error_message,
        "created_at": analysis.created_at,
        "completed_at": analysis.completed_at,
        "violations": [v.model_dump() for v in violations],
        "metrics": metrics,
    }
