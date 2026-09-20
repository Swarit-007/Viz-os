"""Deadlock detection module (multi-instance resource allocation)."""

import random

from .common import MAX_PROCESSES, MAX_RESOURCES, require_int, require_matrix, require_vector


class DeadlockModule:
    name = "Deadlock Detection"
    description = "Detect deadlocks in resource allocation"

    def simulate(self, num_processes, num_resources, allocation=None, request=None, available=None):
        """Detect deadlock. Missing (None) inputs are generated randomly for demos."""
        n = require_int(num_processes, 'num_processes', 1, MAX_PROCESSES)
        m = require_int(num_resources, 'num_resources', 1, MAX_RESOURCES)

        if allocation is None:
            allocation = [[random.randint(0, 2) for _ in range(m)] for _ in range(n)]
        if request is None:
            request = [[random.randint(0, 2) for _ in range(m)] for _ in range(n)]
        if available is None:
            available = [random.randint(1, 5) for _ in range(m)]

        allocation = require_matrix(allocation, n, m, 'allocation')
        request = require_matrix(request, n, m, 'request')
        available = require_vector(available, m, 'available')

        deadlocked, steps = self._detect_deadlock(allocation, request, available)

        return {
            'success': True,
            'algorithm': 'Deadlock Detection',
            'allocation': allocation,
            'request': request,
            'available': available,
            'hasDeadlock': bool(deadlocked),
            'deadlockedProcesses': [f'P{i + 1}' for i in deadlocked],
            'waitForGraph': self._generate_wait_for_graph(allocation, request, deadlocked),
            'steps': steps,
        }

    @staticmethod
    def _detect_deadlock(allocation, request, available):
        """Return (indices of deadlocked processes, step trace)."""
        n, m = len(allocation), len(available)
        work = available.copy()
        # A process holding nothing cannot contribute to a deadlock.
        finished = [not any(row) for row in allocation]
        steps = [{'initializedFinished': [f'P{i + 1}' for i in range(n) if finished[i]]}]

        progress = True
        while progress:
            progress = False
            step = {'work': work.copy(), 'allocated': []}
            for i in range(n):
                if not finished[i] and all(request[i][j] <= work[j] for j in range(m)):
                    for j in range(m):
                        work[j] += allocation[i][j]
                    finished[i] = True
                    step['allocated'].append(f'P{i + 1}')
                    progress = True
            steps.append(step)

        return [i for i in range(n) if not finished[i]], steps

    @staticmethod
    def _generate_wait_for_graph(allocation, request, deadlocked):
        """Edge i -> j when process i requests a resource type that j holds."""
        n, m = len(allocation), len(allocation[0])
        processes = [{'name': f'P{i + 1}', 'id': i, 'isDeadlocked': i in deadlocked} for i in range(n)]
        edges = [
            {'from': i, 'to': j, 'label': f'P{i + 1} waits for P{j + 1}'}
            for i in range(n) for j in range(n)
            if i != j and any(request[i][k] > 0 and allocation[j][k] > 0 for k in range(m))
        ]
        return {'processes': processes, 'edges': edges}
