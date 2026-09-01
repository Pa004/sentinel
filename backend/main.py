"""Sentinel — stateless architecture erosion detection API."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import settings
from backend.routers.analyses import router as analyses_router

app = FastAPI(
    title="Sentinel",
    description="Architecture erosion detection for GitHub repositories",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analyses_router)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
