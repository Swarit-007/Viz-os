import pytest

from backend.modules.common import ValidationError
from backend.modules.fcfs_module import FCFSModule
from backend.modules.priority_module import PriorityModule
from backend.modules.roundrobin_module import RoundRobinModule
from backend.modules.sjf_module import SJFModule
from backend.modules.srtf_module import SRTFModule

TEXTBOOK = [
    {'id': 'P1', 'arrival': 0, 'burst': 8, 'priority': 3},
    {'id': 'P2', 'arrival': 1, 'burst': 4, 'priority': 1},
    {'id': 'P3', 'arrival': 2, 'burst': 9, 'priority': 4},
    {'id': 'P4', 'arrival': 3, 'burst': 5, 'priority': 2},
]


def by_id(result):
    return {r['id']: r for r in result['processResults']}


def gantt_names(result):
    return [g['name'] for g in result['ganttChart']['processes']]


def test_fcfs_textbook():
    result = FCFSModule().simulate(TEXTBOOK)
    assert gantt_names(result) == ['P1', 'P2', 'P3', 'P4']
    assert result['ganttChart']['totalTime'] == 26
    assert result['metrics']['avgWaitingTime'] == 8.75
    assert result['metrics']['cpuUtilization'] == 1


def test_sjf_textbook():
    result = SJFModule().simulate(TEXTBOOK)
    assert gantt_names(result) == ['P1', 'P2', 'P4', 'P3']
    assert result['metrics']['avgWaitingTime'] == 7.75


def test_priority_order_and_priority_in_results():
    result = PriorityModule().simulate(TEXTBOOK)
    assert gantt_names(result) == ['P1', 'P2', 'P4', 'P3']
    assert by_id(result)['P3']['priority'] == 4


def test_srtf_textbook_preempts_and_merges_slices():
    result = SRTFModule().simulate(TEXTBOOK)
    assert result['metrics']['avgWaitingTime'] == 6.5
    assert gantt_names(result) == ['P1', 'P2', 'P4', 'P1', 'P3']
    assert by_id(result)['P1']['completionTime'] == 17


def test_round_robin_quantum():
    result = RoundRobinModule().simulate(TEXTBOOK, 3)
    assert result['timeQuantum'] == 3
    assert all(g['duration'] <= 3 for g in result['ganttChart']['processes'])
    assert sum(g['duration'] for g in result['ganttChart']['processes']) == 26


@pytest.mark.parametrize('module', [FCFSModule(), SJFModule(), SRTFModule(), PriorityModule()])
def test_idle_gap_lowers_utilization(module):
    result = module.simulate([
        {'id': 'A', 'arrival': 0, 'burst': 2, 'priority': 1},
        {'id': 'B', 'arrival': 10, 'burst': 2, 'priority': 1},
    ])
    assert result['ganttChart']['totalTime'] == 12
    assert result['metrics']['cpuUtilization'] == round(4 / 12, 4)
    assert by_id(result)['B']['waitingTime'] == 0


@pytest.mark.parametrize('module', [FCFSModule(), SJFModule(), SRTFModule(), PriorityModule()])
def test_invariants_on_random_workloads(module):
    import random
    rng = random.Random(7)
    for _ in range(50):
        procs = [{'id': f'P{i}', 'arrival': rng.randint(0, 10), 'burst': rng.randint(1, 8),
                  'priority': rng.randint(1, 4)} for i in range(rng.randint(1, 8))]
        result = module.simulate(procs)
        for row in result['processResults']:
            assert row['turnaroundTime'] == row['waitingTime'] + row['burstTime']
            assert row['waitingTime'] >= 0 and row['responseTime'] >= 0
            assert row['startTime'] >= row['arrivalTime']
        assert sum(g['duration'] for g in result['ganttChart']['processes']) == \
            sum(p['burst'] for p in procs)


def test_round_robin_matches_tick_reference():
    """Cross-check against a naive one-tick-at-a-time round robin."""
    import random
    rng = random.Random(11)
    for _ in range(50):
        procs = [{'id': f'P{i}', 'arrival': rng.randint(0, 6), 'burst': rng.randint(1, 6)}
                 for i in range(rng.randint(1, 6))]
        quantum = rng.randint(1, 4)
        expected = reference_round_robin(procs, quantum)
        rows = RoundRobinModule().simulate(procs, quantum)['processResults']
        got = {r['id']: r['completionTime'] for r in rows}
        assert got == expected


def reference_round_robin(procs, quantum):
    remaining = {p['id']: p['burst'] for p in procs}
    order = sorted(procs, key=lambda p: p['arrival'])
    queue, done, t, i = [], {}, 0, 0
    while len(done) < len(procs):
        while i < len(order) and order[i]['arrival'] <= t:
            queue.append(order[i]['id'])
            i += 1
        if not queue:
            t = order[i]['arrival']
            continue
        pid = queue.pop(0)
        run = min(quantum, remaining[pid])
        for _ in range(run):
            t += 1
        remaining[pid] -= run
        while i < len(order) and order[i]['arrival'] <= t:
            queue.append(order[i]['id'])
            i += 1
        if remaining[pid]:
            queue.append(pid)
        else:
            done[pid] = t
    return done


@pytest.mark.parametrize('bad', [
    None, [], 'x', [1],
    [{'id': 'A', 'arrival': -1, 'burst': 1}],
    [{'id': 'A', 'arrival': 0, 'burst': 0}],
    [{'id': 'A', 'arrival': 0, 'burst': 'x'}],
    [{'id': 'A', 'arrival': 0, 'burst': 1.5}],
    [{'id': 'A', 'arrival': 0, 'burst': True}],
    [{'id': 'A', 'arrival': 0, 'burst': 1}, {'id': 'A', 'arrival': 0, 'burst': 1}],
])
def test_invalid_processes_rejected(bad):
    with pytest.raises(ValidationError):
        FCFSModule().simulate(bad)


@pytest.mark.parametrize('quantum', [0, -1, 'a', None, 1.5])
def test_round_robin_rejects_bad_quantum(quantum):
    with pytest.raises(ValidationError):
        RoundRobinModule().simulate(TEXTBOOK, quantum)


def test_input_not_mutated():
    procs = [dict(p) for p in TEXTBOOK]
    SJFModule().simulate(procs)
    assert procs == TEXTBOOK
