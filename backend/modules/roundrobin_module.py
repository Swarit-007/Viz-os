"""Round Robin CPU scheduling."""

from .common import build_schedule_result, process_row, require_int, validate_processes


class RoundRobinModule:
    name = "Round Robin"
    description = "Processes are executed in time slices (quantum) in circular order"

    def simulate(self, processes, time_quantum):
        """Simulate Round Robin with the given time quantum (>= 1)."""
        quantum = require_int(time_quantum, 'time_quantum', 1)
        pending = sorted(validate_processes(processes), key=lambda p: p['arrival'])
        remaining = {p['id']: p['burst'] for p in pending}
        first_run = {}

        time = 0
        ready = []
        gantt, rows, steps = [], [], []

        def admit():
            while pending and pending[0]['arrival'] <= time:
                ready.append(pending.pop(0))

        while pending or ready:
            admit()
            if not ready:
                time = pending[0]['arrival']  # CPU idle until next arrival
                continue

            proc = ready.pop(0)
            first_run.setdefault(proc['id'], time)
            ran = min(quantum, remaining[proc['id']])
            start, end = time, time + ran

            gantt.append({'name': proc['id'], 'startTime': start, 'duration': ran})
            steps.append({'event': 'timeslice', 'process': proc['id'], 'quantum': quantum,
                          'ran': ran, 'start': start, 'end': end})

            remaining[proc['id']] -= ran
            time = end
            admit()  # arrivals during the slice queue ahead of the pre-empted process
            if remaining[proc['id']] > 0:
                ready.append(proc)
            else:
                rows.append(process_row(proc, first_run[proc['id']], time))

        return build_schedule_result('Round Robin', gantt, rows, steps, time, timeQuantum=quantum)
