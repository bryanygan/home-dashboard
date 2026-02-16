"""Open-Meteo weather + sunset client (no API key required)."""
from __future__ import annotations

import logging

import httpx

from app.config import settings

log = logging.getLogger(__name__)

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"


def c_to_f(celsius: float | None) -> float | None:
    """Convert Celsius to Fahrenheit. Returns None if input is None."""
    if celsius is None:
        return None
    return round(celsius * 9 / 5 + 32, 1)


async def fetch_today(client: httpx.AsyncClient) -> dict:
    """Fetch today's weather summary + sunrise/sunset in Fahrenheit."""
    params = {
        "latitude": settings.WEATHER_LAT,
        "longitude": settings.WEATHER_LON,
        "current": "temperature_2m",
        "daily": (
            "temperature_2m_max,temperature_2m_min,"
            "precipitation_probability_max,sunrise,sunset"
        ),
        "timezone": settings.TZ,
        "forecast_days": "1",
    }
    resp = await client.get(OPEN_METEO_URL, params=params)
    resp.raise_for_status()
    data = resp.json()

    daily = data.get("daily", {})
    current = data.get("current", {})

    return {
        "current_temp_f": c_to_f(current.get("temperature_2m")),
        "high_f": c_to_f(daily.get("temperature_2m_max", [None])[0]),
        "low_f": c_to_f(daily.get("temperature_2m_min", [None])[0]),
        "precip_probability": daily.get(
            "precipitation_probability_max", [None]
        )[0],
        "sunrise": daily.get("sunrise", [None])[0],
        "sunset": daily.get("sunset", [None])[0],
    }
