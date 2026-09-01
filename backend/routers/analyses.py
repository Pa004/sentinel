"""Single endpoint: analyze a GitHub repository."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.services.analysis import run_analysis

router = APIRouter(prefix="/api", tags=["analyze"])


class AnalyzeRequest(BaseModel):
    repo_url: str
    branch: str = "main"


@router.post("/analyze")
async def analyze(request: AnalyzeRequest) -> dict:
    """Clone a repo, run Sentinel analysis, return results."""
    try:
        result = await run_analysis(request.repo_url, request.branch)
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)[:500]) from exc
