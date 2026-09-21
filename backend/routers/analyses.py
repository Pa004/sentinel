"""Single endpoint: analyze a GitHub repository."""

from __future__ import annotations

import asyncio
import logging
import re

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, field_validator

from backend.services.analysis import run_analysis

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["analyze"])

_GITHUB_URL_RE = re.compile(r"^(https?://github\.com/)?[\w.-]+/[\w.-]+(/.*)?$")
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
                "repo_url must be a GitHub URL (https://github.com/owner/repo) or owner/repo format"
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
    try:
        await asyncio.wait_for(_semaphore.acquire(), timeout=0)
    except TimeoutError:
        raise HTTPException(
            status_code=429,
            detail="Too many concurrent analyses — try again in a moment",
        ) from None
    try:
        result = await run_analysis(request.repo_url, request.branch)
        return result
    except TimeoutError as exc:
        raise HTTPException(status_code=504, detail=str(exc)) from exc
    except (ValueError, FileNotFoundError) as exc:
        logger.warning("analysis input error: %s", exc)
        raise HTTPException(status_code=400, detail=str(exc)[:200]) from exc
    except Exception:
        logger.exception("analysis failed for %s", request.repo_url)
        raise HTTPException(status_code=500, detail="Analysis failed — check server logs") from None
    finally:
        _semaphore.release()
