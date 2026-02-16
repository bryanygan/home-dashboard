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

    return {
        "status": data.get("status", "unknown"),
        "dns_queries_today": int(data.get("dns_queries_today", 0)),
        "ads_blocked_today": int(data.get("ads_blocked_today", 0)),
        "ads_percentage_today": float(data.get("ads_percentage_today", 0.0)),
        "ftl_running": data.get("status") == "enabled",
    }
