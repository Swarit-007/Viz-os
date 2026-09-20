"""Generic non-preemptive CPU scheduler used by FCFS, SJF and Priority."""

from typing import Any, Callable, Dict, List, Optional

from .common import build_schedule_result, process_row, validate_processes


def simulate_nonpreemptive(processes: List[Dict[str, Any]], algorithm: str,
                           sort_key: Callable[[Dict[str, Any]], Any],
                           reason: Optional[str] = None,
                           include_priority: bool = False) -> Dict[str, Any]:
    """Run a non-preemptive scheduler.

    Whenever the CPU frees up, the ready process with the smallest `sort_key`
    is dispatched. Ties fall back to arrival time, then input order.
    """
    pending = sorted(validate_processes(processes), key=lambda p: p['arrival'])
    time = 0
    ready: List[Dict[str, Any]] = []
    gantt, rows, steps = [], [], []

    while pending or ready:
        while pending and pending[0]['arrival'] <= time:
            ready.append(pending.pop(0))
        if not ready:
            time = pending[0]['arrival']  # CPU idle until next arrival
            continue

        proc = min(ready, key=lambda p: (sort_key(p), p['arrival']))
        ready.remove(proc)
        start, end = time, time + proc['burst']

        gantt.append({'name': proc['id'], 'startTime': start, 'duration': proc['burst']})
        step = {'event': 'dispatch', 'process': proc['id'], 'start': start, 'end': end}
        if reason:
            step = {**step, 'reason': reason}
        steps.append(step)
        rows.append(process_row(proc, start, end, include_priority))
        time = end

    return build_schedule_result(algorithm, gantt, rows, steps, time)
