"""Memory allocation module: First Fit, Best Fit, Worst Fit and Next Fit."""

from typing import Any, Dict, List, Optional

from .common import MAX_PROCESSES, ValidationError, require_int_list

STRATEGIES = ('first', 'best', 'worst', 'next')


class MemoryAllocationModule:
    def allocate_memory(self, blocks: List[int], processes: List[int],
                        strategy: str = 'best') -> Dict[str, Any]:
        """Place each process into a memory block using the chosen strategy.

        Args:
            blocks: block sizes (positive integers)
            processes: process sizes (positive integers)
            strategy: first, best, worst or next (case-insensitive)
        """
        if not isinstance(strategy, str) or strategy.lower() not in STRATEGIES:
            raise ValidationError(
                f'Unknown strategy: {strategy}. Must be one of: {", ".join(STRATEGIES)}')
        strategy = strategy.lower()
        blocks = require_int_list(blocks, 'blocks', 1, MAX_PROCESSES)
        processes = require_int_list(processes, 'processes', 1, MAX_PROCESSES)

        remaining = blocks.copy()
        allocation, steps = [], []
        last_index = 0  # Next Fit resumes searching from the last allocation

        for number, size in enumerate(processes, start=1):
            index = self._choose_block(strategy, remaining, size, last_index)
            step = {'process_index': number, 'process': size, 'status': 'not_allocated',
                    'block': None, 'description': ''}
            if index is None:
                allocation.append({'process': size, 'block': None})
                step['description'] = f'Process {size} cannot be allocated - no free block available'
            else:
                remaining[index] -= size
                last_index = index
                allocation.append({'process': size, 'block': index + 1})
                step.update(status='allocated', block=index + 1, description=(
                    f'Process {size} allocated to block {index + 1} (remaining: {remaining[index]})'))
            steps.append(step)

        final_block_status = [
            {'block_number': i + 1, 'size': original, 'allocated': original - left,
             'remaining': left, 'is_free': left == original}
            for i, (original, left) in enumerate(zip(blocks, remaining))
        ]
        failed = sum(1 for a in allocation if a['block'] is None)

        return {
            'success': True,
            'strategy': strategy,
            'blocks': blocks,
            'processes': processes,
            'allocation': allocation,
            'steps': steps,
            'final_block_status': final_block_status,
            'summary': {
                'allocated_count': len(processes) - failed,
                'unallocated_count': failed,
                'total_free': sum(remaining),
                'largest_free_block': max(remaining),
            },
        }

    @staticmethod
    def _choose_block(strategy: str, blocks: List[int], size: int, start: int) -> Optional[int]:
        """Return the index of the chosen block, or None if nothing fits."""
        fits = [i for i, b in enumerate(blocks) if b >= size]
        if not fits:
            return None
        if strategy == 'first':
            return fits[0]
        if strategy == 'best':
            return min(fits, key=lambda i: (blocks[i], i))
        if strategy == 'worst':
            return max(fits, key=lambda i: (blocks[i], -i))
        # next fit: first fitting block at or after `start`, wrapping around
        return next((i for i in fits if i >= start), fits[0])
