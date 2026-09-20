"""Buddy-system allocation and segmentation address translation."""

from typing import Any, Dict, List

from .common import MAX_PROCESSES, ValidationError, require_int


def _is_power_of_two(n: int) -> bool:
    return n > 0 and n & (n - 1) == 0


class BuddyModule:
    def simulate(self, memory_size: Any = 1024, min_block: Any = 32, operations: Any = None) -> Dict[str, Any]:
        """Run a sequence of alloc / free operations on a buddy-system allocator.

        operations: [{"op": "alloc", "name": "A", "size": 100}, {"op": "free", "name": "A"}]
        Requests round up to the next power of two (>= min_block); the difference is
        internal fragmentation. Freed blocks merge with their buddy when it is also free.
        """
        memory_size = require_int(memory_size, 'memory_size', 2, 65536)
        min_block = require_int(min_block, 'min_block', 1, memory_size)
        if not _is_power_of_two(memory_size) or not _is_power_of_two(min_block):
            raise ValidationError('memory_size and min_block must be powers of two')
        if not isinstance(operations, list) or not operations or len(operations) > MAX_PROCESSES:
            raise ValidationError(f'operations must be a list of 1 to {MAX_PROCESSES} entries')

        free: Dict[int, List[int]] = {memory_size: [0]}  # block size -> sorted start addresses
        allocated: Dict[str, Dict[str, int]] = {}        # name -> {start, size, requested}
        steps = []

        def snapshot() -> List[Dict[str, Any]]:
            blocks = [{'start': a['start'], 'size': a['size'], 'status': 'used', 'name': n,
                       'requested': a['requested']} for n, a in allocated.items()]
            blocks += [{'start': s, 'size': size, 'status': 'free', 'name': None, 'requested': 0}
                       for size, starts in free.items() for s in starts]
            return sorted(blocks, key=lambda b: b['start'])

        for index, op in enumerate(operations, start=1):
            if not isinstance(op, dict) or op.get('op') not in ('alloc', 'free'):
                raise ValidationError(f'operation {index} must have op "alloc" or "free"')
            name = str(op.get('name', ''))
            if not name:
                raise ValidationError(f'operation {index} needs a name')
            detail: List[str] = []
            ok = True

            if op['op'] == 'alloc':
                requested = require_int(op.get('size'), f'operation {index} size', 1, memory_size)
                if name in allocated:
                    raise ValidationError(f'{name} is already allocated')
                size = max(min_block, 1 << (requested - 1).bit_length())
                donor = next((s for s in sorted(free) if s >= size and free[s]), None)
                if donor is None:
                    ok = False
                    detail.append(f'No free block of {size} or larger: allocation of {name} fails')
                else:
                    start = free[donor].pop(0)
                    while donor > size:
                        donor //= 2
                        free.setdefault(donor, []).append(start + donor)
                        free[donor].sort()
                        detail.append(f'Split block at {start} into two blocks of {donor}')
                    for s in [k for k, v in free.items() if not v]:
                        del free[s]
                    allocated[name] = {'start': start, 'size': size, 'requested': requested}
                    detail.append(f'Allocate {size} at {start} for {name} '
                                  f'(requested {requested}, wasted {size - requested})')
            else:
                if name not in allocated:
                    raise ValidationError(f'{name} is not allocated')
                block = allocated.pop(name)
                start, size = block['start'], block['size']
                detail.append(f'Free {name}: block of {size} at {start}')
                while size < memory_size:
                    buddy = start ^ size
                    if buddy in free.get(size, []):
                        free[size].remove(buddy)
                        start = min(start, buddy)
                        size *= 2
                        detail.append(f'Merge with buddy at {buddy} into block of {size} at {start}')
                    else:
                        break
                free.setdefault(size, []).append(start)
                free[size].sort()
                for s in [k for k, v in free.items() if not v]:
                    del free[s]

            blocks = snapshot()
            used = [b for b in blocks if b['status'] == 'used']
            steps.append({
                'step': index, 'op': op['op'], 'name': name, 'ok': ok, 'detail': detail, 'blocks': blocks,
                'internalFragmentation': sum(b['size'] - b['requested'] for b in used),
                'freeMemory': sum(b['size'] for b in blocks if b['status'] == 'free'),
                'largestFree': max((b['size'] for b in blocks if b['status'] == 'free'), default=0),
            })

        return {'success': True, 'memorySize': memory_size, 'minBlock': min_block, 'steps': steps,
                'final': steps[-1]['blocks']}

    def segmentation(self, memory_size: Any = 1000, segments: Any = None, accesses: Any = None) -> Dict[str, Any]:
        """Translate (segment, offset) logical addresses through a segment table.

        segments: [{"name": "code", "base": 0, "limit": 300}, ...]. An access faults when
        the segment does not exist or offset >= limit. Overlapping segments are rejected.
        """
        memory_size = require_int(memory_size, 'memory_size', 1, 1_000_000)
        if not isinstance(segments, list) or not segments or len(segments) > 20:
            raise ValidationError('segments must be a list of 1 to 20 entries')
        table = []
        for i, seg in enumerate(segments):
            if not isinstance(seg, dict):
                raise ValidationError(f'segment {i + 1} must be an object')
            name = str(seg.get('name', f'S{i}'))
            base = require_int(seg.get('base'), f'{name} base', 0, memory_size)
            limit = require_int(seg.get('limit'), f'{name} limit', 1, memory_size)
            if base + limit > memory_size:
                raise ValidationError(f'{name} extends past the end of memory ({memory_size})')
            table.append({'index': i, 'name': name, 'base': base, 'limit': limit})
        if len({t['name'] for t in table}) != len(table):
            raise ValidationError('segment names must be unique')
        ordered = sorted(table, key=lambda t: t['base'])
        for a, b in zip(ordered, ordered[1:]):
            if a['base'] + a['limit'] > b['base']:
                raise ValidationError(f'segments {a["name"]} and {b["name"]} overlap')
        if not isinstance(accesses, list) or not accesses or len(accesses) > MAX_PROCESSES:
            raise ValidationError(f'accesses must be a list of 1 to {MAX_PROCESSES} entries')

        by_name = {t['name']: t for t in table}
        results = []
        for i, acc in enumerate(accesses, start=1):
            if not isinstance(acc, dict):
                raise ValidationError(f'access {i} must be an object')
            name = str(acc.get('segment', ''))
            offset = require_int(acc.get('offset'), f'access {i} offset', 0)
            seg = by_name.get(name)
            if seg is None:
                results.append({'segment': name, 'offset': offset, 'ok': False, 'physical': None,
                                'reason': f'Segment {name} does not exist'})
            elif offset >= seg['limit']:
                results.append({'segment': name, 'offset': offset, 'ok': False, 'physical': None,
                                'reason': f'Segmentation fault: offset {offset} is not below limit {seg["limit"]}'})
            else:
                results.append({'segment': name, 'offset': offset, 'ok': True, 'physical': seg['base'] + offset,
                                'reason': f'{seg["base"]} + {offset} = {seg["base"] + offset}'})

        layout, cursor = [], 0
        for seg in ordered:
            if seg['base'] > cursor:
                layout.append({'kind': 'hole', 'base': cursor, 'size': seg['base'] - cursor})
            layout.append({'kind': 'segment', 'name': seg['name'], 'base': seg['base'], 'size': seg['limit']})
            cursor = seg['base'] + seg['limit']
        if cursor < memory_size:
            layout.append({'kind': 'hole', 'base': cursor, 'size': memory_size - cursor})
        holes = [b['size'] for b in layout if b['kind'] == 'hole']

        return {'success': True, 'memorySize': memory_size, 'table': table, 'accesses': results,
                'layout': layout, 'freeMemory': sum(holes), 'largestHole': max(holes, default=0),
                'faults': sum(1 for r in results if not r['ok'])}
