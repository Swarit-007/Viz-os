"""Shared validation and result-building helpers for VizOS algorithm modules."""

from numbers import Real
from typing import Any, Dict, List, Optional

MAX_PROCESSES = 100
MAX_RESOURCES = 20
MAX_PAGE_REQUESTS = 500
MAX_FRAMES = 100
MAX_TIME = 1000  # cap on arrival/burst so tick-based simulators stay bounded


class ValidationError(ValueError):
    """Raised when client input is malformed. Maps to HTTP 400."""


def require_int(value: Any, name: str, minimum: Optional[int] = None,
                maximum: Optional[int] = None) -> int:
    """Return value as int or raise ValidationError. Rejects bools and non-integral floats."""
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValidationError(f'{name} must be a number')
    if int(value) != value:
        raise ValidationError(f'{name} must be a whole number')
    value = int(value)
    if minimum is not None and value < minimum:
        raise ValidationError(f'{name} must be at least {minimum}')
    if maximum is not None and value > maximum:
        raise ValidationError(f'{name} must be at most {maximum}')
    return value


def require_int_list(values: Any, name: str, minimum: Optional[int] = None,
                     max_length: Optional[int] = None) -> List[int]:
    if not isinstance(values, list) or not values:
        raise ValidationError(f'{name} must be a non-empty list')
    if max_length is not None and len(values) > max_length:
        raise ValidationError(f'{name} must have at most {max_length} entries')
    return [require_int(v, f'{name}[{i}]', minimum) for i, v in enumerate(values)]


def require_matrix(matrix: Any, rows: int, cols: int, name: str) -> List[List[int]]:
    """Validate a rows x cols matrix of non-negative integers."""
    if not isinstance(matrix, list) or len(matrix) != rows:
        raise ValidationError(f'{name} must have {rows} rows')
    result = []
    for i, row in enumerate(matrix):
        if not isinstance(row, list) or len(row) != cols:
            raise ValidationError(f'{name} row {i + 1} must have {cols} columns')
        result.append([require_int(v, f'{name}[{i}][{j}]', 0) for j, v in enumerate(row)])
    return result


def require_vector(vector: Any, size: int, name: str) -> List[int]:
    if not isinstance(vector, list) or len(vector) != size:
        raise ValidationError(f'{name} must have {size} entries')
    return [require_int(v, f'{name}[{i}]', 0) for i, v in enumerate(vector)]


def validate_processes(processes: Any) -> List[Dict[str, Any]]:
    """Validate and normalise a list of scheduling processes.

    Each process needs `arrival` (>= 0) and `burst` (> 0). `id` defaults to
    P<n> and `priority` defaults to 0. Returns fresh dicts; input is not mutated.
    """
    if not isinstance(processes, list) or not processes:
        raise ValidationError('No processes provided')
    if len(processes) > MAX_PROCESSES:
        raise ValidationError(f'At most {MAX_PROCESSES} processes are supported')

    normalised = []
    seen = set()
    for index, proc in enumerate(processes):
        if not isinstance(proc, dict):
            raise ValidationError(f'Process {index + 1} must be an object')
        pid = str(proc.get('id', f'P{index + 1}'))
        if pid in seen:
            raise ValidationError(f'Duplicate process id: {pid}')
        seen.add(pid)
        normalised.append({
            'id': pid,
            'arrival': require_int(proc.get('arrival'), f'{pid} arrival', 0, MAX_TIME),
            'burst': require_int(proc.get('burst'), f'{pid} burst', 1, MAX_TIME),
            'priority': require_int(proc.get('priority', 0), f'{pid} priority'),
        })
    return normalised


def build_schedule_result(algorithm: str, gantt: List[Dict[str, Any]],
                          process_results: List[Dict[str, Any]],
                          steps: List[Dict[str, Any]], total_time: int,
                          **extra: Any) -> Dict[str, Any]:
    """Assemble the response shape shared by all CPU scheduling algorithms."""
    count = len(process_results)
    total_burst = sum(p['burstTime'] for p in process_results)

    def average(key: str) -> float:
        return round(sum(p[key] for p in process_results) / count, 2)

    result = {
        'algorithm': algorithm,
        'ganttChart': {'processes': gantt, 'totalTime': total_time},
        'processResults': process_results,
        'metrics': {
            'avgWaitingTime': average('waitingTime'),
            'avgTurnaroundTime': average('turnaroundTime'),
            'avgResponseTime': average('responseTime'),
            'cpuUtilization': round(total_burst / total_time, 4) if total_time > 0 else 0,
        },
        'steps': steps,
    }
    result.update(extra)
    return result


def process_row(proc: Dict[str, Any], start: int, completion: int,
                include_priority: bool = False) -> Dict[str, Any]:
    """Per-process result row (arrival/burst/start/completion and derived times)."""
    turnaround = completion - proc['arrival']
    row = {
        'id': proc['id'],
        'arrivalTime': proc['arrival'],
        'burstTime': proc['burst'],
    }
    if include_priority:
        row['priority'] = proc['priority']
    row.update({
        'startTime': start,
        'completionTime': completion,
        'turnaroundTime': turnaround,
        'waitingTime': turnaround - proc['burst'],
        'responseTime': start - proc['arrival'],
    })
    return row
