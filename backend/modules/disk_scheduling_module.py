"""Disk scheduling module: FCFS, SSTF, SCAN, C-SCAN, LOOK and C-LOOK."""

from typing import Any, Dict, List

from .common import MAX_PAGE_REQUESTS, ValidationError, require_int, require_int_list

ALGORITHMS = ('fcfs', 'sstf', 'scan', 'cscan', 'look', 'clook')
LABELS = {'fcfs': 'FCFS', 'sstf': 'SSTF', 'scan': 'SCAN', 'cscan': 'C-SCAN',
          'look': 'LOOK', 'clook': 'C-LOOK'}
MAX_CYLINDERS = 100_000


class DiskSchedulingModule:
    def simulate(self, algorithm: str, requests: List[int], head: int,
                 disk_size: int = 200, direction: str = 'up') -> Dict[str, Any]:
        """Simulate a disk head scheduling algorithm.

        Args:
            algorithm: fcfs, sstf, scan, cscan, look or clook (case-insensitive)
            requests: cylinder numbers to service, each in [0, disk_size)
            head: starting head position in [0, disk_size)
            disk_size: number of cylinders (last cylinder is disk_size - 1)
            direction: 'up' (toward higher cylinders) or 'down' for the sweep algorithms

        Movement includes the return jump of C-SCAN / C-LOOK; jump steps are flagged.
        """
        if not isinstance(algorithm, str) or algorithm.lower() not in ALGORITHMS:
            raise ValidationError(
                f'Unknown algorithm: {algorithm}. Must be one of: {", ".join(ALGORITHMS)}')
        algorithm = algorithm.lower()
        if direction not in ('up', 'down'):
            raise ValidationError('direction must be "up" or "down"')
        disk_size = require_int(disk_size, 'disk_size', 2, MAX_CYLINDERS)
        requests = require_int_list(requests, 'requests', 0, MAX_PAGE_REQUESTS)
        head = require_int(head, 'head', 0, disk_size - 1)
        if max(requests) >= disk_size:
            raise ValidationError(f'requests must be below disk_size ({disk_size})')

        order = getattr(self, f'_{algorithm}')(requests, head, disk_size, direction == 'up')

        steps, position, total, jump_total = [], head, 0, 0
        for cylinder, kind in order:
            distance = abs(cylinder - position)
            total += distance
            is_jump = kind in ('jump', 'jumpreq')
            if is_jump:
                jump_total += distance
            steps.append({'from': position, 'to': cylinder, 'distance': distance,
                          'jump': is_jump, 'serviced': kind in ('req', 'jumpreq')})
            position = cylinder

        return {
            'success': True,
            'algorithm': LABELS[algorithm],
            'head': head,
            'disk_size': disk_size,
            'direction': direction,
            'requests': requests,
            'path': [head] + [c for c, _ in order],
            'steps': steps,
            'total_movement': total,
            'jump_movement': jump_total,
            'average_seek': round(total / len(requests), 2),
        }

    # Each strategy returns [(cylinder, kind)] where kind is:
    #   req     - head arrives at a request and services it
    #   edge    - head travels to the physical end of the disk (SCAN / C-SCAN)
    #   jump    - non-servicing return seek to the opposite end (C-SCAN)
    #   jumpreq - return seek that lands on the farthest request (C-LOOK)

    @staticmethod
    def _reqs(cylinders):
        return [(c, 'req') for c in cylinders]

    @staticmethod
    def _sweeps(requests, head):
        """(ascending requests >= head, descending requests < head, descending <= head, ascending > head)."""
        return (sorted(r for r in requests if r >= head),
                sorted((r for r in requests if r < head), reverse=True),
                sorted((r for r in requests if r <= head), reverse=True),
                sorted(r for r in requests if r > head))

    def _fcfs(self, requests, head, size, up):
        return self._reqs(requests)

    def _sstf(self, requests, head, size, up):
        pending, position, order = list(requests), head, []
        while pending:
            nearest = min(pending, key=lambda r: (abs(r - position), r))
            pending.remove(nearest)
            order.append(nearest)
            position = nearest
        return self._reqs(order)

    def _scan(self, requests, head, size, up):
        above, below, at_or_below, strictly_above = self._sweeps(requests, head)
        first, end, rest = (above, size - 1, below) if up else (at_or_below, 0, strictly_above)
        order = self._reqs(first)
        if not order or order[-1][0] != end:
            order.append((end, 'edge'))
        return order + self._reqs(rest)

    def _cscan(self, requests, head, size, up):
        above, below, at_or_below, strictly_above = self._sweeps(requests, head)
        if up:
            first, end, rest, restart = above, size - 1, sorted(below), 0
        else:
            first, end, rest, restart = at_or_below, 0, strictly_above[::-1], size - 1
        order = self._reqs(first)
        if not order or order[-1][0] != end:
            order.append((end, 'edge'))
        if rest:
            order.append((restart, 'jump'))
            order += self._reqs(rest)
        return order

    def _look(self, requests, head, size, up):
        above, below, at_or_below, strictly_above = self._sweeps(requests, head)
        if up:
            return self._reqs(above + below)
        return self._reqs(at_or_below + strictly_above)

    def _clook(self, requests, head, size, up):
        above, below, at_or_below, strictly_above = self._sweeps(requests, head)
        first, rest = (above, sorted(below)) if up else (at_or_below, strictly_above[::-1])
        order = self._reqs(first)
        if rest:
            order.append((rest[0], 'jumpreq'))
            order += self._reqs(rest[1:])
        return order
