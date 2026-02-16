from __future__ import annotations

from fastapi import APIRouter

from app.cache import cache

router = APIRouter(prefix="/api")


@router.get("/network")
async def get_network():
    return cache.get("network")
