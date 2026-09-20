"""Shortest Job First (SJF, non-preemptive) CPU scheduling."""

from .nonpreemptive import simulate_nonpreemptive


class SJFModule:
    name = "Shortest Job First"
    description = "Processes with shortest burst time are executed first"

    def simulate(self, processes):
        """Simulate SJF. Each process needs `id`, `arrival` and `burst`."""
        return simulate_nonpreemptive(processes, 'SJF', sort_key=lambda p: p['burst'],
                                      reason='shortest job')
