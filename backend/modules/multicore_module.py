"""Multi-core CPU scheduling: FCFS, SJF, SRTF and Round Robin on N cores."""

from typing import Any, Dict, List

from .common import ValidationError, build_schedule_result, process_row, require_int, validate_processes

POLICIES = ('fcfs', 'sjf', 'srtf', 'rr')
LABELS = {'fcfs': 'FCFS', 'sjf': 'SJF', 'srtf': 'SRTF', 'rr': 'Round Robin'}
MAX_CORES = 8


class MultiCoreModule:
    name = "Multi-core Scheduling"
    description = "One shared ready queue feeding several identical cores"

    def simulate(self, processes: List[Dict[str, Any]], cores: Any = 2, policy: str = 'fcfs',
                 time_quantum: Any = 2) -> Dict[str, Any]:
        """Simulate a global ready queue served by `cores` identical CPUs (tick by tick).

        fcfs / sjf are non-preemptive; srtf re-picks the k shortest-remaining
        processes every tick; rr gives each dispatch at most `time_quantum` ticks.
        A running process stays on its core while it keeps running (core affinity).
        """
        if not isinstance(policy, str) or policy.lower() not in POLICIES:
            raise ValidationError(f'Unknown policy: {policy}. Must be one of: {", ".join(POLICIES)}')
        policy = policy.lower()
        cores = require_int(cores, 'cores', 1, MAX_CORES)
        quantum = require_int(time_quantum, 'time_quantum', 1, 100)
        procs = validate_processes(processes)

        by_id = {p['id']: p for p in procs}
        remaining = {p['id']: p['burst'] for p in procs}
        arrival_order = sorted(procs, key=lambda p: (p['arrival'], p['id']))
        ready: List[str] = []            # ids waiting for a core
        on_core: List[Any] = [None] * cores   # id running on each core
        slice_left = [0] * cores
        first_run: Dict[str, int] = {}
        lanes: List[List[Dict[str, Any]]] = [[] for _ in range(cores)]
        rows = []
        busy = [0] * cores
        time, next_arrival = 0, 0

        def pick(candidates: List[str]) -> str:
            if policy == 'sjf':
                return min(candidates, key=lambda i: (by_id[i]['burst'], by_id[i]['arrival']))
            if policy == 'srtf':
                return min(candidates, key=lambda i: (remaining[i], by_id[i]['arrival']))
            return candidates[0]  # fcfs and rr: queue order

        while next_arrival < len(arrival_order) or ready or any(c is not None for c in on_core):
            while next_arrival < len(arrival_order) and arrival_order[next_arrival]['arrival'] <= time:
                ready.append(arrival_order[next_arrival]['id'])
                next_arrival += 1

            if policy == 'srtf':
                # preempt everything and re-pick the k shortest remaining each tick
                pool = ready + [c for c in on_core if c is not None]
                chosen = []
                for _ in range(min(cores, len(pool))):
                    best = pick([i for i in pool if i not in chosen])
                    chosen.append(best)
                keep = {i: c for c, i in enumerate(on_core) if i in chosen}
                new_cores: List[Any] = [None] * cores
                for i, c in keep.items():
                    new_cores[c] = i
                free = [c for c in range(cores) if new_cores[c] is None]
                for i in chosen:
                    if i not in keep:
                        new_cores[free.pop(0)] = i
                ready = [i for i in pool if i not in chosen]
                on_core = new_cores
            else:
                for c in range(cores):
                    if on_core[c] is None and ready:
                        chosen_id = pick(ready)
                        ready.remove(chosen_id)
                        on_core[c] = chosen_id
                        slice_left[c] = quantum

            if all(c is None for c in on_core):
                time = arrival_order[next_arrival]['arrival']  # all cores idle
                continue

            for c, pid in enumerate(on_core):
                if pid is None:
                    continue
                first_run.setdefault(pid, time)
                lane = lanes[c]
                if lane and lane[-1]['name'] == pid and lane[-1]['startTime'] + lane[-1]['duration'] == time:
                    lane[-1]['duration'] += 1
                else:
                    lane.append({'name': pid, 'startTime': time, 'duration': 1})
                remaining[pid] -= 1
                busy[c] += 1
            time += 1

            # arrivals during this tick queue before any preempted process (matches Round Robin)
            while next_arrival < len(arrival_order) and arrival_order[next_arrival]['arrival'] <= time:
                ready.append(arrival_order[next_arrival]['id'])
                next_arrival += 1
            for c, pid in enumerate(on_core):
                if pid is None:
                    continue
                if remaining[pid] == 0:
                    rows.append(process_row(by_id[pid], first_run[pid], time))
                    on_core[c] = None
                elif policy == 'rr':
                    slice_left[c] -= 1
                    if slice_left[c] == 0:
                        ready.append(pid)
                        on_core[c] = None

        flat = sorted((s for lane in lanes for s in lane), key=lambda s: (s['startTime'], s['name']))
        result = build_schedule_result(f'{LABELS[policy]} x{cores}', flat, rows, [], time)
        # CPU utilisation is per core-time available, not wall-clock time
        total_burst = sum(p['burst'] for p in procs)
        result['metrics']['cpuUtilization'] = round(total_burst / (time * cores), 4) if time else 0
        result.update(
            cores=cores, policy=policy, coreLanes=lanes,
            perCoreUtilization=[round(b / time, 4) if time else 0 for b in busy],
            steps=[],
        )
        return result
