from __future__ import annotations

from fastapi import APIRouter

from app.cache import cache

router = APIRouter(prefix="/api")


@router.get("/todos")
async def get_todos():
    return cache.get("todos")
