from __future__ import annotations

import time
from typing import Any


class Cache:
    """Thread-safe-enough in-memory cache for a single-worker async app."""

    def __init__(self) -> None:
        self._store: dict[str, dict[str, Any]] = {}

    def get(self, key: str) -> dict[str, Any]:
        entry = self._store.get(key)
        if entry is None:
            return {"data": None, "updated_at": None, "error": "not yet fetched"}
        return {**entry}

    def set(self, key: str, data: Any) -> None:
        self._store[key] = {
            "data": data,
            "updated_at": time.time(),
            "error": None,
        }

    def set_error(self, key: str, error: str) -> None:
        if key in self._store:
            self._store[key]["error"] = error
        else:
            self._store[key] = {
                "data": None,
                "updated_at": None,
                "error": error,
            }

    def keys(self) -> list[str]:
        return list(self._store.keys())


cache = Cache()
