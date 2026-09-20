import random

import pytest

from backend.app import create_app
from backend.modules.buddy_module import BuddyModule
from backend.modules.common import ValidationError
from backend.modules.file_allocation_module import FileAllocationModule
from backend.modules.mlfq_module import MLFQModule
from backend.modules.multicore_module import MultiCoreModule
from backend.modules.roundrobin_module import RoundRobinModule
from backend.modules.sync_module import SyncModule

P = [{'id': 'P1', 'arrival': 0, 'burst': 8}, {'id': 'P2', 'arrival': 1, 'burst': 4},
     {'id': 'P3', 'arrival': 2, 'burst': 9}, {'id': 'P4', 'arrival': 3, 'burst': 5}]


def rand_procs(rng, n=None):
    return [{'id': f'P{i}', 'arrival': rng.randint(0, 8), 'burst': rng.randint(1, 8)}
            for i in range(n or rng.randint(1, 6))]


# ---------------------------------------------------------------- MLFQ
def test_mlfq_single_level_equals_round_robin():
    rng = random.Random(2)
    for _ in range(30):
        procs = rand_procs(rng)
        q = rng.randint(1, 4)
        mlfq = {r['id']: r['completionTime'] for r in MLFQModule().simulate(procs, [q])['processResults']}
        rr = {r['id']: r['completionTime'] for r in RoundRobinModule().simulate(procs, q)['processResults']}
        assert mlfq == rr


def test_mlfq_demotes_and_top_queue_runs_first():
    result = MLFQModule().simulate(P, [2, 4, 8])
    slices = result['ganttChart']['processes']
    assert [s['level'] for s in slices[:4]] == [1, 1, 1, 1]
    assert all(e['to'] == 2 for e in result['events'] if e['event'] == 'demote' and e['level'] == 1)
    assert sum(s['duration'] for s in slices) == 26


def test_mlfq_new_arrival_preempts_lower_queue():
    result = MLFQModule().simulate([
        {'id': 'A', 'arrival': 0, 'burst': 10}, {'id': 'B', 'arrival': 5, 'burst': 1}], [1, 8])
    names = [(s['name'], s['startTime']) for s in result['ganttChart']['processes']]
    assert ('B', 5) in names
    assert any(e['event'] == 'preempt' for e in result['events'])


def test_mlfq_aging_promotes_starving_process():
    hog = [{'id': 'A', 'arrival': 0, 'burst': 30}, {'id': 'B', 'arrival': 0, 'burst': 30}]
    burst_arrivals = [{'id': f'S{i}', 'arrival': i * 2, 'burst': 2} for i in range(1, 8)]
    with_aging = MLFQModule().simulate(hog + burst_arrivals, [2, 4], 6)
    without = MLFQModule().simulate(hog + burst_arrivals, [2, 4], 0)
    assert any(e['event'] == 'promote' for e in with_aging['events'])
    assert not any(e['event'] == 'promote' for e in without['events'])
    assert sum(g['duration'] for g in with_aging['ganttChart']['processes']) == 74


def test_mlfq_invariants():
    rng = random.Random(6)
    for _ in range(40):
        procs = rand_procs(rng)
        result = MLFQModule().simulate(procs, [rng.randint(1, 3), rng.randint(2, 5)], rng.choice([0, 3, 6]))
        assert sum(g['duration'] for g in result['ganttChart']['processes']) == sum(p['burst'] for p in procs)
        for r in result['processResults']:
            assert r['turnaroundTime'] == r['waitingTime'] + r['burstTime']
            assert r['startTime'] >= r['arrivalTime']


@pytest.mark.parametrize('quanta, aging', [([], 0), ([0], 0), ([1] * 9, 0), ('x', 0), ([2], -1), ([2], 'a')])
def test_mlfq_validation(quanta, aging):
    with pytest.raises(ValidationError):
        MLFQModule().simulate(P, quanta, aging)


# ---------------------------------------------------------------- multi-core
@pytest.mark.parametrize('policy', ['fcfs', 'sjf', 'srtf', 'rr'])
def test_multicore_conserves_work_and_no_core_overlap(policy):
    rng = random.Random(8)
    for _ in range(30):
        procs = rand_procs(rng)
        cores = rng.randint(1, 4)
        result = MultiCoreModule().simulate(procs, cores, policy, 2)
        assert sum(s['duration'] for lane in result['coreLanes'] for s in lane) == sum(p['burst'] for p in procs)
        for lane in result['coreLanes']:
            for a, b in zip(lane, lane[1:]):
                assert a['startTime'] + a['duration'] <= b['startTime']
        by_time = {}
        for lane in result['coreLanes']:
            for s in lane:
                for t in range(s['startTime'], s['startTime'] + s['duration']):
                    by_time.setdefault(s['name'], set()).add(t)
        for row in result['processResults']:
            assert row['turnaroundTime'] == row['waitingTime'] + row['burstTime']


