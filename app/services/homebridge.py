"""Homebridge UI X REST API client.

Handles authentication (token refresh on 401), accessory listing,
single-light toggle, and batch scene actions.
"""
from __future__ import annotations

import logging

import httpx

from app.config import settings

log = logging.getLogger(__name__)

# Module-level token — safe for single-worker async
_token: str | None = None


async def _login(client: httpx.AsyncClient) -> str:
    global _token
    resp = await client.post(
        f"{settings.HOMEBRIDGE_URL}/api/auth/login",
        json={
            "username": settings.HOMEBRIDGE_USERNAME,
            "password": settings.HOMEBRIDGE_PASSWORD,
        },
    )
    resp.raise_for_status()
    _token = resp.json()["access_token"]
    log.info("Authenticated with Homebridge")
    return _token


def _headers() -> dict[str, str]:
    if _token:
        return {"Authorization": f"Bearer {_token}"}
    return {}


async def _authed_get(client: httpx.AsyncClient, path: str):
    """GET with auto-reauth on 401."""
    resp = await client.get(
        f"{settings.HOMEBRIDGE_URL}{path}", headers=_headers()
    )
    if resp.status_code == 401:
        await _login(client)
        resp = await client.get(
            f"{settings.HOMEBRIDGE_URL}{path}", headers=_headers()
        )
    resp.raise_for_status()
    return resp.json()


async def _authed_put(client: httpx.AsyncClient, path: str, body: dict):
    """PUT with auto-reauth on 401."""
    resp = await client.put(
        f"{settings.HOMEBRIDGE_URL}{path}", json=body, headers=_headers()
    )
    if resp.status_code == 401:
        await _login(client)
        resp = await client.put(
            f"{settings.HOMEBRIDGE_URL}{path}", json=body, headers=_headers()
        )
    resp.raise_for_status()
    return resp.json() if resp.content else None


# ---- Public API --------------------------------------------------------


async def fetch_accessories(client: httpx.AsyncClient) -> list[dict]:
    """Return simplified list of light-type accessories."""
    raw = await _authed_get(client, "/api/accessories")
    lights: list[dict] = []
    for acc in raw:
        stype = acc.get("type", "")
        if stype not in ("Lightbulb", "Switch", "Outlet"):
            continue
        values = acc.get("values", {})
        lights.append(
            {
                "uniqueId": acc.get("uniqueId"),
                "name": acc.get(
                    "serviceName",
                    acc.get("accessoryInformation", {}).get("Name", "Unknown"),
                ),
                "type": stype,
                "on": bool(values.get("On", False)),
                "brightness": values.get("Brightness"),
                "room": acc.get("instance", {}).get("name"),
            }
        )
    return lights


async def toggle_light(client: httpx.AsyncClient, unique_id: str) -> dict:
    """Toggle a single light and return its new state."""
    raw = await _authed_get(client, "/api/accessories")
    target = None
    for acc in raw:
        if acc.get("uniqueId") == unique_id:
            target = acc
            break
    if not target:
        raise ValueError(f"Accessory {unique_id} not found")

    current_on = target.get("values", {}).get("On", False)
    new_val = not current_on

    await _authed_put(
        client,
        f"/api/accessories/{unique_id}",
        {"characteristicType": "On", "value": new_val},
    )

    return {
        "uniqueId": unique_id,
        "name": target.get("serviceName", "Unknown"),
        "on": new_val,
    }


async def set_lights(
    client: httpx.AsyncClient, unique_ids: list[str], *, on: bool
) -> dict:
    """Set a batch of lights on or off. Returns affected count + errors."""
    errors: list[dict] = []
    affected = 0
    for uid in unique_ids:
        try:
            await _authed_put(
                client,
                f"/api/accessories/{uid}",
                {"characteristicType": "On", "value": on},
            )
            affected += 1
        except Exception as e:
            log.warning("Failed to set light %s to %s: %s", uid, on, e)
            errors.append({"uniqueId": uid, "error": str(e)})
    return {"affected": affected, "errors": errors}
