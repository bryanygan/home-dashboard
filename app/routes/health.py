from __future__ import annotations

import time

from fastapi import APIRouter

from app.cache import cache

router = APIRouter()

_start_time = time.time()
_VERSION = "0.1.0"


@router.get("/healthz")
async def healthz():
    return {
        "status": "ok",
        "version": _VERSION,
        "uptime_seconds": round(time.time() - _start_time),
        "cache_timestamps": cache.timestamps(),
        "cache_errors": cache.errors(),
    }
