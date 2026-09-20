import pytest

from backend.app import create_app


@pytest.fixture
def client():
    return create_app().test_client()


PROCS = [{'id': 'P1', 'arrival': 0, 'burst': 3, 'priority': 1},
         {'id': 'P2', 'arrival': 1, 'burst': 2, 'priority': 2}]


def test_health_and_index(client):
    assert client.get('/api/health').get_json()['status'] == 'healthy'
    assert 'srtf' in client.get('/api').get_json()['endpoints']['cpu_scheduling']
    assert client.get('/').status_code == 200
    assert client.get('/js/main.js').status_code == 200


@pytest.mark.parametrize('algorithm', ['fcfs', 'sjf', 'srtf', 'priority', 'roundrobin'])
def test_scheduling_endpoints(client, algorithm):
    response = client.post(f'/api/scheduling/{algorithm}', json={'processes': PROCS, 'time_quantum': 2})
    assert response.status_code == 200
    assert response.get_json()['metrics']['avgWaitingTime'] >= 0


def test_round_robin_default_quantum(client):
    assert client.post('/api/scheduling/roundrobin', json={'processes': PROCS}).get_json()['timeQuantum'] == 2


def test_round_robin_zero_quantum_is_400_not_hang(client):
    response = client.post('/api/scheduling/roundrobin', json={'processes': PROCS, 'time_quantum': 0})
    assert response.status_code == 400


@pytest.mark.parametrize('path, body', [
    ('/api/scheduling/fcfs', {}),
    ('/api/scheduling/fcfs', {'processes': []}),
    ('/api/scheduling/nope', {'processes': PROCS}),
    ('/api/bankers', {'num_processes': 0}),
    ('/api/deadlock', {'num_processes': 2, 'num_resources': 2, 'allocation': [[1]]}),
    ('/api/page-replacement', {'page_requests': []}),
    ('/api/page-replacement', {'algorithm': 'x', 'page_requests': [1]}),
    ('/api/memory-allocation', {'blocks': [], 'processes': [1]}),
    ('/api/memory-allocation', {'blocks': [1], 'processes': [1], 'strategy': 'x'}),
])
def test_bad_input_is_400_with_message(client, path, body):
    response = client.post(path, json=body)
    assert response.status_code == 400
    payload = response.get_json()
    assert payload['success'] is False and payload['error']


@pytest.mark.parametrize('kwargs', [
    dict(data='not json', content_type='application/json'),
    dict(data='[1,2]', content_type='application/json'),
    dict(data='', content_type='text/plain'),
])
def test_malformed_body_is_400(client, kwargs):
    assert client.post('/api/scheduling/fcfs', **kwargs).status_code == 400


def test_unknown_api_route_returns_json_404(client):
    response = client.get('/api/nothing')
    assert response.status_code == 404
    assert response.get_json()['success'] is False


def test_wrong_method_returns_json_error(client):
    response = client.get('/api/bankers')
    assert response.status_code in (404, 405)
    assert response.get_json()['success'] is False


def test_page_replacement_and_memory_endpoints(client):
    pr = client.post('/api/page-replacement',
                     json={'algorithm': 'optimal', 'frames': 3, 'page_requests': [1, 2, 3, 4, 1]})
    assert pr.get_json()['success'] and pr.get_json()['algorithm'] == 'Optimal'
    mem = client.post('/api/memory-allocation',
                      json={'blocks': [100, 200], 'processes': [150], 'strategy': 'next'})
    assert mem.get_json()['allocation'] == [{'process': 150, 'block': 2}]


def test_security_headers(client):
    headers = client.get('/api/health').headers
    assert headers['X-Content-Type-Options'] == 'nosniff'
    assert headers['X-Frame-Options'] == 'DENY'


def test_no_cors_by_default(client):
    response = client.get('/api/health', headers={'Origin': 'https://evil.example'})
    assert 'Access-Control-Allow-Origin' not in response.headers


def test_cors_opt_in(monkeypatch):
    monkeypatch.setenv('VIZOS_CORS_ORIGINS', 'https://ok.example')
    response = create_app().test_client().get('/api/health', headers={'Origin': 'https://ok.example'})
    assert response.headers['Access-Control-Allow-Origin'] == 'https://ok.example'


def test_path_traversal_blocked(client):
    assert client.get('/../backend/app.py').status_code in (400, 404)
    assert client.get('/%2e%2e/backend/app.py').status_code in (400, 404)


def test_new_endpoints(client):
    disk = client.post('/api/disk-scheduling', json={
        'algorithm': 'sstf', 'requests': [98, 183, 37, 122, 14, 124, 65, 67], 'head': 53})
    assert disk.get_json()['total_movement'] == 236
    assert client.post('/api/disk-scheduling', json={'requests': [1]}).status_code == 400

    pp = client.post('/api/scheduling/priority-preemptive', json={'processes': PROCS})
    assert pp.get_json()['algorithm'] == 'Priority (Preemptive)'

    cmp_ = client.post('/api/compare/scheduling', json={'processes': PROCS})
    assert len(cmp_.get_json()['results']) == 6
    assert client.post('/api/compare/page-replacement',
                       json={'frames': 2, 'page_requests': [1, 2, 3]}).get_json()['success']
    assert client.post('/api/compare/disk', json={'requests': [5, 9], 'head': 1}).get_json()['best']
    assert client.post('/api/compare/nope', json={}).status_code == 400

    req = client.post('/api/bankers/request', json={
        'allocation': [[1]], 'max': [[3]], 'available': [2], 'process': 1, 'request': [1]})
    assert req.get_json()['granted'] is True
