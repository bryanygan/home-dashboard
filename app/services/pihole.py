"""Pi-hole admin API client (v5 /admin/api.php)."""
from __future__ import annotations

import logging

import httpx

from app.config import settings

log = logging.getLogger(__name__)


async def fetch_status(client: httpx.AsyncClient) -> dict:
    """Fetch Pi-hole summary stats."""
    url = f"{settings.PIHOLE_URL}/admin/api.php"
    params: dict[str, str] = {"summary": ""}
    if settings.PIHOLE_API_TOKEN:
        params["auth"] = settings.PIHOLE_API_TOKEN

    resp = await client.get(url, params=params)
    resp.raise_for_status()
    data = resp.json()

    # gravity_last_updated comes as an object with absolute/relative keys
    gravity = data.get("gravity_last_updated", {})
    if isinstance(gravity, dict):
        gravity_ts = gravity.get("absolute")
    else:
        gravity_ts = None

    return {
        "status": data.get("status", "unknown"),
        "queries_today": int(data.get("dns_queries_today", 0)),
        "blocked_today": int(data.get("ads_blocked_today", 0)),
        "percent_blocked": float(data.get("ads_percentage_today", 0.0)),
        "gravity_last_updated": gravity_ts,
    }
