# VizOS

**A laboratory notebook of operating-system algorithms.**
Pick an experiment, change the numbers, press play, and watch the algorithm work one step at a time, with the
matching line of pseudocode lighting up beside it.

VizOS turns the algorithms from an operating-systems course (CPU scheduling, deadlocks, virtual memory, disk
scheduling, file systems and more) into interactive figures. Every figure is computed by a Python simulator from
inputs you control, so you can test your own examples instead of only reading the textbook's.

**Live site:** <https://viz-os-theta.vercel.app>

> Created by **Mayank Karki**, **Swarit Kumar** and **Nitin Kandpal**. See [Credits](#credits).

---

## Contents

1. [What you can do](#what-you-can-do)
2. [The 56 experiments](#the-56-experiments)
3. [How an experiment page works](#how-an-experiment-page-works)
4. [Run it locally](#run-it-locally)
5. [Architecture](#architecture)
6. [The API](#the-api)
7. [Adding a new algorithm](#adding-a-new-algorithm)
8. [Adding a new kind of figure](#adding-a-new-kind-of-figure)
9. [Testing](#testing)
10. [Deployment](#deployment)
11. [Configuration and limits](#configuration-and-limits)
12. [Design notes](#design-notes)
13. [Project layout](#project-layout)
14. [Credits](#credits)

---

## What you can do

- **Explore 56 algorithms** in nine chapters, from FCFS to RAID, each with a description, pseudocode, complexity and notes.
- **Play it back step by step.** Every run is a list of steps. A caption says what just happened, the figure redraws,
  and the pseudocode line responsible is highlighted. Play, pause, step, scrub, change speed.
- **Change any input.** Edit the process table, the reference string, the disk queue, the matrices. Results
  recompute as you type. Bad input is explained in plain words instead of crashing.
- **Randomise.** Every algorithm can produce a valid random input (seeded, so the same seed gives the same input).
- **Load the textbook example** with one click, to check the tool against your course notes.
- **Race a whole family.** Run every scheduler, every page-replacement policy or every disk algorithm on the same
  input and see them ranked.
- **Share.** Your inputs are stored in the page URL, so *Copy link* shares the exact experiment. *Export JSON* saves the result.
- **Search** the catalog with `/` or `Ctrl/Cmd+K`.
- **Switch themes.** Light is drafting paper with pen ink; dark is a blueprint with chalk. Both follow your system setting by default.

### Keyboard shortcuts

| Key | Action |
| --- | --- |
| `/` or `Ctrl/Cmd + K` | open search |
| `R` | random input for the current algorithm |
| `E` | load the textbook example |
| `Space` | play or pause |
| `[` and `]` | step backward and forward |

---

## The 56 experiments

### CPU Scheduling (11)
| Algorithm | What it shows |
| --- | --- |
| First Come First Served | run in arrival order; the convoy effect |
| Shortest Job First | shortest ready burst runs next; best average waiting time among non-preemptive policies |
| Priority Scheduling | lowest priority number runs next, to completion |
| Highest Response Ratio Next | `(waiting + burst) / burst` so long waiters catch up |
| Shortest Remaining Time First | preemptive SJF |
| Preemptive Priority | a higher-priority arrival takes the CPU immediately |
| Round Robin | time quantum and a FIFO queue |
| Lottery Scheduling | random ticket draw, seeded so runs repeat |
| Completely Fair Scheduler | Linux-style virtual runtime with `nice` weights |
| Multilevel Feedback Queue | three queues, demotion, preemption and aging |
| Multi-core Scheduling | one ready queue feeding 1 to 8 cores with FCFS, SJF, SRTF or Round Robin |

### Real-time (2)
| Algorithm | What it shows |
| --- | --- |
| Earliest Deadline First | dynamic priorities by absolute deadline; deadline misses |
| Rate Monotonic | fixed priorities by period; utilisation bound |

### Synchronization (10)
| Algorithm | What it shows |
| --- | --- |
| Dining Philosophers: naive, resource ordering, asymmetric, waiter | four strategies; the naive one deadlocks, the others do not |
| Producer-Consumer: semaphores and unsynchronised | a bounded buffer that is safe, and the same buffer overflowing |
| Race Condition: no lock and mutex lock | interleaved load, add, store lose updates without a lock |
| Readers-Writers | reader priority versus writer priority and starvation |
| Peterson's Algorithm | mutual exclusion from two flags and a turn variable; switch it off to see a collision |

### Deadlocks (4)
| Algorithm | What it shows |
| --- | --- |
| Banker's Algorithm | safe or unsafe state, with the safety check traced process by process |
| Banker's: resource request | grant a request only if the resulting state stays safe |
| Deadlock Detection | which processes can never finish, plus the wait-for graph |
| Resource Allocation Graph | cycle detection by depth-first search |

### Virtual Memory (10)
| Algorithm | What it shows |
| --- | --- |
| FIFO, LRU, MRU, LFU, Optimal, Clock page replacement | frame-by-frame table of hits and faults |
| Belady's Anomaly | faults against frame count for FIFO, LRU and Optimal |
| Working Set Model | working-set size over time (thrashing) |
| Address Translation with a TLB | page and offset split, TLB hit or miss, page faults, effective access time |
| Two-level Page Table | outer index, inner index, offset, and the memory saved |

### Memory Allocation (6)
| Algorithm | What it shows |
| --- | --- |
| First, Best, Worst and Next Fit | processes placed into fixed partitions; external fragmentation |
| Buddy System | splitting, rounding waste and merging of power-of-two blocks |
| Segmentation | segment table translation and segmentation faults |

### Disk and Storage (7)
| Algorithm | What it shows |
| --- | --- |
| FCFS, SSTF, SCAN, C-SCAN, LOOK, C-LOOK | head movement path and total seek distance |
| RAID Levels | RAID 0, 1, 5 and 10 layouts, capacity, and what survives a disk failure |

### File Systems (4)
| Algorithm | What it shows |
| --- | --- |
| Contiguous, Linked and Indexed Allocation | the same files on the same fragmented disk; reads needed to reach the last block |
| Unix Inode | direct, single, double and triple indirect levels |

### Processes and Caches (2)
| Algorithm | What it shows |
| --- | --- |
| fork() Process Tree | how many processes a small program creates |
| CPU Cache | direct-mapped versus set-associative, compulsory versus conflict misses |

---

## How an experiment page works

```
 Header       name, one-line summary, tags
 ┌────────────────────────────────────┐  ┌──────────────────────┐
 │ Fig. N  the figure                 │  │ Setup                │  inputs, Randomise, Example,
 │ caption: what just happened        │  │                      │  Copy link, Export JSON
 │ ⏮ ◀ ▶ ▶| ─────●──── 7/12  1x       │  ├──────────────────────┤
 ├────────────────────────────────────┤  │ Procedure            │  pseudocode, active line highlighted
 │ verdict stamp (e.g. DEADLOCK)      │  ├──────────────────────┤
 │ Measurements (averages, counts)    │  │ Field notes          │  complexity and things to remember
 │ Results table                      │  └──────────────────────┘
 │ Race the whole family              │
 └────────────────────────────────────┘
```

The figure is redrawn for each playback frame from data the server already sent. Scrubbing never recomputes anything.

---

## Run it locally

Requirements: **Python 3.9 or newer**. No Node and no build step: the front end is plain ES modules.

```bash
./start.sh                    # macOS / Linux (Windows: start.bat)
```

Then open <http://localhost:5000>.

The script creates a virtual environment, installs Flask and starts the server. To do it by hand:

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m vizos.app
```

With Docker:

```bash
docker build -t vizos . && docker run -p 8000:8000 vizos
```

---

## Architecture

VizOS has two halves that meet at one JSON contract.

```
 browser (web/)                                     server (vizos/)
┌───────────────────────────┐   GET /api/catalog   ┌──────────────────────────────┐
│ main.js   router, theme,  │ ───────────────────▶ │ core.py     registry, schemas, │
│           shortcuts       │                      │             validation, Trace   │
│ home.js   contents page   │   POST /api/run/id   │ algos/*.py  56 simulators       │
│ page.js   experiment page │ ───────────────────▶ │ compare.py  rank a family       │
│ form.js   schema -> form  │ ◀─────────────────── │ app.py      Flask + static files│
│ player.js playback bar    │   steps, tiles, data └──────────────────────────────┘
│ viz/*.js  one drawer per  │
│           figure kind     │
└───────────────────────────┘
```

**The server describes, the browser draws.** An algorithm is declared once in Python with its name, summary,
pseudocode, complexity, notes, typed input schema, example input and random-input generator. `/api/catalog` sends
all of that to the browser, which builds the home page, the input forms and the pseudocode panel from it. Adding an
algorithm therefore needs no HTML, no form code and no route.

### The result contract

Every algorithm returns the same shape (see `core.result`):

```jsonc
{
  "success": true,
  "id": "fcfs",
  "viz": "timeline",                   // which figure renderer to use
  "summary": [                         // the Measurements ledger
    {"label": "Avg waiting", "value": 8.75, "hint": null, "tone": null}
  ],
  "steps": [                           // one entry per playback frame
    {"note": "P1 runs from 0 to 8 (arrived first). Still waiting: P2, P3, P4.",
     "lines": [2, 4],                  // pseudocode lines to highlight (zero-based)
     "at": 8}                          // where to draw the figure (time, or a snapshot index)
  ],
  "data": { "lanes": [ ... ], "total": 26 },   // whatever the figure needs
  "table": { "title": "...", "headers": [ ... ], "rows": [ ... ] },   // optional
  "verdict": { "ok": false, "label": "Deadlock", "text": "..." }      // optional stamp
}
```

`at` has one rule: for `timeline` figures it is a **time value**; for every other figure it is a **zero-based
snapshot index**, with `-1` meaning "before the first step".

### Parameter schemas

Inputs are described with small builders in `vizos/core.py`. The same dictionary draws the form in the browser and
validates the request on the server, so the two cannot disagree.

| Builder | Browser control | Python value |
| --- | --- | --- |
| `Int` | number box | `int` |
| `Bool` | checkbox | `bool` |
| `Choice` | segmented buttons or drop-down | one of the option values |
| `IntList` | text box of numbers (`7 0 1 2`) | `list[int]` |
| `Lines` | text area, one entry per line | `list[str]` |
| `Table` | editable rows (processes, segments, files) | `list[dict]` with automatic ids `P1, P2, ...` |
| `Matrix` | grid sized by two integer parameters | `list[list[int]]` |
| `Vector` | one row of numbers | `list[int]` |

### Figure kinds

`timeline` (Gantt swim lanes), `frames` (page-replacement table), `disk` (head movement), `grid` (file blocks, RAID,
cache), `memory` and `partitions` (address-space bars), `banker` (matrices), `graph`, `tree`, `curve` (line charts),
`translate` and `multilevel` (address translation), `inode`, `philosophers`, `buffer`, `race` and `sync-state`.

---

## The API

All endpoints take and return JSON. Bad input returns HTTP 400 with `{"success": false, "error": "..."}`.

| Method and path | Purpose |
| --- | --- |
| `GET /api/catalog` | every algorithm with its metadata, parameter schema and example |
| `POST /api/run/<id>` | body `{"params": {...}}`; runs the algorithm and returns the result contract above |
| `POST /api/random/<id>` | optional body `{"seed": 3}`; returns `{"params": {...}}`, a valid random input |
| `POST /api/compare/<family>` | body `{"params": {...}}`; runs every algorithm of `cpu`, `page`, `disk`, `fit`, `files` or `realtime` |
| `GET /api/health` | `{"status": "healthy", "version": "...", "algorithms": 56}` |

Example:

```bash
curl -s -X POST http://localhost:5000/api/run/rr \
  -H 'Content-Type: application/json' \
  -d '{"params": {"quantum": 3, "processes": [
        {"arrival": 0, "burst": 8}, {"arrival": 1, "burst": 4}, {"arrival": 2, "burst": 9}]}}'
```

Fields you leave out take the schema default, so `{}` is always a valid request.

---

## Adding a new algorithm

1. Open the module for its chapter in `vizos/algos/` (or create one and import it in `vizos/algos/__init__.py`).
2. Declare it with `@algorithm(...)`. Give it pseudocode and a `random` generator:

```python
from ..core import Int, IntList, Trace, algorithm, result, tile

@algorithm(
    id='my-sort', name='My Algorithm', category='misc', viz='curve',
    summary='One sentence shown under the title.',
    complexity={'time': 'O(n)', 'space': 'O(1)', 'note': ''},
    pseudocode=['for each item:', '    do the thing'],       # steps refer to these lines by index
    params=[IntList('items', 'Items', [3, 1, 2], 0, 99)],     # draws the form and validates the request
    example={'items': [3, 1, 2]},
    random=lambda rng: {'items': [rng.randint(0, 9) for _ in range(6)]},
    notes=['Something worth remembering.'],
)
def my_algorithm(p):
    trace = Trace()
    for i, item in enumerate(p['items']):
        trace.add(f'Look at {item}.', lines=[0, 1], at=i)     # one playback frame
    return result('my-sort', 'curve', [tile('Items', len(p['items']))], trace, data={...})
```

3. Run `pytest`. The registry tests check every algorithm automatically: metadata is complete, the example runs,
   25 seeded random inputs are valid and reproducible, defaults alone are a valid input, and every highlighted
   pseudocode line exists.

That is all. The algorithm appears on the home page, in search and in `/api/catalog` immediately.

## Adding a new kind of figure

1. Write `render(result, cursor)` in `web/js/viz/` returning a DOM node (build SVG with the `svg()` helper and
   HTML with `h()`; both create text nodes, so data can never inject markup).
2. Register it in the `RENDERERS` table in `web/js/viz/index.js`.
3. Use its name as `viz=` in your algorithm. A test fails if the server uses a `viz` that has no renderer.

---

## Testing

```bash
pip install -e ".[dev]"
pytest            # 330+ tests, about half a second
ruff check .
```

What the tests cover:

- **Contract tests for every algorithm** (`tests/test_registry.py`): metadata, example, random inputs, defaults, step shape.
- **Textbook values**: FCFS 8.75 average wait, page faults 15 / 12 / 9 for FIFO / LRU / Optimal, disk head movement 640 / 236 / 331 / 382 / 299 / 322, Belady's 9 then 10 faults, Banker's safe sequence.
- **Invariants on random workloads**: work is conserved, turnaround = waiting + burst, no core runs two things at once, every disk request is serviced exactly once, Optimal never loses to another policy, forks are never shared between philosophers.
- **Validation**: malformed processes, negative numbers, oversize values, wrong matrix sizes, unknown algorithms.
- **HTTP**: JSON errors, the catalog, seeded randomness, comparisons.
- **Front-end wiring** (`tests/test_frontend.py`): every imported file exists, every figure kind has a renderer, no `innerHTML`, and the Vercel entry point still exports `app`.

---

## Deployment

**Vercel.** `vercel.json` sends every request to `api/index.py`, which exposes the Flask app as the module-level
name `app`. Flask also serves the static files in `web/`. Dependencies come from `api/requirements.txt`.

> Keep `from vizos.app import app` in `api/index.py`. It looks unused, and a linter cleanup once removed it, which
> made Vercel unable to find the app and failed every deployment. A test now guards it.

**Docker.** The `Dockerfile` installs Flask and gunicorn and runs `gunicorn vizos.app:app` on `$PORT` (default 8000) as a non-root user.

**Anywhere else.** `pip install -r requirements.txt -r requirements-prod.txt && gunicorn vizos.app:app`.

The repository runs `ruff`, `pytest` (Python 3.9, 3.12, 3.13) and a JavaScript syntax check on every push (`.github/workflows/ci.yml`).

---

## Configuration and limits

| Environment variable | Default | Purpose |
| --- | --- | --- |
| `PORT` or `VIZOS_PORT` | `5000` | listen port |
| `VIZOS_HOST` | `127.0.0.1` | bind address; use `0.0.0.0` to expose on a network |
| `VIZOS_DEBUG` | off | Flask debug mode. **Never enable on a reachable host**: the debugger allows remote code execution |

Limits keep a request from doing unbounded work: request bodies up to 1 MiB, arrival and burst values up to 200 in
scheduler tables, at most 60 entries in a list or table, at most 12 processes in a scheduling table, 8 cores,
8 philosophers, and for the Banker's algorithm up to 8 processes and 5 resource types.

Responses carry `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY` and `Referrer-Policy: no-referrer`.

---

## Design notes

- **Metaphor.** A laboratory notebook. Light theme is drafting paper with a red margin rule and pen ink; dark theme
  is a blueprint with chalk. There is one accent colour in each (red pen, chalk yellow) and one corner radius.
- **Highlighter colours.** A process keeps the same colour in every figure and table. The colour is derived from its
  id with the golden angle so neighbours stay distinguishable.
- **Hand-drawn edges.** An SVG displacement filter gives shapes a slight wobble. It is never applied to text.
- **Type.** A serif for headings and prose (Iowan Old Style, Palatino, Georgia), a system sans for controls, and a
  monospace for numbers. No web fonts are downloaded.
- **Motion.** One page-turn fade, a pen-stroke underline on the home headline, and playback itself. Everything
  respects `prefers-reduced-motion`, and playback does not start by itself in that mode.
- **Accessibility.** Keyboard operable throughout, visible focus rings, labelled controls, figures carry text
  alternatives, and the search dialog is a native `<dialog>`. Layouts work down to phone width without sideways scrolling.
- **Safety.** All dynamic text is inserted as text nodes, never parsed as HTML.

---

## Project layout

```
vizos/                    Python package (the simulators)
  core.py                 registry, @algorithm decorator, schema builders, validation, Trace, result()
  compare.py              rank every algorithm of a family on one input
  app.py                  Flask application factory, JSON API, static files
  algos/
    cpu.py                FCFS, SJF, SRTF, Priority, HRRN, Round Robin, Lottery, CFS, MLFQ, multi-core
    realtime.py           EDF, Rate Monotonic
    sync.py               philosophers, producer-consumer, race condition, readers-writers, Peterson
    deadlock.py           Banker's, request check, detection, resource-allocation graph
    paging.py             page replacement, Belady, working set, TLB, two-level page tables
    memory.py             fit strategies, buddy system, segmentation
    disk.py               six head-scheduling algorithms, RAID
    files.py              contiguous / linked / indexed allocation, inode
    misc.py               fork tree, CPU cache
web/                      front end (plain ES modules, no build step)
  index.html              page shell and the hand-drawn-edge SVG filter
  css/app.css             themes and every figure's styling
  js/main.js              router, theme, shortcuts
  js/home.js              contents page
  js/page.js              experiment page
  js/form.js              schema-driven input form
  js/player.js            playback bar
  js/palette.js           search dialog
  js/api.js               server calls
  js/viz/                 one renderer per figure kind
tests/                    pytest suite
api/index.py              Vercel entry point
vercel.json               Vercel routing
Dockerfile                container image
start.sh, start.bat       one-command local start
```

---

## Credits

VizOS was created by:

- **Mayank Karki**
- **Swarit Kumar**
- **Nitin Kandpal**

The algorithms follow the standard operating-systems curriculum (for example the examples popularised by
Silberschatz, Galvin and Gagne, *Operating System Concepts*), reimplemented from scratch for this project.

VizOS is intended for teaching and learning. There is no license file yet; ask the authors before reusing the code.
