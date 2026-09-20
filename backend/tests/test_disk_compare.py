import random

import pytest

from backend.modules.bankers_module import BankersModule
from backend.modules.common import ValidationError
from backend.modules.compare_module import CompareModule
from backend.modules.disk_scheduling_module import DiskSchedulingModule
from backend.modules.priority_preemptive_module import PreemptivePriorityModule

REQUESTS = [98, 183, 37, 122, 14, 124, 65, 67]


@pytest.mark.parametrize('algorithm, total', [
    ('fcfs', 640), ('sstf', 236), ('scan', 331), ('cscan', 382), ('look', 299), ('clook', 322),
])
def test_disk_textbook_up(algorithm, total):
    result = DiskSchedulingModule().simulate(algorithm, REQUESTS, 53, 200, 'up')
    assert result['total_movement'] == total
    assert sum(s['distance'] for s in result['steps']) == total


def test_disk_scan_down_first_matches_textbook():
    assert DiskSchedulingModule().simulate('scan', REQUESTS, 53, 200, 'down')['total_movement'] == 236


def test_cscan_jump_is_flagged():
    result = DiskSchedulingModule().simulate('cscan', REQUESTS, 53, 200, 'up')
    jumps = [s for s in result['steps'] if s['jump']]
    assert len(jumps) == 1 and jumps[0]['from'] == 199 and jumps[0]['to'] == 0
    assert result['jump_movement'] == 199


@pytest.mark.parametrize('algorithm', ['fcfs', 'sstf', 'scan', 'cscan', 'look', 'clook'])
@pytest.mark.parametrize('direction', ['up', 'down'])
def test_every_request_serviced_exactly_once(algorithm, direction):
    rng = random.Random(9)
    for _ in range(60):
        reqs = [rng.randint(0, 49) for _ in range(rng.randint(1, 10))]
        head = rng.randint(0, 49)
        result = DiskSchedulingModule().simulate(algorithm, reqs, head, 50, direction)
        serviced = sorted(s['to'] for s in result['steps'] if s['serviced'])
        assert serviced == sorted(reqs)
        assert result['path'][0] == head
        assert all(0 <= c < 50 for c in result['path'])


def test_look_never_worse_than_scan_and_sstf_beats_fcfs_here():
    rng = random.Random(4)
    dm = DiskSchedulingModule()
    for _ in range(50):
        reqs = [rng.randint(0, 99) for _ in range(rng.randint(1, 12))]
        head = rng.randint(0, 99)
        assert dm.simulate('look', reqs, head, 100)['total_movement'] <= \
            dm.simulate('scan', reqs, head, 100)['total_movement']
        assert dm.simulate('clook', reqs, head, 100)['total_movement'] <= \
            dm.simulate('cscan', reqs, head, 100)['total_movement']


@pytest.mark.parametrize('kwargs', [
    dict(algorithm='bogus', requests=[1], head=0),
    dict(algorithm='fcfs', requests=[], head=0),
    dict(algorithm='fcfs', requests=[1], head=200),
    dict(algorithm='fcfs', requests=[200], head=0),
    dict(algorithm='fcfs', requests=[1], head=0, direction='sideways'),
    dict(algorithm='fcfs', requests=[1], head=0, disk_size=1),
    dict(algorithm='fcfs', requests=[-1], head=0),
    dict(algorithm='fcfs', requests=[1], head=None),
])
def test_disk_validation(kwargs):
    with pytest.raises(ValidationError):
        DiskSchedulingModule().simulate(**kwargs)


def test_preemptive_priority_preempts():
    result = PreemptivePriorityModule().simulate([
        {'id': 'A', 'arrival': 0, 'burst': 5, 'priority': 3},
        {'id': 'B', 'arrival': 1, 'burst': 2, 'priority': 1},
    ])
    assert [g['name'] for g in result['ganttChart']['processes']] == ['A', 'B', 'A']
    rows = {r['id']: r for r in result['processResults']}
    assert rows['B']['completionTime'] == 3 and rows['A']['completionTime'] == 7
    assert rows['A']['priority'] == 3


def test_compare_scheduling_ranks_by_waiting_time():
    procs = [{'id': 'P1', 'arrival': 0, 'burst': 8, 'priority': 3},
             {'id': 'P2', 'arrival': 1, 'burst': 4, 'priority': 1},
             {'id': 'P3', 'arrival': 2, 'burst': 9, 'priority': 4},
             {'id': 'P4', 'arrival': 3, 'burst': 5, 'priority': 2}]
    result = CompareModule().scheduling(procs, 2)
    assert len(result['results']) == 7
    assert 'SRTF' in result['best']  # SRTF minimises average waiting time
    assert result['results'][0]['ganttChart']['totalTime'] == 26


def test_compare_page_and_disk():
    page = CompareModule().page_replacement(3, [7, 0, 1, 2, 0, 3, 0, 4, 2, 3, 0, 3, 2, 1, 2, 0, 1, 7, 0, 1])
    assert page['best'] == ['Optimal']
    assert {r['algorithm']: r['faults'] for r in page['results']}['FIFO'] == 15
    disk = CompareModule().disk(REQUESTS, 53, 200)
    assert disk['best'] == ['SSTF']


ALLOC = [[0, 1, 0], [2, 0, 0], [3, 0, 2], [2, 1, 1], [0, 0, 2]]
MAX = [[7, 5, 3], [3, 2, 2], [9, 0, 2], [2, 2, 2], [4, 3, 3]]


def test_bankers_request_textbook_granted_and_denied():
    b = BankersModule()
    granted = b.request_resources(ALLOC, MAX, [3, 3, 2], 2, [1, 0, 2])
    assert granted['granted'] and granted['available'] == [2, 3, 0]
    assert granted['allocation'][1] == [3, 0, 2]
    assert len(granted['safeSequence']) == 5
    # textbook: after P2's grant, P1 asking (0,2,0) would leave an unsafe state
    state = b.request_resources(granted['allocation'], MAX, granted['available'], 1, [0, 2, 0])
    assert not state['granted'] and 'unsafe' in state['reason']


def test_bankers_request_rejections():
    b = BankersModule()
    over_need = b.request_resources(ALLOC, MAX, [3, 3, 2], 2, [9, 0, 0])
    assert not over_need['granted'] and 'maximum claim' in over_need['reason']
    over_avail = b.request_resources(ALLOC, MAX, [0, 0, 0], 2, [1, 0, 0])
    assert not over_avail['granted'] and 'not available' in over_avail['reason']
    with pytest.raises(ValidationError):
        b.request_resources(ALLOC, MAX, [3, 3, 2], 9, [0, 0, 0])
    with pytest.raises(ValidationError):
        b.request_resources(ALLOC, MAX, [3, 3, 2], 1, [0, 0])
    with pytest.raises(ValidationError):
        b.request_resources(None, MAX, [3, 3, 2], 1, [0, 0, 0])
