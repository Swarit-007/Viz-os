import random

import pytest

import vizos.algos  # noqa: F401
from vizos.algos.disk import simulate_disk
from vizos.algos.paging import simulate_replacement
from vizos.core import ValidationError, run_algorithm

REF = [7, 0, 1, 2, 0, 3, 0, 4, 2, 3, 0, 3, 2, 1, 2, 0, 1, 7, 0, 1]
DISK = [98, 183, 37, 122, 14, 124, 65, 67]


def faults(policy, frames, refs):
    return run_algorithm(f'page-{policy}', {'frames': frames, 'refs': refs})['summary'][0]['value']


@pytest.mark.parametrize('policy, expected', [('fifo', 15), ('lru', 12), ('optimal', 9), ('mru', 16), ('lfu', 13)])
def test_page_replacement_textbook(policy, expected):
    assert faults(policy, 3, REF) == expected


def test_optimal_is_a_lower_bound_and_lru_never_shows_belady():
    rng = random.Random(3)
    for _ in range(60):
        refs = [rng.randint(0, 6) for _ in range(rng.randint(1, 30))]
        frames = rng.randint(1, 5)
        best = faults('optimal', frames, refs)
        assert all(best <= faults(p, frames, refs) for p in ('fifo', 'lru', 'mru', 'lfu', 'clock'))
        assert faults('lru', frames + 1, refs) <= faults('lru', frames, refs)


def test_belady_anomaly_and_curve():
    refs = [1, 2, 3, 4, 1, 2, 5, 1, 2, 3, 4, 5]
    assert faults('fifo', 3, refs) == 9 and faults('fifo', 4, refs) == 10
    out = run_algorithm('belady', {'refs': refs, 'max_frames': 6})
    assert out['verdict']['ok'] is False and out['data']['mark'] == [4]


def test_frames_are_slot_stable_and_clock_has_hand():
    steps, _ = simulate_replacement('lru', 3, [1, 2, 3, 1])
    assert steps[-1]['slots'] == [1, 2, 3] and steps[-1]['hit']
    steps, _ = simulate_replacement('clock', 3, REF)
    assert all('refbits' in s and 'hand' in s for s in steps)


def test_working_set():
    out = run_algorithm('working-set', {'refs': [1, 2, 1, 3, 1, 2, 4], 'window': 3})
    assert out['data']['series'][0]['y'] == [1, 2, 2, 3, 2, 3, 3]


def test_tlb_translation():
    out = run_algorithm('tlb', {'page_size': '1024', 'page_table': [5, 2, -1], 'addresses': [100, 300, 2100, 100], 'tlb_size': 2, 't_tlb': 10, 't_mem': 100})
    acc = out['data']['accesses']
    assert acc[0]['pa'] == 5 * 1024 + 100 and acc[1]['tlb'] == 'hit' and acc[2]['fault'] is True and acc[3]['tlb'] == 'hit'
    bad = run_algorithm('tlb', {'page_size': '1024', 'page_table': [5], 'addresses': [5000], 'tlb_size': 1, 't_tlb': 1, 't_mem': 1})
    assert bad['data']['accesses'][0]['invalid']


def test_two_level_saves_space():
    out = run_algorithm('two-level', {'bits_outer': 4, 'bits_inner': 4, 'bits_offset': 8, 'addresses': [0x0123, 0x0456, 0x8123]})
    assert out['data']['accesses'][0]['newInner'] and not out['data']['accesses'][1]['newInner']
    assert out['data']['accesses'][2]['newInner']


@pytest.mark.parametrize('strategy, placement', [('first', [2, 5, 2, None]), ('best', [4, 2, 3, 5]), ('worst', [5, 2, 5, None]), ('next', [2, 5, 5, None])])
def test_fit_strategies(strategy, placement):
    out = run_algorithm(f'fit-{strategy}', {'blocks': [100, 500, 200, 300, 600], 'procs': [212, 417, 112, 426]})
    got = [None if s['placed'] is None else s['placed'] + 1 for s in out['data']['snapshots']]
    assert got == placement


def test_fit_never_overcommits():
    rng = random.Random(1)
    for strategy in ('first', 'best', 'worst', 'next'):
        for _ in range(30):
            out = run_algorithm(f'fit-{strategy}', {'blocks': [rng.randint(10, 100) for _ in range(rng.randint(1, 6))], 'procs': [rng.randint(1, 60) for _ in range(rng.randint(1, 8))]})
            assert all(b['free'] >= 0 for b in out['data']['snapshots'][-1]['blocks'])


