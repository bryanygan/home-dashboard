"""Read a local todos JSON file exported by Apple Shortcuts."""
from __future__ import annotations

import json
import logging
import os

from app.config import settings

log = logging.getLogger(__name__)


async def read_todos() -> dict:
    """Read and validate the todos JSON file.

    Accepts either a bare list or {"items": [...]}.
    Returns {"items": [...], "count": N} or flags file_missing.
    """
    path = settings.TODOS_FILE_PATH

    if not os.path.exists(path):
        return {"items": [], "count": 0, "file_missing": True}

    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    if isinstance(raw, list):
        items = raw
    elif isinstance(raw, dict) and "items" in raw:
        items = raw["items"]
    else:
        raise ValueError(
            'Unexpected todos JSON format: expected list or {"items": [...]}'
        )

    return {"items": items, "count": len(items)}
