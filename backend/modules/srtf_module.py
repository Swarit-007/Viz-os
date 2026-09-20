"""Shortest Remaining Time First (SRTF, preemptive SJF) CPU scheduling."""

from .common import build_schedule_result, process_row, validate_processes


class SRTFModule:
    name = "Shortest Remaining Time First"
    description = "Preemptive SJF: the process with the least remaining time runs next"

    def simulate(self, processes):
        """Simulate SRTF. Each process needs `id`, `arrival` and `burst`."""
        pending = sorted(validate_processes(processes), key=lambda p: p['arrival'])
        remaining = {p['id']: p['burst'] for p in pending}
        first_run = {}

        time = 0
        ready = []
        gantt, rows, steps = [], [], []

        while pending or ready:
            while pending and pending[0]['arrival'] <= time:
                ready.append(pending.pop(0))
            if not ready:
                time = pending[0]['arrival']  # CPU idle until next arrival
                continue

            proc = min(ready, key=lambda p: (remaining[p['id']], p['arrival']))
            first_run.setdefault(proc['id'], time)

            # Run until it finishes or the next arrival, whichever comes first.
            run = remaining[proc['id']]
            if pending:
                run = min(run, pending[0]['arrival'] - time)
            start, end = time, time + run

            if gantt and gantt[-1]['name'] == proc['id'] and \
                    gantt[-1]['startTime'] + gantt[-1]['duration'] == start:
                gantt[-1]['duration'] += run
            else:
                gantt.append({'name': proc['id'], 'startTime': start, 'duration': run})
            steps.append({'event': 'run', 'process': proc['id'], 'reason': 'least remaining time',
                          'start': start, 'end': end})

            remaining[proc['id']] -= run
            time = end
            if remaining[proc['id']] == 0:
                ready.remove(proc)
                rows.append(process_row(proc, first_run[proc['id']], time))

        return build_schedule_result('SRTF', gantt, rows, steps, time)
