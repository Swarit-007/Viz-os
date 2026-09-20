"""File allocation methods on a simulated disk: contiguous, linked and indexed."""

from typing import Any, Dict, List

from .common import MAX_PROCESSES, ValidationError, require_int, require_int_list

MAX_BLOCKS = 256


class FileAllocationModule:
    def simulate(self, total_blocks: Any = 32, files: Any = None, used_blocks: Any = None) -> Dict[str, Any]:
        """Allocate the same files with all three methods so they can be compared.

        Args:
            total_blocks: disk size in blocks
            files: [{"name": "A", "size": 4}, ...] allocated in order (size in blocks)
            used_blocks: block numbers (0-based) already occupied, to pre-fragment the disk

        contiguous: needs one run of `size` free blocks (first fit); fails on external fragmentation.
        linked: takes any free blocks in order; each block points to the next, so reaching
            block k reads k + 1 blocks.
        indexed: one extra index block lists every data block; reaching any block reads 2.
        """
        total = require_int(total_blocks, 'total_blocks', 4, MAX_BLOCKS)
        if not isinstance(files, list) or not files or len(files) > MAX_PROCESSES:
            raise ValidationError(f'files must be a list of 1 to {MAX_PROCESSES} entries')
        parsed = []
        for i, f in enumerate(files):
            if not isinstance(f, dict):
                raise ValidationError(f'file {i + 1} must be an object')
            name = str(f.get('name', f'F{i + 1}'))
            parsed.append({'name': name, 'size': require_int(f.get('size'), f'{name} size', 1, total)})
        if len({f['name'] for f in parsed}) != len(parsed):
            raise ValidationError('file names must be unique')
        used = require_int_list(used_blocks, 'used_blocks', 0) if used_blocks else []
        if any(b >= total for b in used):
            raise ValidationError(f'used_blocks must be below total_blocks ({total})')

        return {
            'success': True, 'totalBlocks': total, 'usedBlocks': sorted(set(used)),
            'methods': {
                'contiguous': self._contiguous(total, parsed, set(used)),
                'linked': self._linked(total, parsed, set(used)),
                'indexed': self._indexed(total, parsed, set(used)),
            },
        }

    @staticmethod
    def _initial_map(total: int, used: set) -> List[Dict[str, Any]]:
        return [{'index': i, 'state': 'reserved' if i in used else 'free', 'file': None, 'next': None,
                 'role': None} for i in range(total)]

    @staticmethod
    def _finish(blocks: List[Dict[str, Any]], placed: List[Dict[str, Any]], failed: List[str]) -> Dict[str, Any]:
        free = [b['index'] for b in blocks if b['state'] == 'free']
        runs, run = [], 0
        for b in blocks:
            run = run + 1 if b['state'] == 'free' else 0
            if run:
                if run == 1:
                    runs.append(1)
                else:
                    runs[-1] = run
        return {'blocks': blocks, 'files': placed, 'failed': failed, 'freeBlocks': len(free),
                'largestFreeRun': max(runs, default=0), 'freeRuns': len(runs)}

    def _contiguous(self, total, files, used):
        blocks = self._initial_map(total, used)
        placed, failed = [], []
        for f in files:
            start = None
            run = 0
            for b in blocks:
                run = run + 1 if b['state'] == 'free' else 0
                if run == f['size']:
                    start = b['index'] - f['size'] + 1
                    break
            if start is None:
                failed.append(f['name'])
                continue
            for i in range(start, start + f['size']):
                blocks[i].update(state='file', file=f['name'], role='data')
            placed.append({'name': f['name'], 'size': f['size'], 'blocks': list(range(start, start + f['size'])),
                           'start': start, 'seekCost': 1, 'lastBlockReads': 1})
        return self._finish(blocks, placed, failed)

    def _linked(self, total, files, used):
        blocks = self._initial_map(total, used)
        placed, failed = [], []
        for f in files:
            free = [b['index'] for b in blocks if b['state'] == 'free'][:f['size']]
            if len(free) < f['size']:
                failed.append(f['name'])
                continue
            for pos, i in enumerate(free):
                blocks[i].update(state='file', file=f['name'], role='data',
                                 next=free[pos + 1] if pos + 1 < len(free) else None)
            placed.append({'name': f['name'], 'size': f['size'], 'blocks': free, 'start': free[0],
                           'seekCost': f['size'], 'lastBlockReads': f['size']})
        return self._finish(blocks, placed, failed)

    def _indexed(self, total, files, used):
        blocks = self._initial_map(total, used)
        placed, failed = [], []
        for f in files:
            free = [b['index'] for b in blocks if b['state'] == 'free'][:f['size'] + 1]
            if len(free) < f['size'] + 1:
                failed.append(f['name'])
                continue
            index_block, data = free[0], free[1:]
            blocks[index_block].update(state='file', file=f['name'], role='index', next=None)
            for i in data:
                blocks[i].update(state='file', file=f['name'], role='data')
            placed.append({'name': f['name'], 'size': f['size'], 'blocks': data, 'indexBlock': index_block,
                           'start': index_block, 'seekCost': 2, 'lastBlockReads': 2})
        return self._finish(blocks, placed, failed)
