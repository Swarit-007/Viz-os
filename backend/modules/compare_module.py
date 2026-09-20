"""Run every algorithm of a family on the same input and rank the results."""

from typing import Any, Dict, List

from .common import ValidationError
from .disk_scheduling_module import ALGORITHMS as DISK_ALGORITHMS
from .disk_scheduling_module import DiskSchedulingModule
from .fcfs_module import FCFSModule
from .page_replacement_module import ALGORITHMS as PAGE_ALGORITHMS
from .page_replacement_module import PageReplacementModule
from .priority_module import PriorityModule
from .priority_preemptive_module import PreemptivePriorityModule
from .roundrobin_module import RoundRobinModule
from .sjf_module import SJFModule
from .srtf_module import SRTFModule


class CompareModule:
    def scheduling(self, processes: List[Dict[str, Any]], time_quantum: int = 2) -> Dict[str, Any]:
        """Compare all CPU schedulers. Ranked by average waiting time (lower is better)."""
        runs = [
            FCFSModule().simulate(processes),
            SJFModule().simulate(processes),
            SRTFModule().simulate(processes),
            PriorityModule().simulate(processes),
            PreemptivePriorityModule().simulate(processes),
            RoundRobinModule().simulate(processes, time_quantum),
        ]
        results = [{
            'algorithm': run['algorithm'],
            **run['metrics'],
            'totalTime': run['ganttChart']['totalTime'],
            'contextSwitches': max(len(run['ganttChart']['processes']) - 1, 0),
            'ganttChart': run['ganttChart'],
        } for run in runs]
        return self._rank('scheduling', results, key='avgWaitingTime', metric='avgWaitingTime')

    def page_replacement(self, frames: int, page_requests: List[int]) -> Dict[str, Any]:
        """Compare all page replacement algorithms. Ranked by page faults."""
        module = PageReplacementModule()
        results = []
        for name in PAGE_ALGORITHMS:
            run = module.simulate(name, frames, page_requests)
            results.append({'algorithm': run['algorithm'], 'faults': run['total_page_faults'],
                            'hits': run['total_hits'], 'hitRatio': run['hit_ratio']})
        return self._rank('page_replacement', results, key='faults', metric='faults')

    def disk(self, requests: List[int], head: int, disk_size: int = 200,
             direction: str = 'up') -> Dict[str, Any]:
        """Compare all disk schedulers. Ranked by total head movement."""
        module = DiskSchedulingModule()
        results = []
        for name in DISK_ALGORITHMS:
            run = module.simulate(name, requests, head, disk_size, direction)
            results.append({'algorithm': run['algorithm'], 'totalMovement': run['total_movement'],
                            'averageSeek': run['average_seek'], 'path': run['path']})
        return self._rank('disk', results, key='totalMovement', metric='totalMovement')

    @staticmethod
    def _rank(kind: str, results: List[Dict[str, Any]], key: str, metric: str) -> Dict[str, Any]:
        if not results:
            raise ValidationError('Nothing to compare')
        best = min(r[key] for r in results)
        for r in results:
            r['isBest'] = r[key] == best
        return {'success': True, 'kind': kind, 'metric': metric, 'results': results,
                'best': [r['algorithm'] for r in results if r['isBest']]}
