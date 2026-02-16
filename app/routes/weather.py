from __future__ import annotations

from fastapi import APIRouter

from app.cache import cache

router = APIRouter(prefix="/api")


@router.get("/weather/today")
async def get_weather():
    return cache.get("weather")
