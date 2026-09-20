import random

import pytest

import vizos.algos  # noqa: F401
from vizos.core import ValidationError, run_algorithm

P = [{'id': 'P1', 'arrival': 0, 'burst': 8, 'priority': 3}, {'id': 'P2', 'arrival': 1, 'burst': 4, 'priority': 1},
     {'id': 'P3', 'arrival': 2, 'burst': 9, 'priority': 4}, {'id': 'P4', 'arrival': 3, 'burst': 5, 'priority': 2}]


def run(alg, **kw):
    return run_algorithm(alg, {'processes': P, **kw})


def avg_wait(out):
    return next(t['value'] for t in out['summary'] if t['label'] == 'Avg waiting')


def order(out):
    return [s['name'] for s in out['data']['lanes'][0]['slices']]


@pytest.mark.parametrize('alg, wait', [('fcfs', 8.75), ('sjf', 7.75), ('srtf', 6.5), ('priority', 7.75), ('priority-preemptive', 6.5),
                                       ('hrrn', 7.75), ('rr', 13.5), ('mlfq', 13.0)])
def test_textbook_average_waiting(alg, wait):
    kw = {'quantum': 3} if alg == 'rr' else {}
    assert avg_wait(run(alg, **kw)) == wait


def test_orders():
    assert order(run('fcfs')) == ['P1', 'P2', 'P3', 'P4']
    assert order(run('sjf')) == ['P1', 'P2', 'P4', 'P3']
    assert order(run('srtf')) == ['P1', 'P2', 'P4', 'P1', 'P3']


@pytest.mark.parametrize('alg', ['fcfs', 'sjf', 'srtf', 'priority', 'priority-preemptive', 'hrrn', 'rr', 'lottery', 'cfs', 'mlfq', 'multicore'])
def test_invariants_on_random_workloads(alg):
    rng = random.Random(4)
    for _ in range(40):
        procs = [{'id': f'P{i + 1}', 'arrival': rng.randint(0, 8), 'burst': rng.randint(1, 8), 'priority': rng.randint(1, 4),
                  'tickets': rng.randint(1, 30), 'nice': rng.randint(-3, 3)} for i in range(rng.randint(1, 6))]
        out = run_algorithm(alg, {'processes': procs, 'quantum': rng.randint(1, 4), 'seed': rng.randint(0, 99), 'cores': rng.randint(1, 3)})
        slices = [s for lane in out['data']['lanes'] for s in lane['slices']]
        assert sum(s['dur'] for s in slices) == sum(p['burst'] for p in procs)
        for r in out['data']['rows']:
            assert r['turnaround'] == r['waiting'] + r['burst'] and r['waiting'] >= 0 and r['start'] >= r['arrival']
        for lane in out['data']['lanes']:
            for a, b in zip(lane['slices'], lane['slices'][1:]):
                assert a['start'] + a['dur'] <= b['start']


def test_idle_gap_lowers_utilisation():
    out = run_algorithm('fcfs', {'processes': [{'id': 'A', 'arrival': 0, 'burst': 2}, {'id': 'B', 'arrival': 10, 'burst': 2}]})
    assert out['data']['total'] == 12
    assert next(t['value'] for t in out['summary'] if t['label'] == 'CPU utilisation') == '33.3%'


def test_mlfq_demotes_preempts_and_ages():
    out = run('mlfq', q1=2, q2=4, q3=8, aging=0)
    assert any('demoted' in s['note'] for s in out['steps'])
    pre = run_algorithm('mlfq', {'processes': [{'id': 'A', 'arrival': 0, 'burst': 10}, {'id': 'B', 'arrival': 5, 'burst': 1}], 'q1': 1, 'q2': 8, 'q3': 8, 'aging': 0})
    assert any('preempted' in s['note'] for s in pre['steps'])
    hogs = [{'id': 'A', 'arrival': 0, 'burst': 30}, {'id': 'B', 'arrival': 0, 'burst': 30}] + [{'id': f'S{i}', 'arrival': i * 2, 'burst': 2} for i in range(1, 8)]
    aged = run_algorithm('mlfq', {'processes': hogs, 'q1': 2, 'q2': 4, 'q3': 8, 'aging': 6})
    assert any('promoted' in s['note'] for s in aged['steps'])
    assert not any('promoted' in s['note'] for s in run_algorithm('mlfq', {'processes': hogs, 'q1': 2, 'q2': 4, 'q3': 8, 'aging': 0})['steps'])


def test_multicore_speedup_and_single_core_equals_fcfs():
    one = run_algorithm('multicore', {'processes': P, 'cores': 1, 'policy': 'fcfs'})
    two = run_algorithm('multicore', {'processes': P, 'cores': 2, 'policy': 'fcfs'})
    assert one['data']['total'] == run('fcfs')['data']['total']
    assert two['data']['total'] < one['data']['total'] and len(two['data']['lanes']) == 2


def test_lottery_is_seeded_and_favours_tickets():
    a = run_algorithm('lottery', {'processes': [{'id': 'A', 'arrival': 0, 'burst': 40, 'tickets': 90}, {'id': 'B', 'arrival': 0, 'burst': 40, 'tickets': 10}],
                                  'quantum': 1, 'seed': 5})
    b = run_algorithm('lottery', {'processes': [{'id': 'A', 'arrival': 0, 'burst': 40, 'tickets': 90}, {'id': 'B', 'arrival': 0, 'burst': 40, 'tickets': 10}],
                                  'quantum': 1, 'seed': 5})
    assert a == b
    fin = {r['id']: r['finish'] for r in a['data']['rows']}
    assert fin['A'] < fin['B']


def test_cfs_lower_nice_gets_more_cpu_early():
    out = run_algorithm('cfs', {'processes': [{'id': 'A', 'arrival': 0, 'burst': 30, 'nice': -5}, {'id': 'B', 'arrival': 0, 'burst': 30, 'nice': 5}],
                                'latency': 12, 'min_slice': 1})
    fin = {r['id']: r['finish'] for r in out['data']['rows']}
    assert fin['A'] < fin['B']


def test_realtime_edf_vs_rms_on_the_classic_counterexample():
    tasks = [{'id': 'T1', 'period': 5, 'wcet': 2, 'deadline': 5}, {'id': 'T2', 'period': 7, 'wcet': 4, 'deadline': 7}]
    edf = run_algorithm('edf', {'tasks': tasks, 'horizon': 0})
    rms = run_algorithm('rms', {'tasks': tasks, 'horizon': 0})
    assert edf['verdict']['ok'] and not rms['verdict']['ok']


def test_realtime_overload_misses():
    tasks = [{'id': 'T1', 'period': 4, 'wcet': 3, 'deadline': 4}, {'id': 'T2', 'period': 6, 'wcet': 3, 'deadline': 6}]
    assert not run_algorithm('edf', {'tasks': tasks, 'horizon': 0})['verdict']['ok']


@pytest.mark.parametrize('bad', [[], [{'id': 'A', 'arrival': -1, 'burst': 1}], [{'id': 'A', 'arrival': 0, 'burst': 0}],
                                 [{'id': 'A', 'arrival': 0, 'burst': 1}, {'id': 'A', 'arrival': 0, 'burst': 1}],
                                 [{'id': 'A', 'arrival': 0, 'burst': 'x'}], [{'id': 'A', 'arrival': 0, 'burst': 5000}]])
def test_invalid_processes_rejected(bad):
    with pytest.raises(ValidationError):
        run_algorithm('fcfs', {'processes': bad})
