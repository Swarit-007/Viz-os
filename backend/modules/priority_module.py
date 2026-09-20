"""Priority (non-preemptive) CPU scheduling."""

from .nonpreemptive import simulate_nonpreemptive


class PriorityModule:
    name = "Priority Scheduling"
    description = "Processes are executed based on their priority (lower number = higher priority)"

    def simulate(self, processes):
        """Simulate priority scheduling. Each process needs `id`, `arrival`, `burst` and `priority`."""
        return simulate_nonpreemptive(processes, 'Priority', sort_key=lambda p: p['priority'],
                                      reason='highest priority', include_priority=True)