def test_buddy_split_merge_and_alignment():
    ops = ['alloc A 100', 'alloc B 240', 'alloc C 64', 'free B', 'free A', 'free C']
    out = run_algorithm('buddy', {'memory': '1024', 'min_block': '64', 'ops': ops})
    assert out['data']['snapshots'][0]['blocks'][0]['waste'] == 28
    assert out['data']['snapshots'][-1]['blocks'] == [{'start': 0, 'size': 1024, 'label': '', 'kind': 'free', 'waste': 0}]
    rng = random.Random(9)
    for _ in range(20):
        from vizos.algos.memory import _random_buddy_ops
        res = run_algorithm('buddy', {'memory': '1024', 'min_block': '16', 'ops': _random_buddy_ops(rng)})
        for snap in res['data']['snapshots']:
            cur = 0
            for b in snap['blocks']:
                assert b['start'] == cur and b['start'] % b['size'] == 0
                cur += b['size']
            assert cur == 1024


def test_buddy_errors():
    for ops in (['free Z'], ['alloc A 10', 'alloc A 10'], ['oops']):
        with pytest.raises(ValidationError):
            run_algorithm('buddy', {'memory': '256', 'min_block': '8', 'ops': ops})


def test_segmentation():
    out = run_algorithm('segmentation', {'memory': 1000, 'segments': [{'id': 'a', 'name': 'code', 'base': 0, 'limit': 300}, {'id': 'b', 'name': 'data', 'base': 500, 'limit': 200}],
                                         'accesses': ['code 10', 'data 199', 'data 200', 'heap 0']})
    assert [s['mark'] for s in out['data']['snapshots']] == [10, 699, None, None]
    with pytest.raises(ValidationError):
        run_algorithm('segmentation', {'memory': 1000, 'segments': [{'id': 'a', 'name': 'x', 'base': 0, 'limit': 500}, {'id': 'b', 'name': 'y', 'base': 400, 'limit': 100}], 'accesses': ['x 1']})


@pytest.mark.parametrize('alg, total', [('fcfs', 640), ('sstf', 236), ('scan', 331), ('cscan', 382), ('look', 299), ('clook', 322)])
def test_disk_textbook(alg, total):
    assert simulate_disk(alg, DISK, 53, 200, True)[1] == total
    assert run_algorithm(f'disk-{alg}', {'requests': DISK, 'head': 53, 'size': 200, 'direction': 'up'})['summary'][0]['value'] == total


@pytest.mark.parametrize('alg', ['fcfs', 'sstf', 'scan', 'cscan', 'look', 'clook'])
@pytest.mark.parametrize('up', [True, False])
def test_disk_services_every_request_once(alg, up):
    rng = random.Random(9)
    for _ in range(50):
        reqs = [rng.randint(0, 49) for _ in range(rng.randint(1, 10))]
        steps, total, _ = simulate_disk(alg, reqs, rng.randint(0, 49), 50, up)
        assert sorted(s['to'] for s in steps if s['serviced']) == sorted(reqs)
        assert total == sum(s['dist'] for s in steps)


def test_disk_scan_down_and_validation():
    assert simulate_disk('scan', DISK, 53, 200, False)[1] == 236
    with pytest.raises(ValidationError):
        run_algorithm('disk-fcfs', {'requests': [500], 'head': 0, 'size': 200, 'direction': 'up'})


@pytest.mark.parametrize('level, disks, ok', [('0', 4, False), ('1', 2, True), ('5', 4, True), ('10', 4, True)])
def test_raid_failure_survival(level, disks, ok):
    out = run_algorithm('raid', {'level': level, 'disks': disks, 'blocks': 8, 'failed': 2})
    assert out['verdict']['ok'] is ok


def test_raid_parity_rotates_and_validates():
    out = run_algorithm('raid', {'level': '5', 'disks': 4, 'blocks': 12, 'failed': 0})
    cells = out['data']['snapshots'][-1]
    parity_cols = [i % 4 for i, c in enumerate(cells) if c['kind'] == 'parity']
    assert len(set(parity_cols)) == 4
    for bad in ({'level': '5', 'disks': 2}, {'level': '10', 'disks': 5}, {'level': '5', 'disks': 4, 'failed': 7}):
        with pytest.raises(ValidationError):
            run_algorithm('raid', {'blocks': 6, 'failed': 0, **bad})
