"""Read a local todos JSON file exported by Apple Shortcuts."""
from __future__ import annotations

import json
import logging
import os

from app.config import settings

log = logging.getLogger(__name__)

# Track file mtime to skip redundant reads
_last_mtime: float = 0.0
_last_result: dict | None = None


async def read_todos() -> dict:
    """Read and validate the todos JSON file.

    Only re-reads from disk when the file's mtime has changed.
    Validates schema: items must have "text" and "checked" fields.
    """
    global _last_mtime, _last_result

    path = settings.TODOS_FILE_PATH

    if not os.path.exists(path):
        _last_mtime = 0.0
        _last_result = None
        return {"items": [], "count": 0, "error": "File not found: " + path}

    current_mtime = os.path.getmtime(path)
    if current_mtime == _last_mtime and _last_result is not None:
        return _last_result

    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    # Accept either a bare list or {"items": [...], "updated_at": "..."}
    updated_at = None
    if isinstance(raw, list):
        items = raw
    elif isinstance(raw, dict) and "items" in raw:
        items = raw["items"]
        updated_at = raw.get("updated_at")
    else:
        raise ValueError(
            'Unexpected todos JSON format: expected list or {"items": [...]}'
        )

    # Validate each item has "text" and "checked"
    validated: list[dict] = []
    for i, item in enumerate(items):
        if not isinstance(item, dict):
            log.warning("Todo item %d is not an object, skipping", i)
            continue
        if "text" not in item:
            log.warning("Todo item %d missing 'text' field, skipping", i)
            continue
        validated.append({
            "text": item["text"],
            "checked": bool(item.get("checked", False)),
        })

    result = {
        "items": validated,
        "count": len(validated),
        "updated_at": updated_at,
    }

    _last_mtime = current_mtime
    _last_result = result
    return result
