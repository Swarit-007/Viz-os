# VizOS

A laboratory notebook of operating-system algorithms. Pick an experiment, change the numbers, press play,
and watch it work, one step at a time, with the pseudocode line lighting up beside it.

**56 algorithms** across nine chapters, each with a simulator, pseudocode, complexity notes, a random-input generator
and a textbook example. Light theme = drafting paper, dark theme = blueprint.

| Chapter | Experiments |
| --- | --- |
| CPU Scheduling | FCFS, SJF, SRTF, Priority (non-preemptive and preemptive), HRRN, Round Robin, Lottery, CFS, Multilevel Feedback Queue with aging, Multi-core |
| Real-time | Earliest Deadline First, Rate Monotonic |
| Synchronization | Dining philosophers (naive, resource ordering, asymmetric, waiter), producer-consumer (with and without semaphores), race condition (with and without a lock), readers-writers, Peterson's algorithm |
| Deadlocks | Banker's algorithm, Banker's resource request, deadlock detection, resource-allocation-graph cycles |
| Virtual Memory | FIFO, LRU, MRU, LFU, Optimal, Clock; Belady's anomaly; working set; TLB translation with effective access time; two-level page tables |
| Memory Allocation | First, Best, Worst and Next Fit; buddy system; segmentation |
| Disk and Storage | FCFS, SSTF, SCAN, C-SCAN, LOOK, C-LOOK; RAID 0, 1, 5 and 10 with disk failure |
| File Systems | Contiguous, linked and indexed allocation; Unix inode |
| Processes and Caches | fork() process trees; set-associative CPU cache |

## Run it

```bash
./start.sh                    # macOS / Linux   (Windows: start.bat)
```

Open <http://localhost:5000>. Manually:

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m vizos.app
```

Keyboard: `/` or `Ctrl/Cmd+K` search, `R` random input, `E` textbook example, `Space` play or pause, `[` and `]` step.
Every page has a shareable link (your inputs are encoded in the URL), JSON export, and, for most families,
a button that races every algorithm of the family on your input.

## How it is built

```
vizos/            Python package
  core.py         registry, parameter schemas + validation, result helpers
  algos/          one module per chapter; each algorithm registers metadata + a run() function
  compare.py      run a whole family on one input
  app.py          Flask app: JSON API + static site
web/              front end, plain ES modules, no build step
  js/viz/         one renderer per figure kind (timeline, frames, disk, grid, ...)
tests/            pytest: contract tests for every algorithm, textbook values, invariants, API
api/index.py      Vercel entry point
```

An algorithm is declared once. Its metadata (summary, complexity, pseudocode, and a typed parameter schema)
is served at `/api/catalog`, and the front end builds the page and the input form from it, so adding an
algorithm never needs any form code:

```python
@algorithm(id='fcfs', name='First Come First Served', category='cpu', viz='timeline', pseudocode=[...],
           params=[procs_param()], example={...}, random=lambda rng: {...}, ...)
def fcfs(params): ...
```

Each result carries `summary` tiles, a list of `steps` (each with a note, the pseudocode lines to highlight and a
cursor for the figure), and figure `data`.

### API

| Method and path | Purpose |
| --- | --- |
| `GET /api/catalog` | every algorithm with its metadata and parameter schema |
| `POST /api/run/<id>` | `{"params": {...}}` returns the result; invalid input is HTTP 400 with `{"success": false, "error": "..."}` |
| `POST /api/random/<id>` | `{"seed": 3}` (optional) returns a valid random input; the same seed gives the same input |
| `POST /api/compare/<family>` | rank every algorithm of a family (`cpu`, `page`, `disk`, `fit`, `files`, `realtime`) on one input |
| `GET /api/health` | health check |

### Configuration

| Variable | Default | Purpose |
| --- | --- | --- |
| `PORT` / `VIZOS_PORT` | `5000` | listen port |
| `VIZOS_HOST` | `127.0.0.1` | bind address |
| `VIZOS_DEBUG` | off | Flask debug mode. Never enable on a reachable host |

## Develop

```bash
pip install -e ".[dev]"
pytest          # 330+ tests
ruff check .
```

Deploy: Vercel (`vercel.json` routes everything to `api/index.py`), or the Dockerfile (gunicorn).
