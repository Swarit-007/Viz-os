import pytest

from backend.modules.bankers_module import BankersModule
from backend.modules.common import ValidationError
from backend.modules.deadlock_module import DeadlockModule

ALLOC = [[0, 1, 0], [2, 0, 0], [3, 0, 2], [2, 1, 1], [0, 0, 2]]
MAX = [[7, 5, 3], [3, 2, 2], [9, 0, 2], [2, 2, 2], [4, 3, 3]]


def test_bankers_textbook_safe():
    result = BankersModule().simulate(5, 3, ALLOC, MAX, [3, 3, 2])
    assert result['isSafe']
    assert result['need'][0] == [7, 4, 3]
    assert sorted(result['safeSequence']) == ['P1', 'P2', 'P3', 'P4', 'P5']
    assert result['safeSequence'][0] == 'P2'
    assert replay_is_valid(result)


def replay_is_valid(result):
    work = result['available'][:]
    for name in result['safeSequence']:
        i = int(name[1:]) - 1
        assert all(result['need'][i][j] <= work[j] for j in range(len(work)))
        work = [w + a for w, a in zip(work, result['allocation'][i])]
    return True


def test_bankers_unsafe():
    result = BankersModule().simulate(2, 1, [[1], [1]], [[3], [3]], [0])
    assert not result['isSafe']
    assert result['safeSequence'] == []


def test_bankers_rag_totals_are_deterministic():
    first = BankersModule().simulate(5, 3, ALLOC, MAX, [3, 3, 2])['rag']['resources']
    second = BankersModule().simulate(5, 3, ALLOC, MAX, [3, 3, 2])['rag']['resources']
    assert first == second
    assert first[0]['total'] == 10  # 7 allocated + 3 available


def test_bankers_random_state_is_valid():
    for _ in range(50):
        result = BankersModule().simulate(4, 3)
        assert all(v >= 0 for row in result['need'] for v in row)


@pytest.mark.parametrize('kwargs', [
    dict(allocation=[[1]], max_matrix=[[1, 1]], available=[1]),
    dict(allocation=[[5]], max_matrix=[[1]], available=[1]),
    dict(allocation=[[-1]], max_matrix=[[1]], available=[1]),
    dict(allocation=[[1]], max_matrix=None, available=[1]),
    dict(allocation=[[1]], max_matrix=[[1]], available=[1, 2]),
])
def test_bankers_validation(kwargs):
    with pytest.raises(ValidationError):
        BankersModule().simulate(1, 1, **kwargs)


def test_bankers_size_limits():
    with pytest.raises(ValidationError):
        BankersModule().simulate(0, 3)
    with pytest.raises(ValidationError):
        BankersModule().simulate(10_000, 3)


def test_deadlock_detected_and_graph_consistent():
    result = DeadlockModule().simulate(2, 2, [[1, 0], [0, 1]], [[0, 1], [1, 0]], [0, 0])
    assert result['hasDeadlock']
    assert result['deadlockedProcesses'] == ['P1', 'P2']
    flags = [p['isDeadlocked'] for p in result['waitForGraph']['processes']]
    assert flags == [True, True]
    assert len(result['waitForGraph']['edges']) == 2


def test_no_deadlock_when_resources_available():
    for _ in range(20):  # previously the graph re-ran detection with a random `available`
        result = DeadlockModule().simulate(2, 2, [[1, 0], [0, 1]], [[0, 1], [1, 0]], [1, 1])
        assert not result['hasDeadlock']
        assert not any(p['isDeadlocked'] for p in result['waitForGraph']['processes'])


def test_process_holding_nothing_is_never_deadlocked():
    result = DeadlockModule().simulate(2, 1, [[0], [1]], [[5], [0]], [0])
    assert result['deadlockedProcesses'] == []


def test_deadlock_validation():
    with pytest.raises(ValidationError):
        DeadlockModule().simulate(2, 2, [[1, 0]], [[0, 1], [1, 0]], [0, 0])
