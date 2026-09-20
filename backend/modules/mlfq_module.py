"""Multilevel Feedback Queue (MLFQ) scheduling with optional aging."""

from typing import Any, Dict, List

from .common import ValidationError, build_schedule_result, process_row, require_int, validate_processes

MAX_LEVELS = 5


class MLFQModule:
    name = "Multilevel Feedback Queue"
    description = ("Processes start in the top queue and are demoted when they use a full quantum. "
                   "Aging promotes processes that wait too long.")

    def simulate(self, processes: List[Dict[str, Any]], quanta: Any = None, aging: Any = 0) -> Dict[str, Any]:
        """Simulate a preemptive MLFQ.

        Args:
            processes: list of {id, arrival, burst}
            quanta: time quantum per level, top level first (default [2, 4, 8]).
                The last level is round robin with its own quantum.
            aging: a process that has waited this long in a lower queue moves up one
                level. 0 disables aging.

        Rules: the highest non-empty queue always runs. A newly arrived or promoted
        higher-level process preempts the running one, which goes to the back of its
        own queue. A process that uses its whole quantum is demoted one level.
        """
        procs = validate_processes(processes)
        if quanta is None:
            quanta = [2, 4, 8]
        if not isinstance(quanta, list) or not 1 <= len(quanta) <= MAX_LEVELS:
            raise ValidationError(f'quanta must list 1 to {MAX_LEVELS} levels')
        quanta = [require_int(q, f'quanta[{i}]', 1, 100) for i, q in enumerate(quanta)]
        aging = require_int(aging, 'aging', 0, 1000)
        levels = len(quanta)

        pending = sorted(procs, key=lambda p: p['arrival'])
        state = {p['id']: {'level': 0, 'remaining': p['burst'], 'since': p['arrival']} for p in procs}
        first_run: Dict[str, int] = {}
        queues: List[List[Dict[str, Any]]] = [[] for _ in range(levels)]
        gantt, rows, events = [], [], []

        current = None
        used = 0  # ticks used in the current slice
        time = 0
        new_slice = True

        def enqueue(proc, level, at):
            state[proc['id']].update(level=level, since=at)
            queues[level].append(proc)

        def admit():
            while pending and pending[0]['arrival'] <= time:
                proc = pending.pop(0)
                enqueue(proc, 0, time)
                events.append({'time': time, 'event': 'arrive', 'process': proc['id'], 'level': 1})

        while pending or any(queues) or current:
            admit()

            # aging: promote anything that has waited too long below the top level
            if aging:
                for level in range(1, levels):
                    for proc in list(queues[level]):
                        if time - state[proc['id']]['since'] >= aging:
                            queues[level].remove(proc)
                            enqueue(proc, level - 1, time)
                            events.append({'time': time, 'event': 'promote', 'process': proc['id'],
                                           'level': level, 'to': level, 'reason': 'aging'})

            # preemption by a higher-level process
            if current is not None:
                cur_level = state[current['id']]['level']
                if any(queues[lvl] for lvl in range(cur_level)):
                    events.append({'time': time, 'event': 'preempt', 'process': current['id'],
                                   'level': cur_level + 1})
                    enqueue(current, cur_level, time)
                    current, used, new_slice = None, 0, True

            if current is None:
                level = next((lvl for lvl in range(levels) if queues[lvl]), None)
                if level is None:
                    time = pending[0]['arrival']  # CPU idle until next arrival
                    continue
                current = queues[level].pop(0)
                used, new_slice = 0, True

            cur = state[current['id']]
            level = cur['level']
            first_run.setdefault(current['id'], time)
            if new_slice:
                gantt.append({'name': current['id'], 'startTime': time, 'duration': 0, 'level': level + 1})
                new_slice = False
            gantt[-1]['duration'] += 1
            cur['remaining'] -= 1
            used += 1
            time += 1
            admit()  # arrivals at the end of a slice queue ahead of the demoted or re-queued process

            if cur['remaining'] == 0:
                rows.append(process_row(current, first_run[current['id']], time))
                events.append({'time': time, 'event': 'finish', 'process': current['id'], 'level': level + 1})
                current, used = None, 0
            elif used == quanta[level]:
                target = min(level + 1, levels - 1)
                events.append({'time': time, 'event': 'demote' if target != level else 'requeue',
                               'process': current['id'], 'level': level + 1, 'to': target + 1})
                enqueue(current, target, time)
                current, used = None, 0

        result = build_schedule_result('MLFQ', gantt, rows, [], time, quanta=quanta, aging=aging)
        result['steps'] = events
        result['events'] = events
        result['levels'] = levels
        return result
