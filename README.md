# VizOS

Interactive visualizer for core Operating Systems algorithms. A Flask API runs the simulations
and a dependency-free HTML/CSS/JS frontend draws Gantt charts, resource graphs and step-by-step traces.

## Algorithms

| Area | Algorithms |
| --- | --- |
| CPU scheduling | FCFS, SJF, SRTF (preemptive SJF), Priority (non-preemptive and preemptive), Round Robin |
| Disk scheduling | FCFS, SSTF, SCAN, C-SCAN, LOOK, C-LOOK |
| Deadlocks | Banker's algorithm (safe sequence, resource-request check, RAG), deadlock detection (wait-for graph) |
| Analysis | Side-by-side comparison of every algorithm on the same input |
| Page replacement | FIFO, LRU, Optimal, Clock (second chance) |
| Memory allocation | First Fit, Best Fit, Worst Fit, Next Fit |

## Quick start

```bash
./start.sh            # macOS / Linux   (Windows: start.bat)
```

Then open <http://localhost:5000>. Every screen recomputes as you edit, has a textbook example, and can be played back step by step. Light and dark themes follow your system. Manual setup:

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python backend/app.py
```

### Configuration (environment variables)

| Variable | Default | Purpose |
| --- | --- | --- |
| `PORT` / `VIZOS_PORT` | `5000` | Listen port |
| `VIZOS_HOST` | `127.0.0.1` | Bind address (use `0.0.0.0` to expose on the network) |
| `VIZOS_DEBUG` | off | Set to `1` for Flask debug mode. Never enable on a reachable host |
| `VIZOS_CORS_ORIGINS` | none | Comma-separated origins allowed to call `/api/*` cross-origin |

### Docker

```bash
docker build -t vizos . && docker run -p 8000:8000 vizos
```

## API

All endpoints take and return JSON. Invalid input returns HTTP 400 with `{"success": false, "error": "..."}`.

| Method & path | Body |
| --- | --- |
| `POST /api/scheduling/{fcfs,sjf,srtf,priority,priority-preemptive}` | `{"processes": [{"id": "P1", "arrival": 0, "burst": 5, "priority": 1}]}` |
| `POST /api/scheduling/roundrobin` | as above plus `"time_quantum": 2` |
| `POST /api/bankers` | `num_processes`, `num_resources`, optional `allocation`, `max`, `available` (random if omitted) |
| `POST /api/bankers/request` | `allocation`, `max`, `available`, `process` (1-based), `request` |
| `POST /api/deadlock` | `num_processes`, `num_resources`, optional `allocation`, `request`, `available` |
| `POST /api/page-replacement` | `{"algorithm": "fifo\|lru\|optimal\|clock", "frames": 3, "page_requests": [1, 2, 3]}` |
| `POST /api/memory-allocation` | `{"strategy": "first\|best\|worst\|next", "blocks": [100, 500], "processes": [212]}` |
| `POST /api/disk-scheduling` | `{"algorithm": "fcfs\|sstf\|scan\|cscan\|look\|clook", "requests": [98, 183], "head": 53, "disk_size": 200, "direction": "up"}` |
| `POST /api/compare/{scheduling,page-replacement,disk}` | same body as the matching simulation; returns every algorithm ranked |
| `GET /api/health` | health check |

Limits: 100 processes, 20 resource types, 500 page references, 100 frames, 1 MiB request body.

## Development

```bash
pip install -r backend/requirements.txt
pytest          # unit + API tests
ruff check .    # lint
```

Layout: `backend/app.py` (routes, error handling), `backend/modules/` (one module per algorithm
plus `common.py` for validation and result building), `backend/tests/`, `frontend/` (static ES-module
site, no build step: `js/views/` has one file per screen, `js/charts.js` the SVG charts),
`api/index.py` (Vercel entry point).

## Deployment

Vercel: `vercel.json` routes everything to `api/index.py`. Elsewhere: use the Dockerfile
(gunicorn) or run `gunicorn backend.app:app`.
