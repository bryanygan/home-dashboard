"""Open-Meteo weather + sunset client (no API key required)."""
from __future__ import annotations

import logging

import httpx

from app.config import settings

log = logging.getLogger(__name__)

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"


async def fetch_today(client: httpx.AsyncClient) -> dict:
    """Fetch today's weather summary + sunrise/sunset."""
    params = {
        "latitude": settings.WEATHER_LAT,
        "longitude": settings.WEATHER_LON,
        "current": "temperature_2m",
        "daily": (
            "temperature_2m_max,temperature_2m_min,"
            "precipitation_probability_max,sunrise,sunset"
        ),
        "timezone": "auto",
        "forecast_days": "1",
    }
    resp = await client.get(OPEN_METEO_URL, params=params)
    resp.raise_for_status()
    data = resp.json()

    daily = data.get("daily", {})
    current = data.get("current", {})

    return {
        "temperature_c": current.get("temperature_2m"),
        "high_c": daily.get("temperature_2m_max", [None])[0],
        "low_c": daily.get("temperature_2m_min", [None])[0],
        "precipitation_chance": daily.get(
            "precipitation_probability_max", [None]
        )[0],
        "sunrise": daily.get("sunrise", [None])[0],
        "sunset": daily.get("sunset", [None])[0],
    }
