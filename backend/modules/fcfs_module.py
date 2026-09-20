"""First Come First Serve (FCFS) CPU scheduling."""

from .nonpreemptive import simulate_nonpreemptive


class FCFSModule:
    name = "First Come First Serve"
    description = "Processes are executed in the order they arrive"

    def simulate(self, processes):
        """Simulate FCFS. Each process needs `id`, `arrival` and `burst`."""
        return simulate_nonpreemptive(processes, 'FCFS', sort_key=lambda p: p['arrival'])
