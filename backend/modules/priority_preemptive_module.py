"""Preemptive Priority CPU scheduling."""

from .preemptive import simulate_preemptive


class PreemptivePriorityModule:
    name = "Preemptive Priority Scheduling"
    description = "A newly arrived higher-priority process (lower number) preempts the running one"

    def simulate(self, processes):
        """Simulate preemptive priority. Each process needs `id`, `arrival`, `burst`, `priority`."""
        return simulate_preemptive(processes, 'Priority (Preemptive)',
                                   rank=lambda p, remaining: p['priority'],
                                   reason='highest priority', include_priority=True)
