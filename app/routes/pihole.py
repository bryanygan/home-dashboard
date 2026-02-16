from __future__ import annotations

from fastapi import APIRouter

from app.cache import cache

router = APIRouter(prefix="/api")


@router.get("/pihole")
async def get_pihole():
    return cache.get("pihole")
