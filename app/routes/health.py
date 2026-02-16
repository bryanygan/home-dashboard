from __future__ import annotations

import time

from fastapi import APIRouter

from app.cache import cache

router = APIRouter()

_start_time = time.time()


@router.get("/healthz")
async def healthz():
    return {
        "status": "ok",
        "uptime_seconds": round(time.time() - _start_time),
        "cache_keys": cache.keys(),
    }
