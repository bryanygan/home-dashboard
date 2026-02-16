from __future__ import annotations

import logging
import os
import sys

from dotenv import load_dotenv

load_dotenv()

log = logging.getLogger(__name__)


def _csv_list(key: str) -> list[str]:
    raw = os.getenv(key, "")
    return [x.strip() for x in raw.split(",") if x.strip()]


class Settings:
    # --- Auth / Server ---
    API_KEY: str = os.getenv("SMARTPANEL_API_KEY", "")
    HOST: str = os.getenv("SMARTPANEL_HOST", "0.0.0.0")
    PORT: int = int(os.getenv("SMARTPANEL_PORT", "8100"))

    # --- Homebridge UI X ---
    HOMEBRIDGE_URL: str = os.getenv("HOMEBRIDGE_URL", "http://localhost:8581")
    HOMEBRIDGE_USERNAME: str = os.getenv("HOMEBRIDGE_USERNAME", "admin")
    HOMEBRIDGE_PASSWORD: str = os.getenv("HOMEBRIDGE_PASSWORD", "")

    # --- Pi-hole (v5 admin API) ---
    PIHOLE_URL: str = os.getenv("PIHOLE_URL", "http://localhost")
    PIHOLE_API_TOKEN: str = os.getenv("PIHOLE_API_TOKEN", "")

    # --- Network checks ---
    ROUTER_IP: str = os.getenv("ROUTER_IP", "192.168.1.1")
    PING_TARGET: str = os.getenv("PING_TARGET", "1.1.1.1")
    DNS_CHECK_HOST: str = os.getenv("DNS_CHECK_HOST", "example.com")

    # --- Weather (Open-Meteo) ---
    WEATHER_LAT: str = os.getenv("WEATHER_LAT", "0")
    WEATHER_LON: str = os.getenv("WEATHER_LON", "0")

    # --- Todos ---
    TODOS_FILE_PATH: str = os.getenv("TODOS_FILE_PATH", "/home/pi/todos.json")

    # --- Scene light IDs (comma-separated Homebridge uniqueIds) ---
    SCENE_ALL_ON_IDS: list[str] = _csv_list("SCENE_ALL_ON_IDS")
    SCENE_MOVIE_OFF_IDS: list[str] = _csv_list("SCENE_MOVIE_OFF_IDS")

    # --- Background refresh intervals (seconds) ---
    REFRESH_LIGHTS: int = int(os.getenv("REFRESH_LIGHTS", "15"))
    REFRESH_PIHOLE: int = int(os.getenv("REFRESH_PIHOLE", "30"))
    REFRESH_NETWORK: int = int(os.getenv("REFRESH_NETWORK", "60"))
    REFRESH_WEATHER: int = int(os.getenv("REFRESH_WEATHER", "3600"))
    REFRESH_TODOS: int = int(os.getenv("REFRESH_TODOS", "30"))

    # --- Validation ---
    _REQUIRED = {
        "HOMEBRIDGE_PASSWORD": "Homebridge refresh will fail without credentials",
        "PIHOLE_API_TOKEN": "Pi-hole stats may be incomplete without an API token",
    }
    _RECOMMENDED = {
        "WEATHER_LAT": "Weather data will be for lat=0/lon=0 (Gulf of Guinea)",
        "WEATHER_LON": "Weather data will be for lat=0/lon=0 (Gulf of Guinea)",
    }

    @classmethod
    def validate(cls) -> None:
        """Log warnings for missing required/recommended env vars.

        Exits with code 1 only if a truly fatal var is absent.  For most
        vars we just warn — the background loop will surface the error in
        the cache so the dashboard can still show partial data.
        """
        fatal = False
        for var, hint in cls._REQUIRED.items():
            if not os.getenv(var):
                log.warning("Missing env var %s — %s", var, hint)
        for var, hint in cls._RECOMMENDED.items():
            val = os.getenv(var, "0")
            if val == "0":
                log.warning("Env var %s is unset/default — %s", var, hint)
        if not os.getenv("HOMEBRIDGE_URL"):
            log.error("HOMEBRIDGE_URL is not set — cannot reach Homebridge")
            fatal = True
        if fatal:
            sys.exit(1)


settings = Settings()
