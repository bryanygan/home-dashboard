from __future__ import annotations

import time
from typing import Any

from pydantic import BaseModel


class CacheEntry(BaseModel):
    """Typed snapshot for a single cache key."""

    data: Any = None
    updated_at: float | None = None
    error: str | None = None


class Cache:
    """In-memory cache for a single-worker async app.

    Every key stores a ``CacheEntry``.  GET endpoints return the model
    dict directly so FastAPI serialises it with no extra work.
    """

    def __init__(self) -> None:
        self._store: dict[str, CacheEntry] = {}

    def get(self, key: str) -> dict[str, Any]:
        entry = self._store.get(key)
        if entry is None:
            return CacheEntry(error="not yet fetched").model_dump()
        return entry.model_dump()

    def set(self, key: str, data: Any) -> None:
        self._store[key] = CacheEntry(
            data=data,
            updated_at=time.time(),
            error=None,
        )

    def set_error(self, key: str, error: str) -> None:
        if key in self._store:
            self._store[key].error = error
        else:
            self._store[key] = CacheEntry(error=error)

    def keys(self) -> list[str]:
        return list(self._store.keys())

    def timestamps(self) -> dict[str, float | None]:
        """Return {key: updated_at} for every cached service."""
        return {k: v.updated_at for k, v in self._store.items()}

    def errors(self) -> dict[str, str | None]:
        """Return {key: error} for every cached service."""
        return {k: v.error for k, v in self._store.items()}


cache = Cache()
