"""SmartPanel — lightweight local hub API for Raspberry Pi."""
from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager

import httpx
from fastapi import Depends, FastAPI

from app.auth import verify_api_key
from app.cache import cache
from app.config import Settings, settings
from app.routes import health, lights
from app.routes import network as network_routes
from app.routes import pihole as pihole_routes
from app.routes import todos as todos_routes
from app.routes import weather as weather_routes
from app.services import homebridge, network, pihole, todos, weather

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
log = logging.getLogger("smartpanel")


async def _refresh_loop(
    key: str,
    fetcher,
    interval: int,
    timeout: float = 5.0,
    initial_delay: float = 0.0,
):
    """Generic background refresh: call *fetcher*, store result in cache."""
    if initial_delay:
        await asyncio.sleep(initial_delay)
    while True:
        try:
            data = await asyncio.wait_for(fetcher(), timeout=timeout)
            cache.set(key, data)
            log.debug("Refreshed %s", key)
        except asyncio.CancelledError:
            break
        except Exception as e:
            log.warning("Refresh %s failed: %s", key, e)
            cache.set_error(key, str(e))
        await asyncio.sleep(interval)


@asynccontextmanager
async def lifespan(app: FastAPI):
    client = httpx.AsyncClient(timeout=httpx.Timeout(5.0))
    app.state.http = client

    # Stagger startup slightly so not everything hits at t=0
    tasks = [
        asyncio.create_task(
            _refresh_loop(
                "lights",
                lambda: homebridge.fetch_accessories(client),
                settings.REFRESH_LIGHTS,
                initial_delay=0,
            )
        ),
        asyncio.create_task(
            _refresh_loop(
                "pihole",
                lambda: pihole.fetch_status(client),
                settings.REFRESH_PIHOLE,
                initial_delay=1,
            )
        ),
        asyncio.create_task(
            _refresh_loop(
                "network",
                network.check_all,
                settings.REFRESH_NETWORK,
                timeout=8.0,
                initial_delay=2,
            )
        ),
        asyncio.create_task(
            _refresh_loop(
                "weather",
                lambda: weather.fetch_today(client),
                settings.REFRESH_WEATHER,
                timeout=10.0,
                initial_delay=3,
            )
        ),
        asyncio.create_task(
            _refresh_loop(
                "todos",
                todos.read_todos,
                settings.REFRESH_TODOS,
                initial_delay=0,
            )
        ),
    ]

    # Placeholder for future fitness integration
    cache.set("fitness", {"placeholder": True})

    Settings.validate()

    log.info(
        "SmartPanel started — %d background jobs, port %s",
        len(tasks),
        settings.PORT,
    )
    yield

    for t in tasks:
        t.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)
    await client.aclose()
    log.info("SmartPanel shutdown complete")


app = FastAPI(
    title="SmartPanel",
    version="0.1.0",
    lifespan=lifespan,
    dependencies=[Depends(verify_api_key)],
)

app.include_router(health.router)
app.include_router(lights.router)
app.include_router(pihole_routes.router)
app.include_router(network_routes.router)
app.include_router(weather_routes.router)
app.include_router(todos_routes.router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        log_level="info",
    )