def test_multicore_single_core_matches_fcfs_and_more_cores_never_slower():
    from backend.modules.fcfs_module import FCFSModule
    single = MultiCoreModule().simulate(P, 1, 'fcfs')
    assert single['metrics'] == FCFSModule().simulate(P)['metrics']
    two = MultiCoreModule().simulate(P, 2, 'fcfs')
    assert two['ganttChart']['totalTime'] < single['ganttChart']['totalTime']
    assert len(two['coreLanes']) == 2 and len(two['perCoreUtilization']) == 2


def test_multicore_validation():
    for kwargs in (dict(cores=0), dict(cores=9), dict(policy='bogus'), dict(time_quantum=0)):
        with pytest.raises(ValidationError):
            MultiCoreModule().simulate(P, **kwargs)


# ---------------------------------------------------------------- sync
def test_philosophers_naive_deadlocks_and_fixes_do_not():
    s = SyncModule()
    naive = s.philosophers(5, 'naive', 60, 1, True)
    assert naive['deadlock'] and naive['deadlockTick'] == 3
    assert all(len(p['holding']) == 1 for p in naive['steps'][-1]['philosophers'])
    for strategy in ('ordered', 'asymmetric', 'waiter'):
        for seed in range(5):
            for sync_start in (True, False):
                result = s.philosophers(5, strategy, 80, seed, sync_start)
                assert not result['deadlock'] and result['totalMeals'] > 0


def test_philosophers_forks_are_never_shared():
    result = SyncModule().philosophers(6, 'ordered', 100, 4, False)
    for snap in result['steps']:
        held = [f for p in snap['philosophers'] for f in p['holding']]
        assert len(held) == len(set(held))
        for p in snap['philosophers']:
            if p['state'] == 'eating':
                assert len(p['holding']) == 2


def test_producer_consumer_semaphores_protect_buffer():
    ok = SyncModule().producer_consumer(3, 2, 1, 80, 3, True)
    assert ok['overflows'] == 0 and ok['underflows'] == 0
    assert all(0 <= s['buffer'] <= 3 for s in ok['steps'])
    assert ok['produced'] - ok['consumed'] == ok['steps'][-1]['buffer']
    bad = SyncModule().producer_consumer(3, 3, 1, 80, 3, False)
    assert bad['overflows'] > 0


def test_race_condition_loses_updates_only_without_lock():
    s = SyncModule()
    assert any(s.race(2, 6, False, seed)['lostUpdates'] > 0 for seed in range(10))
    for seed in range(10):
        locked = s.race(3, 6, True, seed)
        assert locked['final'] == locked['expected'] == 18


@pytest.mark.parametrize('call', [
    lambda s: s.philosophers(1), lambda s: s.philosophers(5, 'x'), lambda s: s.philosophers(5, ticks=0),
    lambda s: s.producer_consumer(0), lambda s: s.race(1), lambda s: s.race(2, 0),
])
def test_sync_validation(call):
    with pytest.raises(ValidationError):
        call(SyncModule())


# ---------------------------------------------------------------- buddy / segmentation
def test_buddy_split_and_full_coalesce():
    ops = [{'op': 'alloc', 'name': 'A', 'size': 100}, {'op': 'alloc', 'name': 'B', 'size': 240},
           {'op': 'alloc', 'name': 'C', 'size': 64}, {'op': 'free', 'name': 'B'},
           {'op': 'free', 'name': 'A'}, {'op': 'free', 'name': 'C'}]
    result = BuddyModule().simulate(1024, 64, ops)
    assert result['steps'][0]['internalFragmentation'] == 28
    assert result['final'] == [{'start': 0, 'size': 1024, 'status': 'free', 'name': None, 'requested': 0}]


def test_buddy_blocks_always_tile_memory_and_align():
    rng = random.Random(1)
    for _ in range(30):
        live, ops = [], []
        for i in range(25):
            if live and rng.random() < 0.4:
                ops.append({'op': 'free', 'name': live.pop(rng.randrange(len(live)))})
            else:
                name = f'X{i}'
                ops.append({'op': 'alloc', 'name': name, 'size': rng.randint(1, 300)})
                live.append(name)
        # allocations that fail are fine: they must not enter `live`
        result = BuddyModule().simulate(1024, 16, _valid(ops))
        for step in result['steps']:
            cursor = 0
            for b in step['blocks']:
                assert b['start'] == cursor and b['start'] % b['size'] == 0
                cursor += b['size']
            assert cursor == 1024


def _valid(ops):
    """Drop frees of names whose allocation failed by replaying against a scratch allocator."""
    kept, sim = [], BuddyModule()
    for op in ops:
        try:
            sim.simulate(1024, 16, kept + [op])
            kept.append(op)
        except ValidationError:
            pass
    return kept


