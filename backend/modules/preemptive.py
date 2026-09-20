"""Generic preemptive CPU scheduler used by SRTF and preemptive Priority."""

from typing import Any, Callable, Dict, List, Optional

from .common import build_schedule_result, process_row, validate_processes


def simulate_preemptive(processes: List[Dict[str, Any]], algorithm: str,
                        rank: Callable[[Dict[str, Any], Dict[str, int]], Any],
                        reason: Optional[str] = None,
                        include_priority: bool = False) -> Dict[str, Any]:
    """Run a preemptive scheduler.

    `rank(proc, remaining)` returns a sort key; the ready process with the
    smallest key runs. The choice is re-evaluated at every arrival. Consecutive
    slices of the same process are merged in the Gantt chart.
    """
    pending = sorted(validate_processes(processes), key=lambda p: p['arrival'])
    remaining = {p['id']: p['burst'] for p in pending}
    first_run: Dict[str, int] = {}

    time = 0
    ready: List[Dict[str, Any]] = []
    gantt, rows, steps = [], [], []

    while pending or ready:
        while pending and pending[0]['arrival'] <= time:
            ready.append(pending.pop(0))
        if not ready:
            time = pending[0]['arrival']  # CPU idle until next arrival
            continue

        proc = min(ready, key=lambda p: (rank(p, remaining), p['arrival']))
        first_run.setdefault(proc['id'], time)

        # Run until it finishes or the next arrival, whichever comes first.
        run = remaining[proc['id']]
        if pending:
            run = min(run, pending[0]['arrival'] - time)
        start, end = time, time + run

        last = gantt[-1] if gantt else None
        if last and last['name'] == proc['id'] and last['startTime'] + last['duration'] == start:
            last['duration'] += run
        else:
            gantt.append({'name': proc['id'], 'startTime': start, 'duration': run})
        step = {'event': 'run', 'process': proc['id'], 'start': start, 'end': end}
        if reason:
            step['reason'] = reason
        steps.append(step)

        remaining[proc['id']] -= run
        time = end
        if remaining[proc['id']] == 0:
            ready.remove(proc)
            rows.append(process_row(proc, first_run[proc['id']], time, include_priority))

    return build_schedule_result(algorithm, gantt, rows, steps, time)
