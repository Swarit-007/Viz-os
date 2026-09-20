"""Page replacement module: FIFO, LRU, Optimal and Clock (second chance)."""

from typing import Any, Dict, List

from .common import MAX_FRAMES, MAX_PAGE_REQUESTS, ValidationError, require_int, require_int_list

ALGORITHMS = ('fifo', 'lru', 'optimal', 'clock')
LABELS = {'fifo': 'FIFO', 'lru': 'LRU', 'optimal': 'Optimal', 'clock': 'Clock'}


class PageReplacementModule:
    def simulate(self, algorithm: str, frames: int, page_requests: List[int]) -> Dict[str, Any]:
        """Simulate a page replacement algorithm.

        Args:
            algorithm: one of fifo, lru, optimal, clock (case-insensitive)
            frames: number of physical frames (>= 1)
            page_requests: reference string of non-negative page numbers
        """
        if not isinstance(algorithm, str) or algorithm.lower() not in ALGORITHMS:
            raise ValidationError(
                f'Unknown algorithm: {algorithm}. Must be one of: {", ".join(ALGORITHMS)}')
        algorithm = algorithm.lower()
        frames = require_int(frames, 'frames', 1, MAX_FRAMES)
        pages = require_int_list(page_requests, 'page_requests', 0, MAX_PAGE_REQUESTS)

        # `memory` is ordered oldest -> newest for FIFO/LRU/Optimal and by
        # physical frame slot for Clock.
        memory: List[int] = []
        last_used: Dict[int, int] = {}
        ref_bits: List[int] = []
        hand = 0
        faults = 0
        steps = []

        for i, page in enumerate(pages):
            step = {
                'step': i + 1,
                'requested_page': page,
                'memory_before': memory.copy(),
                'page_fault': False,
                'replaced_page': None,
                'memory_after': None,
                'description': '',
            }

            if page in memory:
                if algorithm == 'lru':
                    step['description'] = f'Page {page} already in memory, marked most recently used'
                elif algorithm == 'clock':
                    ref_bits[memory.index(page)] = 1
                    step['description'] = f'Page {page} already in memory, reference bit set'
                else:
                    step['description'] = f'Page {page} already in memory, no page fault'
            else:
                faults += 1
                step['page_fault'] = True
                if len(memory) < frames:
                    memory.append(page)
                    if algorithm == 'clock':
                        ref_bits.append(1)
                    step['description'] = f'Page {page} added to memory (memory not full)'
                elif algorithm == 'clock':
                    while ref_bits[hand]:
                        ref_bits[hand] = 0
                        hand = (hand + 1) % frames
                    victim = memory[hand]
                    memory[hand] = page
                    ref_bits[hand] = 1
                    hand = (hand + 1) % frames
                    step['replaced_page'] = victim
                    step['description'] = (
                        f'Page fault: Clock replaced page {victim} with page {page}')
                else:
                    victim = self._pick_victim(algorithm, memory, pages, i, last_used)
                    memory.remove(victim)
                    memory.append(page)
                    step['replaced_page'] = victim
                    step['description'] = (
                        f'Page fault: Replaced page {victim} with page {page} ({LABELS[algorithm]})')

            last_used[page] = i
            step['memory_after'] = memory.copy()
            if algorithm == 'clock':
                step['reference_bits'] = ref_bits.copy()
                step['hand'] = hand
            steps.append(step)

        total = len(pages)
        return {
            'success': True,
            'algorithm': LABELS[algorithm],
            'frames': frames,
            'page_requests': pages,
            'total_page_faults': faults,
            'total_hits': total - faults,
            'hit_ratio': round((total - faults) / total, 4),
            'fault_ratio': round(faults / total, 4),
            'steps': steps,
            'final_memory': memory,
        }

    @staticmethod
    def _pick_victim(algorithm: str, memory: List[int], pages: List[int], now: int,
                     last_used: Dict[int, int]) -> int:
        """Choose the page to evict for FIFO, LRU or Optimal."""
        if algorithm == 'fifo':
            return memory[0]
        if algorithm == 'lru':
            return min(memory, key=lambda p: last_used[p])
        future = pages[now + 1:]
        # Evict the page used farthest in the future; never-used-again pages win immediately.
        def next_use(p: int) -> float:
            return future.index(p) if p in future else float('inf')
        return max(memory, key=next_use)

    # Convenience wrappers kept for backwards compatibility.
    def simulate_fifo(self, frames: int, page_requests: List[int]) -> Dict[str, Any]:
        return self.simulate('fifo', frames, page_requests)

    def simulate_lru(self, frames: int, page_requests: List[int]) -> Dict[str, Any]:
        return self.simulate('lru', frames, page_requests)
