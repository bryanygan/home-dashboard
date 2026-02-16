"""Network health checks: router ping, internet ping, DNS resolve."""
from __future__ import annotations

import asyncio
import logging
import re
import time

from app.config import settings

log = logging.getLogger(__name__)


async def _ping(host: str, timeout: int = 2) -> dict:
    """Ping a host once and return up/down + latency."""
    try:
        proc = await asyncio.create_subprocess_exec(
            "ping", "-c", "1", "-W", str(timeout), host,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await asyncio.wait_for(
            proc.communicate(), timeout=timeout + 2
        )
        if proc.returncode == 0:
            match = re.search(r"time[=<]([\d.]+)", stdout.decode())
            latency = float(match.group(1)) if match else None
            return {"up": True, "latency_ms": latency}
        return {"up": False, "latency_ms": None}
    except Exception as e:
        log.warning("Ping %s failed: %s", host, e)
        return {"up": False, "latency_ms": None}


async def _dns_check(host: str) -> dict:
    """Resolve a hostname via the system resolver and measure latency."""
    loop = asyncio.get_running_loop()
    start = time.monotonic()
    try:
        await asyncio.wait_for(loop.getaddrinfo(host, None), timeout=3.0)
        latency = (time.monotonic() - start) * 1000
        return {"up": True, "latency_ms": round(latency, 1)}
    except Exception as e:
        log.warning("DNS check %s failed: %s", host, e)
        return {"up": False, "latency_ms": None}


async def check_all() -> dict:
    """Run all network checks concurrently."""
    router, internet, dns = await asyncio.gather(
        _ping(settings.ROUTER_IP),
        _ping(settings.PING_TARGET),
        _dns_check(settings.DNS_CHECK_HOST),
    )
    return {"router": router, "internet": internet, "dns": dns}
