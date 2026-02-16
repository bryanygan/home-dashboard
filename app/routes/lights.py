from __future__ import annotations

import asyncio
import time

from fastapi import APIRouter, HTTPException, Request

from app.cache import cache
from app.config import settings
from app.services import homebridge

router = APIRouter(prefix="/api")

# Simple per-scene cooldown tracker
_scene_last_called: dict[str, float] = {}
_SCENE_COOLDOWN = 3.0  # seconds


def _check_cooldown(scene: str) -> bool:
    """Return True if the scene can fire, False if still in cooldown."""
    now = time.time()
    last = _scene_last_called.get(scene, 0.0)
    if now - last < _SCENE_COOLDOWN:
        return False
    _scene_last_called[scene] = now
    return True


async def _delayed_refresh(client, delay: float = 2.0) -> None:
    """Re-sync lights cache shortly after a scene action."""
    await asyncio.sleep(delay)
    try:
        data = await homebridge.fetch_accessories(client)
        cache.set("lights", data)
    except Exception:
        pass  # next regular cycle will catch up


@router.get("/lights")
async def get_lights():
    return cache.get("lights")


@router.post("/lights/{unique_id}/toggle")
async def toggle_light(unique_id: str, request: Request):
    client = request.app.state.http
    try:
        result = await homebridge.toggle_light(client, unique_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.post("/scenes/all_on")
async def scene_all_on(request: Request):
    if not _check_cooldown("all_on"):
        raise HTTPException(status_code=429, detail="Scene called too recently, try again in a few seconds")
    client = request.app.state.http
    ids = settings.SCENE_ALL_ON_IDS
    if not ids:
        raise HTTPException(
            status_code=400, detail="SCENE_ALL_ON_IDS not configured"
        )
    result = await homebridge.set_lights(client, ids, on=True)
    asyncio.create_task(_delayed_refresh(client))
    return {"scene": "all_on", **result}


@router.post("/scenes/movie")
async def scene_movie(request: Request):
    if not _check_cooldown("movie"):
        raise HTTPException(status_code=429, detail="Scene called too recently, try again in a few seconds")
    client = request.app.state.http

    off_ids = settings.SCENE_MOVIE_OFF_IDS
    on_ids = settings.SCENE_MOVIE_ON_IDS
    if not off_ids and not on_ids:
        raise HTTPException(
            status_code=400, detail="SCENE_MOVIE_OFF_IDS / SCENE_MOVIE_ON_IDS not configured"
        )

    # Turn off the movie-off lights, turn on the movie-on lights
    all_success: list[str] = []
    all_failed: list[str] = []
    all_errors: list[dict] = []

    if off_ids:
        off_result = await homebridge.set_lights(client, off_ids, on=False)
        all_success.extend(off_result["success_ids"])
        all_failed.extend(off_result["failed_ids"])
        all_errors.extend(off_result["errors"])

    if on_ids:
        on_result = await homebridge.set_lights(client, on_ids, on=True)
        all_success.extend(on_result["success_ids"])
        all_failed.extend(on_result["failed_ids"])
        all_errors.extend(on_result["errors"])

    asyncio.create_task(_delayed_refresh(client))
    return {
        "scene": "movie",
        "success_ids": all_success,
        "failed_ids": all_failed,
        "errors": all_errors,
        "timestamp": time.time(),
    }
