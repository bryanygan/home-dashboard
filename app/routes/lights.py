from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from app.cache import cache
from app.config import settings
from app.services import homebridge

router = APIRouter(prefix="/api")


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
    client = request.app.state.http
    ids = settings.SCENE_ALL_ON_IDS
    if not ids:
        raise HTTPException(
            status_code=400, detail="SCENE_ALL_ON_IDS not configured"
        )
    result = await homebridge.set_lights(client, ids, on=True)
    return {"scene": "all_on", **result}


@router.post("/scenes/movie")
async def scene_movie(request: Request):
    client = request.app.state.http
    ids = settings.SCENE_MOVIE_OFF_IDS
    if not ids:
        raise HTTPException(
            status_code=400, detail="SCENE_MOVIE_OFF_IDS not configured"
        )
    result = await homebridge.set_lights(client, ids, on=False)
    return {"scene": "movie", **result}
