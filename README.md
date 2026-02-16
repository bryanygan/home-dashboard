# SmartPanel — Phase 1 Backend

A lightweight, cache-first local hub API designed for Raspberry Pi 3 Model B.
Aggregates Homebridge, Pi-hole, network health, weather, and todos into a
single fast API that will power an iPad wall dashboard.

## Quick Start

### 1. Clone to Pi

```bash
cd /home/bghype
git clone <your-repo-url> smartpanel
cd smartpanel
```

### 2. Create virtualenv and install

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure

```bash
# Local dev — reads from project dir
cp .env.example .env
nano .env

# Production — systemd reads from /etc
sudo cp .env.example /etc/smartpanel.env
sudo chmod 600 /etc/smartpanel.env
sudo nano /etc/smartpanel.env
```

**Required values to change:**
- `HOMEBRIDGE_PASSWORD` — your Homebridge UI login password
- `PIHOLE_API_TOKEN` — find at Pi-hole Admin > Settings > API > Show API token
- `LAT` / `LON` — your location coordinates
- `ROUTER_IP` — your LAN gateway (check with `ip route | grep default`)

### 4. Run manually (for testing)

```bash
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8100 --workers 1
```

Then test:
```bash
curl http://localhost:8100/healthz
curl http://localhost:8100/api/lights
curl http://localhost:8100/api/pihole
curl http://localhost:8100/api/network
curl http://localhost:8100/api/weather/today
curl http://localhost:8100/api/todos
```

### 5. Install as systemd service

```bash
sudo cp smartpanel.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable smartpanel
sudo systemctl start smartpanel
```

Check status:
```bash
sudo systemctl status smartpanel
sudo journalctl -u smartpanel -f
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/healthz` | Health check, uptime, version, cache timestamps + errors |
| GET | `/api/lights` | Cached light states |
| POST | `/api/lights/{id}/toggle` | Toggle a light (live call) |
| POST | `/api/scenes/all_on` | Turn on all scene lights |
| POST | `/api/scenes/movie` | Movie mode (off + on lists) |
| GET | `/api/pihole` | Pi-hole stats |
| GET | `/api/network` | Router/internet/DNS status |
| GET | `/api/weather/today` | Weather summary + sunset |
| GET | `/api/todos` | Todos from JSON file |

### Authentication

Set `SMARTPANEL_API_KEY` in your env file to require an API key. Pass it as:
```
X-API-KEY: your-secret-key
```

Leave `SMARTPANEL_API_KEY` empty to disable auth (LAN-only testing).

## Cache Refresh Intervals

| Service | Default Interval | Timeout |
|---------|-----------------|---------|
| Lights | 15s | 5s |
| Pi-hole | 30s | 5s |
| Network | 60s | 8s |
| Weather | 60 min | 10s |
| Todos | 30s | 5s |

All intervals are configurable via `REFRESH_*` env vars.

## Finding Homebridge Light IDs

1. Start SmartPanel and wait ~15 seconds for the first lights refresh
2. `curl http://localhost:8100/api/lights | python3 -m json.tool`
3. Copy the `uniqueId` values for your target lights
4. Set them in your env file:
   ```
   SCENE_ALL_ON_IDS=id1,id2,id3
   SCENE_MOVIE_OFF_IDS=id1,id2
   SCENE_MOVIE_ON_IDS=id3
   ```
5. Restart SmartPanel

## Pi-hole API Token

Navigate to Pi-hole Admin > Settings > API > Show API token, then set:
```
PIHOLE_API_TOKEN=your_token_here
```

## Safe Defaults

These defaults are tuned to avoid overloading Homebridge or Pi-hole on a
resource-constrained Pi 3B. Only change them if you have a specific reason:

```bash
# Refresh intervals — don't go lower than these on a Pi 3B
REFRESH_LIGHTS=15     # Homebridge can bog down below ~10s
REFRESH_PIHOLE=30     # Pi-hole API is fast but no need to hammer it
REFRESH_NETWORK=60    # Pings are cheap but 60s is plenty for a dashboard
REFRESH_WEATHER=3600  # Open-Meteo rate-limits at ~10k/day; 1h is fine
REFRESH_TODOS=30      # Local file read; mtime-checked so no-ops are free

# uvicorn — always use 1 worker on Pi 3B (each worker ~25-40 MB)
# --workers 1 is already set in the systemd unit

# systemd memory guard (already in smartpanel.service)
# MemoryHigh=60M    # soft limit — systemd reclaims aggressively
# MemoryMax=80M     # hard limit — SIGTERM if exceeded
```

