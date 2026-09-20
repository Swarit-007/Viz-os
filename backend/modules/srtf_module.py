"""Shortest Remaining Time First (SRTF, preemptive SJF) CPU scheduling."""

from .preemptive import simulate_preemptive


class SRTFModule:
    name = "Shortest Remaining Time First"
    description = "Preemptive SJF: the process with the least remaining time runs next"

    def simulate(self, processes):
        """Simulate SRTF. Each process needs `id`, `arrival` and `burst`."""
        return simulate_preemptive(processes, 'SRTF', rank=lambda p, remaining: remaining[p['id']],
                                   reason='least remaining time')
