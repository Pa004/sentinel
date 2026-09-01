"""GitHub OAuth authentication routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth import create_access_token, oauth
from backend.config import settings
from backend.database import get_db
from backend.models import User

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/github")
async def github_login(request: Request) -> dict:
    """Redirect to GitHub OAuth authorization page."""
    redirect_uri = f"{settings.frontend_url}/auth/callback"
    return await oauth.github.authorize_redirect(request, redirect_uri)


@router.get("/github/callback")
async def github_callback(request: Request, db: AsyncSession = Depends(get_db)) -> dict:
    """Handle GitHub OAuth callback, create/update user, return JWT."""
    token = await oauth.github.authorize_access_token(request)
    user_info = await oauth.github.get("user", token=token)
    gh_user = user_info.json()

    github_id = gh_user["id"]
    username = gh_user["login"]
    avatar_url = gh_user.get("avatar_url", "")

    result = await db.execute(select(User).where(User.github_id == github_id))
    user = result.scalar_one_or_none()

    if user is None:
        user = User(
            github_id=github_id,
            username=username,
            avatar_url=avatar_url,
            access_token=token.get("access_token"),
        )
        db.add(user)
    else:
        user.username = username
        user.avatar_url = avatar_url
        user.access_token = token.get("access_token")

    await db.commit()
    await db.refresh(user)

    jwt_token = create_access_token(github_id, username)
    return {"access_token": jwt_token, "token_type": "bearer"}