def test_buddy_allocation_failure_and_validation():
    big = BuddyModule().simulate(64, 8, [{'op': 'alloc', 'name': 'A', 'size': 64}, {'op': 'alloc', 'name': 'B', 'size': 8}])
    assert big['steps'][1]['ok'] is False
    for args in ((100, 8, [{'op': 'alloc', 'name': 'A', 'size': 1}]), (64, 8, []), (64, 8, [{'op': 'free', 'name': 'Z'}]),
                 (64, 8, [{'op': 'alloc', 'name': 'A', 'size': 1}, {'op': 'alloc', 'name': 'A', 'size': 1}])):
        with pytest.raises(ValidationError):
            BuddyModule().simulate(*args)


def test_segmentation_translation_and_faults():
    segs = [{'name': 'code', 'base': 0, 'limit': 300}, {'name': 'data', 'base': 500, 'limit': 200}]
    result = BuddyModule().segmentation(1000, segs, [
        {'segment': 'code', 'offset': 10}, {'segment': 'data', 'offset': 199},
        {'segment': 'data', 'offset': 200}, {'segment': 'stack', 'offset': 0}])
    assert [a['physical'] for a in result['accesses']] == [10, 699, None, None]
    assert result['faults'] == 2 and result['freeMemory'] == 500 and result['largestHole'] == 300
    assert [b['kind'] for b in result['layout']] == ['segment', 'hole', 'segment', 'hole']


def test_segmentation_validation():
    with pytest.raises(ValidationError):
        BuddyModule().segmentation(1000, [{'name': 'a', 'base': 0, 'limit': 500}, {'name': 'b', 'base': 400, 'limit': 100}],
                                   [{'segment': 'a', 'offset': 0}])
    with pytest.raises(ValidationError):
        BuddyModule().segmentation(100, [{'name': 'a', 'base': 50, 'limit': 100}], [{'segment': 'a', 'offset': 0}])


# ---------------------------------------------------------------- files
def test_file_allocation_fragmentation_story():
    result = FileAllocationModule().simulate(
        16, [{'name': 'A', 'size': 4}, {'name': 'B', 'size': 5}, {'name': 'C', 'size': 3}], [2, 3, 7, 8, 12])
    methods = result['methods']
    assert methods['contiguous']['failed'] == ['A', 'B']
    assert methods['linked']['files'][0]['blocks'] == [0, 1, 4, 5]
    assert methods['linked']['files'][0]['seekCost'] == 4
    assert methods['indexed']['files'][0]['indexBlock'] == 0
    assert methods['indexed']['files'][0]['seekCost'] == 2


def test_file_allocation_blocks_never_double_used():
    rng = random.Random(3)
    for _ in range(30):
        total = rng.randint(8, 40)
        used = rng.sample(range(total), rng.randint(0, total // 2))
        files = [{'name': f'F{i}', 'size': rng.randint(1, 8)} for i in range(rng.randint(1, 6))]
        result = FileAllocationModule().simulate(total, files, used)
        for method in result['methods'].values():
            seen = []
            for f in method['files']:
                seen += f['blocks'] + ([f['indexBlock']] if 'indexBlock' in f else [])
            assert len(seen) == len(set(seen)) and not set(seen) & set(used)


def test_file_allocation_validation():
    for args in ((32, [], None), (32, [{'name': 'A', 'size': 0}], None), (32, [{'name': 'A', 'size': 1}], [99]),
                 (2, [{'name': 'A', 'size': 1}], None),
                 (32, [{'name': 'A', 'size': 1}, {'name': 'A', 'size': 1}], None)):
        with pytest.raises(ValidationError):
            FileAllocationModule().simulate(*args)


# ---------------------------------------------------------------- HTTP
def test_new_http_endpoints():
    client = create_app().test_client()
    assert client.post('/api/scheduling/mlfq', json={'processes': P, 'quanta': [2, 4], 'aging': 5}).get_json()['levels'] == 2
    assert client.post('/api/scheduling/multicore', json={'processes': P, 'cores': 2, 'policy': 'srtf'}).status_code == 200
    assert client.post('/api/sync/philosophers', json={'strategy': 'naive', 'synchronized_start': True}).get_json()['deadlock']
    assert client.post('/api/sync/producer-consumer', json={}).get_json()['success']
    assert client.post('/api/sync/race', json={}).get_json()['expected'] == 10
    assert client.post('/api/sync/nope', json={}).status_code == 400
    assert client.post('/api/memory/buddy', json={'operations': [{'op': 'alloc', 'name': 'A', 'size': 10}]}).get_json()['success']
    assert client.post('/api/memory/segmentation', json={
        'segments': [{'name': 'a', 'base': 0, 'limit': 10}], 'accesses': [{'segment': 'a', 'offset': 1}]}).get_json()['faults'] == 0
    assert client.post('/api/file-allocation', json={'files': [{'name': 'A', 'size': 2}]}).get_json()['success']
    assert client.post('/api/file-allocation', json={}).status_code == 400
