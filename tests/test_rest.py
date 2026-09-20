import random

import pytest

import vizos.algos  # noqa: F401
from vizos.app import create_app
from vizos.core import REGISTRY, ValidationError, run_algorithm


# ------------------------------------------------------------------ files
def test_file_allocation_story():
    p = {'blocks': 16, 'reserved': [2, 3, 7, 8, 12], 'files': [{'id': 'A', 'size': 4}, {'id': 'B', 'size': 5}, {'id': 'C', 'size': 3}]}
    assert run_algorithm('file-contiguous', p)['verdict']['ok'] is False
    linked = run_algorithm('file-linked', p)
    assert linked['verdict'] is not None and linked['table']['rows'][0][2] == '4'
    indexed = run_algorithm('file-indexed', p)
    assert indexed['table']['rows'][0][2] == '2'


def test_file_blocks_never_shared():
    rng = random.Random(3)
    for method in ('contiguous', 'linked', 'indexed'):
        for _ in range(20):
            total = rng.randint(8, 40)
            used = sorted(set(rng.sample(range(total), rng.randint(0, total // 2))))
            files = [{'id': f'F{i}', 'size': rng.randint(1, 8)} for i in range(rng.randint(1, 5))]
            out = run_algorithm(f'file-{method}', {'blocks': total, 'reserved': used, 'files': files})
            final = out['data']['snapshots'][-1]
            assert all(final[u]['kind'] == 'reserved' for u in used)


def test_inode_levels_and_limits():
    out = run_algorithm('inode', {'block_size': 4096, 'pointer': 4, 'direct': 12, 'file_size': 48, 'probe': 0})
    assert out['data']['levels'][0]['used'] == 12 and out['data']['levels'][1]['used'] == 0 and out['data']['probe']['reads'] == 1
    big = run_algorithm('inode', {'block_size': 4096, 'pointer': 4, 'direct': 12, 'file_size': 5000, 'probe': 4200})
    assert big['data']['levels'][2]['used'] > 0 and big['data']['probe']['level'] == 2
    with pytest.raises(ValidationError):
        run_algorithm('inode', {'block_size': 512, 'pointer': 8, 'direct': 1, 'file_size': 100000000, 'probe': 0})


# ------------------------------------------------------------------ deadlock
ALLOC = [[0, 1, 0], [2, 0, 0], [3, 0, 2], [2, 1, 1], [0, 0, 2]]
MAX = [[7, 5, 3], [3, 2, 2], [9, 0, 2], [2, 2, 2], [4, 3, 3]]


def test_bankers_safe_and_sequence_replays():
    out = run_algorithm('bankers', {'n': 5, 'm': 3, 'allocation': ALLOC, 'max': MAX, 'available': [3, 3, 2]})
    assert out['verdict']['ok']
    seq = [int(x[1:]) - 1 for x in out['verdict']['text'].split(': ')[1].split(' -> ')]
    work, need = [3, 3, 2], out['data']['need']
    for i in seq:
        assert all(need[i][j] <= work[j] for j in range(3))
        work = [w + a for w, a in zip(work, ALLOC[i])]


def test_bankers_unsafe_and_validation():
    out = run_algorithm('bankers', {'n': 2, 'm': 1, 'allocation': [[1], [1]], 'max': [[3], [3]], 'available': [0]})
    assert out['verdict']['ok'] is False
    with pytest.raises(ValidationError):
        run_algorithm('bankers', {'n': 1, 'm': 1, 'allocation': [[5]], 'max': [[1]], 'available': [1]})


def test_bankers_request_grant_and_deny():
    base = {'n': 5, 'm': 3, 'allocation': ALLOC, 'max': MAX, 'available': [3, 3, 2]}
    assert run_algorithm('bankers-request', {**base, 'process': 2, 'request': [1, 0, 2]})['verdict']['ok']
    assert not run_algorithm('bankers-request', {**base, 'process': 2, 'request': [9, 0, 0]})['verdict']['ok']
    assert not run_algorithm('bankers-request', {**base, 'available': [0, 0, 0], 'process': 2, 'request': [1, 0, 0]})['verdict']['ok']
    after = {**base, 'allocation': [row[:] for row in ALLOC], 'available': [2, 3, 0]}
    after['allocation'][1] = [3, 0, 2]
    denied = run_algorithm('bankers-request', {**after, 'process': 1, 'request': [0, 2, 0]})
    assert denied['verdict']['ok'] is False and 'unsafe' in denied['verdict']['text']


def test_deadlock_detection_and_cycle():
    dead = run_algorithm('deadlock-detect', {'n': 2, 'm': 2, 'allocation': [[1, 0], [0, 1]], 'request': [[0, 1], [1, 0]], 'available': [0, 0]})
    assert not dead['verdict']['ok'] and dead['data']['graph']['nodes'][0]['kind'] == 'dead'
    fine = run_algorithm('deadlock-detect', {'n': 2, 'm': 2, 'allocation': [[1, 0], [0, 1]], 'request': [[0, 1], [1, 0]], 'available': [1, 1]})
    assert fine['verdict']['ok']
    assert not run_algorithm('rag-cycle', {'edges': ['R1 -> P1', 'P1 -> R2', 'R2 -> P2', 'P2 -> R1']})['verdict']['ok']
    assert run_algorithm('rag-cycle', {'edges': ['R1 -> P1', 'P1 -> R2']})['verdict']['ok']
    with pytest.raises(ValidationError):
        run_algorithm('rag-cycle', {'edges': ['P1 -> P2']})


# ------------------------------------------------------------------ sync
def test_dining_strategies():
    naive = run_algorithm('dining-naive', {'n': 5, 'ticks': 60, 'seed': 1, 'all_hungry': True})
    assert not naive['verdict']['ok'] and naive['steps'][-1]['at'] == 2
    for name in ('ordered', 'asymmetric', 'waiter'):
        for seed in range(6):
            out = run_algorithm(f'dining-{name}', {'n': 5, 'ticks': 80, 'seed': seed, 'all_hungry': seed % 2 == 0})
            assert out['verdict']['ok']
            for snap in out['data']['snapshots']:
                held = [f for ph in snap['philosophers'] for f in ph['holding']]
                assert len(held) == len(set(held))


def test_prodcons_and_race():
    safe = run_algorithm('prodcons-semaphore', {'buffer': 3, 'producers': 2, 'consumers': 1, 'p_period': 1, 'c_period': 2, 'ticks': 80, 'seed': 3})
    assert safe['verdict']['ok'] and all(0 <= s['buffer'] <= 3 for s in safe['data']['snapshots'])
    assert not run_algorithm('prodcons-unsafe', {'buffer': 3, 'producers': 3, 'consumers': 1, 'p_period': 1, 'c_period': 2, 'ticks': 80, 'seed': 3})['verdict']['ok']
    assert any(not run_algorithm('race-unlocked', {'threads': 2, 'increments': 6, 'seed': s})['verdict']['ok'] for s in range(10))
    for s in range(10):
        assert run_algorithm('race-lock', {'threads': 3, 'increments': 6, 'seed': s})['verdict']['ok']


def test_peterson_and_readers_writers():
    for seed in range(8):
        assert run_algorithm('peterson', {'protocol': True, 'rounds': 4, 'seed': seed})['verdict']['ok']
    assert any(not run_algorithm('peterson', {'protocol': False, 'rounds': 4, 'seed': s})['verdict']['ok'] for s in range(8))
    out = run_algorithm('readers-writers', {'priority': 'writers', 'readers': 4, 'writers': 2, 'ticks': 40, 'seed': 1})
    assert out['summary'][1]['value'] > 0


# ------------------------------------------------------------------ misc
def test_fork_tree_counts():
    assert run_algorithm('fork-tree', {'program': ['fork', 'fork']})['summary'][0]['value'] == 4
    assert run_algorithm('fork-tree', {'program': ['fork', 'fork', 'fork']})['summary'][0]['value'] == 8
    assert run_algorithm('fork-tree', {'program': ['fork-if-child', 'fork']})['summary'][0]['value'] == 2
    with pytest.raises(ValidationError):
        run_algorithm('fork-tree', {'program': ['exec']})


def test_cache_conflicts_relieved_by_associativity():
    addrs = [0, 128, 0, 128, 0, 128]
    direct = run_algorithm('cache', {'lines': 8, 'ways': '1', 'block_size': 16, 'addresses': addrs})
    two_way = run_algorithm('cache', {'lines': 8, 'ways': '2', 'block_size': 16, 'addresses': addrs})
    assert direct['summary'][1]['value'] == 0 and two_way['summary'][1]['value'] == 4
    with pytest.raises(ValidationError):
        run_algorithm('cache', {'lines': 6, 'ways': '4', 'block_size': 16, 'addresses': [0]})


# ------------------------------------------------------------------ HTTP
@pytest.fixture
def client():
    return create_app().test_client()


def test_catalog_and_health(client):
    cat = client.get('/api/catalog').get_json()
    assert len(cat['algorithms']) == len(REGISTRY) and cat['categories'] and 'cpu' in cat['compare']
    assert client.get('/api/health').get_json()['algorithms'] == len(REGISTRY)
    assert client.get('/').status_code == 200 and client.get('/css/app.css').status_code in (200, 404)


def test_run_random_and_compare(client):
    ok = client.post('/api/run/rr', json={'params': REGISTRY['rr'].example})
    assert ok.status_code == 200 and ok.get_json()['viz'] == 'timeline'
    rnd = client.post('/api/random/disk-scan', json={'seed': 4}).get_json()['params']
    assert rnd == client.post('/api/random/disk-scan', json={'seed': 4}).get_json()['params']
    cmp_ = client.post('/api/compare/page', json={'params': REGISTRY['page-fifo'].example}).get_json()
    assert cmp_['lowerIsBetter'] and any(r['best'] for r in cmp_['results'])
    assert client.post('/api/compare/cpu', json={'params': {'processes': REGISTRY['fcfs'].example['processes']}}).status_code == 200


@pytest.mark.parametrize('path, body', [('/api/run/nope', {}), ('/api/run/rr', {'params': {'quantum': 0}}), ('/api/run/fcfs', {'params': {'processes': 'x'}}),
                                        ('/api/compare/nope', {}), ('/api/random/nope', {}), ('/api/random/rr', {'seed': 'x'}), ('/api/run/rr', [1])])
def test_errors_are_json_400(client, path, body):
    r = client.post(path, json=body)
    assert r.status_code == 400 and r.get_json()['success'] is False and r.get_json()['error']


def test_malformed_and_wrong_method(client):
    assert client.post('/api/run/rr', data='not json', content_type='application/json').status_code in (200, 400)
    assert client.get('/api/nothing').get_json()['success'] is False
    assert client.get('/api/run/rr').status_code in (404, 405)
    assert client.get('/api/health').headers['X-Content-Type-Options'] == 'nosniff'
