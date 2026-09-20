"""Banker's Algorithm module for deadlock avoidance."""

import random

from .common import MAX_PROCESSES, MAX_RESOURCES, ValidationError, require_int, require_matrix, require_vector


class BankersModule:
    name = "Banker's Algorithm"
    description = "Deadlock avoidance algorithm using resource allocation"

    def simulate(self, num_processes, num_resources, allocation=None, max_matrix=None, available=None):
        """Run Banker's safety algorithm.

        Missing (None) allocation / max / available are generated randomly so the
        UI can offer a one-click demo. Raises ValidationError on bad input.
        """
        n = require_int(num_processes, 'num_processes', 1, MAX_PROCESSES)
        m = require_int(num_resources, 'num_resources', 1, MAX_RESOURCES)

        if allocation is None and max_matrix is None:
            allocation, max_matrix = self._generate_state(n, m)
        elif allocation is None or max_matrix is None:
            raise ValidationError('Provide both allocation and max, or neither')
        if available is None:
            available = [random.randint(2, 9) for _ in range(m)]

        allocation = require_matrix(allocation, n, m, 'allocation')
        max_matrix = require_matrix(max_matrix, n, m, 'max')
        available = require_vector(available, m, 'available')

        for i in range(n):
            for j in range(m):
                if allocation[i][j] > max_matrix[i][j]:
                    raise ValidationError(
                        f'allocation exceeds max for P{i + 1}, R{j + 1}')

        need = [[max_matrix[i][j] - allocation[i][j] for j in range(m)] for i in range(n)]
        safe_sequence, steps = self._find_safe_sequence(allocation, need, available)

        return {
            'success': True,
            'algorithm': "Banker's Algorithm",
            'allocation': allocation,
            'max': max_matrix,
            'need': need,
            'available': available,
            'safeSequence': safe_sequence,
            'rag': self._generate_rag_data(allocation, max_matrix, need, available),
            'isSafe': len(safe_sequence) == n,
            'steps': steps,
        }

    def request_resources(self, allocation, max_matrix, available, process, request):
        """Banker's resource-request algorithm for one process (1-based `process`).

        Grants the request only if it is within the declared need, within what is
        available, and the resulting state is still safe.
        """
        n = len(allocation) if isinstance(allocation, list) else 0
        m = len(available) if isinstance(available, list) else 0
        n = require_int(n, 'allocation rows', 1, MAX_PROCESSES)
        m = require_int(m, 'available length', 1, MAX_RESOURCES)
        allocation = require_matrix(allocation, n, m, 'allocation')
        max_matrix = require_matrix(max_matrix, n, m, 'max')
        available = require_vector(available, m, 'available')
        process = require_int(process, 'process', 1, n)
        request = require_vector(request, m, 'request')
        for i in range(n):
            for j in range(m):
                if allocation[i][j] > max_matrix[i][j]:
                    raise ValidationError(f'allocation exceeds max for P{i + 1}, R{j + 1}')

        i = process - 1
        need = [[max_matrix[r][c] - allocation[r][c] for c in range(m)] for r in range(n)]
        result = {'success': True, 'process': f'P{process}', 'request': request,
                  'granted': False, 'reason': None, 'safeSequence': [], 'steps': []}

        if any(request[j] > need[i][j] for j in range(m)):
            result['reason'] = 'Request exceeds the process maximum claim (need)'
            return result
        if any(request[j] > available[j] for j in range(m)):
            result['reason'] = 'Resources not available: process must wait'
            return result

        # Pretend to allocate, then check safety of the resulting state.
        new_available = [available[j] - request[j] for j in range(m)]
        new_allocation = [row.copy() for row in allocation]
        new_need = [row.copy() for row in need]
        for j in range(m):
            new_allocation[i][j] += request[j]
            new_need[i][j] -= request[j]
        sequence, steps = self._find_safe_sequence(new_allocation, new_need, new_available)
        safe = len(sequence) == n

        result.update(
            granted=safe,
            reason='Request granted: resulting state is safe' if safe
            else 'Request denied: granting it would leave the system in an unsafe state',
            safeSequence=sequence, steps=steps, need=new_need if safe else need,
            allocation=new_allocation if safe else allocation,
            available=new_available if safe else available)
        return result

    @staticmethod
    def _generate_state(n, m):
        """Random allocation with max >= allocation so need is never negative."""
        allocation = [[random.randint(0, 3) for _ in range(m)] for _ in range(n)]
        max_matrix = [[a + random.randint(0, 4) for a in row] for row in allocation]
        return allocation, max_matrix

    @staticmethod
    def _find_safe_sequence(allocation, need, available):
        """Return (safe sequence, step trace). The sequence is shorter than n when unsafe."""
        n, m = len(allocation), len(available)
        work = available.copy()
        finished = [False] * n
        sequence, steps = [], []

        while True:
            chosen = next((i for i in range(n)
                           if not finished[i] and all(need[i][j] <= work[j] for j in range(m))), None)
            step = {'work': work.copy(), 'allocationsReleased': [], 'chosenProcess': None}
            if chosen is not None:
                for j in range(m):
                    work[j] += allocation[chosen][j]
                finished[chosen] = True
                sequence.append(f'P{chosen + 1}')
                step['chosenProcess'] = f'P{chosen + 1}'
                step['allocationsReleased'] = allocation[chosen].copy()
            steps.append(step)
            if chosen is None:
                return sequence, steps

    @staticmethod
    def _generate_rag_data(allocation, max_matrix, need, available):
        """Resource allocation graph: R -> P for held units, P -> R for outstanding need."""
        n, m = len(allocation), len(available)
        processes = [{'name': f'P{i + 1}', 'id': i, 'allocation': allocation[i], 'max': max_matrix[i]}
                     for i in range(n)]
        resources = []
        for j in range(m):
            allocated = sum(allocation[i][j] for i in range(n))
            resources.append({'name': f'R{j + 1}', 'id': j,
                              'total': allocated + available[j], 'allocated': allocated})

        edges = []
        for i in range(n):
            for j in range(m):
                if allocation[i][j] > 0:
                    edges.append({'from': f'R{j + 1}', 'to': f'P{i + 1}',
                                  'type': 'allocation', 'value': allocation[i][j]})
        for i in range(n):
            for j in range(m):
                if need[i][j] > 0:
                    edges.append({'from': f'P{i + 1}', 'to': f'R{j + 1}',
                                  'type': 'request', 'value': need[i][j]})
        return {'processes': processes, 'resources': resources, 'edges': edges}
