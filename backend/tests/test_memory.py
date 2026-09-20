import pytest

from backend.modules.common import ValidationError
from backend.modules.memory_allocation_module import MemoryAllocationModule
from backend.modules.page_replacement_module import PageReplacementModule

REF = [7, 0, 1, 2, 0, 3, 0, 4, 2, 3, 0, 3, 2, 1, 2, 0, 1, 7, 0, 1]


@pytest.mark.parametrize('algorithm, faults', [('fifo', 15), ('lru', 12), ('optimal', 9)])
def test_page_replacement_textbook(algorithm, faults):
    result = PageReplacementModule().simulate(algorithm, 3, REF)
    assert result['total_page_faults'] == faults
    assert result['total_hits'] == len(REF) - faults
    assert result['hit_ratio'] == round((len(REF) - faults) / len(REF), 4)


def test_clock_second_chance():
    result = PageReplacementModule().simulate('clock', 3, REF)
    assert 9 <= result['total_page_faults'] <= len(REF)
    assert all(len(s['memory_after']) <= 3 for s in result['steps'])
    assert all('reference_bits' in s and 'hand' in s for s in result['steps'])


def test_optimal_never_worse_than_others():
    import random
    rng = random.Random(3)
    pm = PageReplacementModule()
    for _ in range(40):
        refs = [rng.randint(0, 6) for _ in range(rng.randint(1, 30))]
        frames = rng.randint(1, 5)
        best = pm.simulate('optimal', frames, refs)['total_page_faults']
        for other in ('fifo', 'lru', 'clock'):
            assert best <= pm.simulate(other, frames, refs)['total_page_faults']


def test_lru_keeps_frame_positions_on_hit():
    result = PageReplacementModule().simulate('lru', 3, [1, 2, 3, 1])
    assert result['steps'][-1]['memory_after'] == [1, 2, 3]
    assert not result['steps'][-1]['page_fault']


def test_belady_anomaly_fifo():
    refs = [1, 2, 3, 4, 1, 2, 5, 1, 2, 3, 4, 5]
    pm = PageReplacementModule()
    assert pm.simulate('fifo', 3, refs)['total_page_faults'] == 9
    assert pm.simulate('fifo', 4, refs)['total_page_faults'] == 10


@pytest.mark.parametrize('args', [
    ('bogus', 3, [1]), ('fifo', 0, [1]), ('fifo', 3, []), ('fifo', 3, [-1]),
    ('fifo', 'x', [1]), ('fifo', 3, None), ('fifo', 3, ['a']), (None, 3, [1]),
])
def test_page_replacement_validation(args):
    with pytest.raises(ValidationError):
        PageReplacementModule().simulate(*args)


BLOCKS, PROCS = [100, 500, 200, 300, 600], [212, 417, 112, 426]


def blocks_of(result):
    return [a['block'] for a in result['allocation']]


def test_first_best_worst_next_fit():
    m = MemoryAllocationModule()
    assert blocks_of(m.allocate_memory(BLOCKS, PROCS, 'first')) == [2, 5, 2, None]
    assert blocks_of(m.allocate_memory(BLOCKS, PROCS, 'best')) == [4, 2, 3, 5]
    assert blocks_of(m.allocate_memory(BLOCKS, PROCS, 'worst')) == [5, 2, 5, None]
    assert blocks_of(m.allocate_memory(BLOCKS, PROCS, 'next')) == [2, 5, 5, None]


def test_summary_and_block_status():
    result = MemoryAllocationModule().allocate_memory([100, 200, 300], [150, 250, 500], 'best')
    assert blocks_of(result) == [2, 3, None]
    assert result['summary'] == {'allocated_count': 2, 'unallocated_count': 1,
                                 'total_free': 200, 'largest_free_block': 100}
    assert result['final_block_status'][0]['is_free']


def test_allocation_never_overcommits():
    import random
    rng = random.Random(5)
    for strategy in ('first', 'best', 'worst', 'next'):
        for _ in range(30):
            blocks = [rng.randint(10, 100) for _ in range(rng.randint(1, 6))]
            procs = [rng.randint(1, 60) for _ in range(rng.randint(1, 8))]
            result = MemoryAllocationModule().allocate_memory(blocks, procs, strategy)
            assert all(b['remaining'] >= 0 for b in result['final_block_status'])


@pytest.mark.parametrize('args', [
    ([], [1], 'best'), ([1], [], 'best'), ([1], [1], 'bogus'), ([0], [1], 'best'),
    ([1], [-5], 'best'), (None, [1], 'best'), ([1], [1], None), (['a'], [1], 'best'),
])
def test_memory_validation(args):
    with pytest.raises(ValidationError):
        MemoryAllocationModule().allocate_memory(*args)
