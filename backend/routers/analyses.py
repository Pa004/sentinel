"""Single endpoint: analyze a GitHub repository."""

from __future__ import annotations

import asyncio
import re

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, field_validator

from backend.services.analysis import run_analysis

router = APIRouter(prefix="/api", tags=["analyze"])

_GITHUB_URL_RE = re.compile(
    r"^(https?://github\.com/)?[\w.-]+/[\w.-]+(/.*)?$"
)
_BRANCH_RE = re.compile(r"^[\w./-]+$")

MAX_CONCURRENT_ANALYSES = 3
_semaphore = asyncio.Semaphore(MAX_CONCURRENT_ANALYSES)


class AnalyzeRequest(BaseModel):
    repo_url: str
    branch: str = "main"

    @field_validator("repo_url")
    @classmethod
    def validate_repo_url(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("repo_url is required")
        if not _GITHUB_URL_RE.match(v):
            raise ValueError(
                "repo_url must be a GitHub URL (https://github.com/owner/repo) "
                "or owner/repo format"
            )
        if len(v) > 500:
            raise ValueError("repo_url is too long (max 500 characters)")
        return v

    @field_validator("branch")
    @classmethod
    def validate_branch(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("branch is required")
        if not _BRANCH_RE.match(v):
            raise ValueError(
                "branch name contains invalid characters — "
                "only alphanumeric, dots, hyphens, slashes, and underscores are allowed"
            )
        if len(v) > 200:
            raise ValueError("branch name is too long (max 200 characters)")
        return v


@router.post("/analyze")
async def analyze(request: AnalyzeRequest) -> dict:
    """Clone a repo, run Sentinel analysis, return results."""
    if _semaphore.locked():
        raise HTTPException(
            status_code=429,
            detail="Too many concurrent analyses — try again in a moment",
        )
    try:
        async with _semaphore:
            result = await run_analysis(request.repo_url, request.branch)
            return result
    except TimeoutError as exc:
        raise HTTPException(status_code=504, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)[:500]) from exc
