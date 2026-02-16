from __future__ import annotations

from fastapi import HTTPException, Request

from app.config import settings


async def verify_api_key(request: Request) -> None:
    """Dependency that enforces X-API-KEY when SMARTPANEL_API_KEY is set."""
    if not settings.API_KEY:
        return  # auth disabled
    # Always allow healthz without auth
    if request.url.path == "/healthz":
        return
    key = request.headers.get("X-API-KEY", "")
    if key != settings.API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
