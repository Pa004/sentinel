"""GitHub repository listing routes."""

from __future__ import annotations

import httpx
from fastapi import APIRouter, Depends, HTTPException

from backend.dependencies import get_current_user
from backend.models import User

router = APIRouter(prefix="/api/v1/repos", tags=["repos"])


@router.get("")
async def list_repos(
    user: User = Depends(get_current_user),
) -> list[dict]:
    """List the authenticated user's public repositories via GitHub API."""
    if not user.access_token:
        raise HTTPException(
            status_code=400,
            detail="No GitHub access token. Please re-authenticate.",
        )

    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://api.github.com/user/repos",
            headers={"Authorization": f"Bearer {user.access_token}"},
            params={"type": "public", "per_page": 100, "sort": "updated"},
        )
        if resp.status_code != 200:
            raise HTTPException(status_code=502, detail="GitHub API error")
        repos = resp.json()

    return [
        {
            "name": r["name"],
            "full_name": r["full_name"],
            "owner": r["owner"]["login"],
            "description": r.get("description", ""),
            "language": r.get("language"),
            "default_branch": r.get("default_branch", "main"),
        }
        for r in repos
    ]