## Performance Verification

Run these on the Pi after starting SmartPanel:

```bash
# 1. Is the process running?
ps aux | grep uvicorn

# 2. Memory usage (RSS) — target: <60 MB
ps -o pid,rss,vsz,comm -p $(pgrep -f "uvicorn app.main")
# RSS column is in KB — divide by 1024 for MB

# 3. System memory overview
free -m

# 4. Swap activity (should be near-zero si/so columns)
vmstat 1 5

# 5. Health check
curl -s http://localhost:8100/healthz | python3 -m json.tool

# 6. All endpoints return data (not "not yet fetched")
for ep in lights pihole network weather/today todos; do
  echo "--- /api/$ep ---"
  curl -s http://localhost:8100/api/$ep | python3 -m json.tool
done

# 7. Response time check (<100ms target)
curl -o /dev/null -s -w "healthz: %{time_total}s\n" http://localhost:8100/healthz
curl -o /dev/null -s -w "lights:  %{time_total}s\n" http://localhost:8100/api/lights
curl -o /dev/null -s -w "pihole:  %{time_total}s\n" http://localhost:8100/api/pihole
curl -o /dev/null -s -w "network: %{time_total}s\n" http://localhost:8100/api/network
curl -o /dev/null -s -w "weather: %{time_total}s\n" http://localhost:8100/api/weather/today
curl -o /dev/null -s -w "todos:   %{time_total}s\n" http://localhost:8100/api/todos

# 8. Toggle a light (replace LIGHT_ID with a real uniqueId)
curl -s -X POST http://localhost:8100/api/lights/LIGHT_ID/toggle | python3 -m json.tool

# 9. Scene test (only after configuring SCENE_*_IDS)
curl -s -X POST http://localhost:8100/api/scenes/all_on | python3 -m json.tool
curl -s -X POST http://localhost:8100/api/scenes/movie | python3 -m json.tool

# 10. With auth enabled (set SMARTPANEL_API_KEY=mysecret, restart)
curl -s -H "X-API-KEY: mysecret" http://localhost:8100/api/lights | python3 -m json.tool
curl -s http://localhost:8100/api/lights  # should return 401

# 11. Check logs for errors
sudo journalctl -u smartpanel --since "5 min ago" --no-pager

# 12. Sustained memory check (let it run 10 min, then re-check RSS)
sleep 600 && ps -o pid,rss,comm -p $(pgrep -f "uvicorn app.main")
```

## Diagnosing Swap Pressure

If you see SmartPanel using swap or the system feeling sluggish:

```bash
# Check current swap usage
free -m
# Look at "Swap:" line — used should be near 0

# Watch swap in/out activity in real time (si/so columns)
vmstat 1 10
# si = swap-in (KB/s from disk), so = swap-out (KB/s to disk)
# Both should be 0 or near-0 during normal operation

# Find which processes are using swap
for pid in /proc/[0-9]*; do
  name=$(cat $pid/comm 2>/dev/null)
  swap=$(grep VmSwap $pid/status 2>/dev/null | awk '{print $2}')
  [ -n "$swap" ] && [ "$swap" -gt 0 ] && echo "$swap kB  $name ($(basename $pid))"
done | sort -rn | head -10

# SmartPanel-specific: check if RSS is creeping up
# Run this every few minutes and compare
ps -o pid,rss,vsz -p $(pgrep -f "uvicorn app.main")

# If RSS exceeds 60 MB:
# 1. Check REFRESH_* intervals aren't set too low (below safe defaults)
# 2. Check if Homebridge is returning a huge accessory list
#    curl -s http://localhost:8100/api/lights | python3 -c "import sys,json; print(len(json.load(sys.stdin)['data']))"
# 3. Restart SmartPanel to reset memory
#    sudo systemctl restart smartpanel
# 4. If swap persists, reduce REFRESH_LIGHTS to 30 and REFRESH_PIHOLE to 60
```
