"""Memory allocation: partition fit strategies, the buddy system and segmentation."""

from typing import Any, Dict, List

from ..core import Choice, Col, Int, IntList, Lines, Table, Trace, ValidationError, algorithm, result, tile

# --------------------------------------------------------------------------- partition fits
FIT_NAMES = {'first': 'First Fit', 'best': 'Best Fit', 'worst': 'Worst Fit', 'next': 'Next Fit'}
FIT_TEXT = {
    'first': ('take the first block that is large enough', 'Fast; fragments the start of memory.'),
    'best': ('take the smallest block that is large enough', 'Leaves the smallest leftover per request but creates many tiny useless holes.'),
    'worst': ('take the largest block', 'Leaves big leftovers that can still be reused, but wastes large blocks early.'),
    'next': ('scan from where the last allocation ended and take the first block that fits', 'Spreads allocations out; ignores the start of memory.'),
}
BLOCKS = [100, 500, 200, 300, 600]
PROCS = [212, 417, 112, 426]


def _fit(strategy):
    def run(p):
        blocks, procs = p['blocks'], p['procs']
        free = list(blocks)
        allocs: List[List[Dict[str, Any]]] = [[] for _ in blocks]
        last = 0
        trace, snaps = Trace(), []
        failed = 0
        for k, size in enumerate(procs):
            name = f'P{k + 1}'
            fits = [i for i, b in enumerate(free) if b >= size]
            pick = None
            if fits:
                if strategy == 'first':
                    pick = fits[0]
                elif strategy == 'best':
                    pick = min(fits, key=lambda i: (free[i], i))
                elif strategy == 'worst':
                    pick = max(fits, key=lambda i: (free[i], -i))
                else:
                    pick = next((i for i in fits if i >= last), fits[0])
            if pick is None:
                failed += 1
                trace.add(f'{name} needs {size}: no block is large enough. Allocation fails.', [0, 1, 4], k)
            else:
                free[pick] -= size
                allocs[pick].append({'name': name, 'size': size})
                last = pick
                trace.add(f'{name} needs {size}: candidates are blocks {", ".join(str(i + 1) for i in fits)}. Block {pick + 1} is chosen; {free[pick]} is left over.',
                          [0, 1, 2, 3], k)
            snaps.append({'blocks': [{'size': blocks[i], 'free': free[i], 'allocs': [dict(a) for a in allocs[i]]} for i in range(len(blocks))],
                          'placed': pick, 'name': name})
        total_free = sum(free)
        largest = max(free)
        summary = [tile('Allocated', len(procs) - failed, tone='good'), tile('Failed', failed, tone='bad' if failed else None),
                   tile('Total free', total_free), tile('Largest free block', largest, 'external fragmentation')]
        verdict = None
        if failed and total_free >= min(procs):
            verdict = {'ok': False, 'label': 'External fragmentation', 'text': f'{total_free} units are free in total, but no single block can hold the failed request.'}
        return result(f'fit-{strategy}', 'partitions', summary, trace, {'blocks': blocks, 'snapshots': snaps}, None, verdict)

    verb, note = FIT_TEXT[strategy]
    algorithm(id=f'fit-{strategy}', name=FIT_NAMES[strategy], category='memory', family='fit', viz='partitions',
              summary=f'Place each process into a fixed partition: {verb}.',
              complexity={'time': 'O(processes x blocks)', 'space': 'O(blocks)', 'note': ''},
              pseudocode=['for each process, in order:', '    candidates = blocks with free space >= process size', f'    {verb}',
                          '    shrink that block by the process size', '    if there is no candidate: the allocation fails'],
              params=[IntList('blocks', 'Block sizes', BLOCKS, 1, 5000, 1, 12), IntList('procs', 'Process sizes', PROCS, 1, 5000, 1, 16)],
              example={'blocks': BLOCKS, 'procs': PROCS},
              random=lambda rng: {'blocks': [rng.randint(4, 60) * 10 for _ in range(rng.randint(4, 6))], 'procs': [rng.randint(4, 55) * 10 for _ in range(rng.randint(4, 6))]},
              notes=[note], tags=['fragmentation'])(run)


for _f in FIT_NAMES:
    _fit(_f)


# --------------------------------------------------------------------------- buddy system
def _parse_ops(lines):
    ops = []
    for i, raw in enumerate(lines):
        parts = raw.split()
        if parts and parts[0] == 'alloc' and len(parts) == 3 and parts[2].isdigit():
            ops.append({'op': 'alloc', 'name': parts[1], 'size': int(parts[2])})
        elif parts and parts[0] == 'free' and len(parts) == 2:
            ops.append({'op': 'free', 'name': parts[1]})
        else:
            raise ValidationError(f'Line {i + 1}: write "alloc NAME SIZE" or "free NAME"')
    return ops


@algorithm(id='buddy', name='Buddy System', category='memory', viz='memory', family='buddy',
           summary='Memory is split into power-of-two blocks. Requests round up; freed blocks merge with their buddy.',
           complexity={'time': 'O(log n) per operation', 'space': 'O(n)', 'note': 'n = memory size / minimum block.'},
           pseudocode=['alloc(size):', '    n = size rounded up to a power of two (at least the minimum block)', '    find the smallest free block >= n',
                       '    while block > n: split it into two buddies', '    mark the block used', 'free(block):', '    mark the block free',
                       '    while its buddy is also free: merge the two into one block'],
           params=[Choice('memory', 'Total memory', [(str(n), str(n)) for n in (256, 512, 1024, 2048)], '1024'),
                   Choice('min_block', 'Smallest block', [(str(n), str(n)) for n in (8, 16, 32, 64)], '32'),
                   Lines('ops', 'Operations', ['alloc A 100', 'alloc B 240', 'alloc C 64', 'alloc D 60', 'free B', 'free A', 'free C', 'free D'],
                         hint='alloc NAME SIZE, or free NAME', placeholder='alloc A 100')],
           example={'memory': '1024', 'min_block': '32', 'ops': ['alloc A 100', 'alloc B 240', 'alloc C 64', 'alloc D 60', 'free B', 'free A', 'free C', 'free D']},
           random=lambda rng: {'memory': '1024', 'min_block': '32', 'ops': _random_buddy_ops(rng)},
           notes=['Internal fragmentation is the rounding waste inside a block; external fragmentation is limited because buddies re-merge.',
                  'Address arithmetic makes finding a buddy a single XOR.'], tags=['fragmentation'])
def buddy(p):
    memory, min_block = int(p['memory']), int(p['min_block'])
    ops = _parse_ops(p['ops'])
    free: Dict[int, List[int]] = {memory: [0]}
    live: Dict[str, Dict[str, int]] = {}
    trace, snaps = Trace(), []

    def blocks():
        out = [{'start': b['start'], 'size': b['size'], 'label': n, 'kind': 'used', 'waste': b['size'] - b['req']} for n, b in live.items()]
        out += [{'start': s, 'size': size, 'label': '', 'kind': 'free', 'waste': 0} for size, starts in free.items() for s in starts]
        return sorted(out, key=lambda b: b['start'])

    def tidy():
        for k in [k for k, v in free.items() if not v]:
            del free[k]
    failures = 0
    for k, op in enumerate(ops):
        notes, lines = [], []
        if op['op'] == 'alloc':
            if op['name'] in live:
                raise ValidationError(f'{op["name"]} is already allocated')
            if op['size'] < 1 or op['size'] > memory:
                raise ValidationError(f'Request {op["size"]} is outside 1..{memory}')
            size = max(min_block, 1 << (op['size'] - 1).bit_length())
            lines += [0, 1, 2]
            donor = next((s for s in sorted(free) if s >= size and free[s]), None)
            if donor is None:
                failures += 1
                notes.append(f'No free block of {size} or larger. {op["name"]} cannot be allocated.')
            else:
                start = free[donor].pop(0)
                while donor > size:
                    donor //= 2
                    free.setdefault(donor, []).append(start + donor)
                    free[donor].sort()
                    notes.append(f'Split into two buddies of {donor}.')
                    lines.append(3)
                tidy()
                live[op['name']] = {'start': start, 'size': size, 'req': op['size']}
                notes.append(f'{op["name"]} gets {size} at {start} (asked {op["size"]}, wasted {size - op["size"]}).')
                lines.append(4)
        else:
            if op['name'] not in live:
                raise ValidationError(f'{op["name"]} is not allocated')
            b = live.pop(op['name'])
            start, size = b['start'], b['size']
            notes.append(f'{op["name"]} frees its block of {size} at {start}.')
            lines += [5, 6]
            while size < memory and (start ^ size) in free.get(size, []):
                free[size].remove(start ^ size)
                start = min(start, start ^ size)
                size *= 2
                notes.append(f'Buddy is free too: merge into {size} at {start}.')
                lines.append(7)
            free.setdefault(size, []).append(start)
            free[size].sort()
            tidy()
        snaps.append({'blocks': blocks(), 'mark': None})
        trace.add(f'{op["op"]} {op["name"]}: ' + ' '.join(notes), lines, k)
    last = snaps[-1]['blocks']
    waste = sum(b['waste'] for b in last)
    free_total = sum(b['size'] for b in last if b['kind'] == 'free')
    summary = [tile('Internal waste', waste, 'rounding inside blocks'), tile('Free memory', free_total),
               tile('Largest free block', max((b['size'] for b in last if b['kind'] == 'free'), default=0)), tile('Failed allocations', failures, tone='bad' if failures else None)]
    return result('buddy', 'memory', summary, trace, {'size': memory, 'initial': [{'start': 0, 'size': memory, 'label': '', 'kind': 'free', 'waste': 0}],
                                                       'snapshots': snaps})


def _random_buddy_ops(rng):
    """Sizes stay at or below 1/8 of memory and at most 5 blocks are live, so every allocation succeeds."""
    live, out = [], []
    for i in range(rng.randint(8, 12)):
        if live and (len(live) >= 5 or rng.random() < 0.4):
            out.append(f'free {live.pop(rng.randrange(len(live)))}')
        else:
            name = chr(65 + i)
            out.append(f'alloc {name} {rng.randint(10, 128)}')
            live.append(name)
    return out


# --------------------------------------------------------------------------- segmentation
SEGS = [{'id': 'code', 'base': 0, 'limit': 300}, {'id': 'data', 'base': 500, 'limit': 200}, {'id': 'stack', 'base': 800, 'limit': 150}]


@algorithm(id='segmentation', name='Segmentation', category='memory', viz='memory', family='translate',
           summary='A logical address is (segment, offset). The segment table gives a base and limit; offsets beyond the limit fault.',
           complexity={'time': 'O(1) per access', 'space': 'O(segments)', 'note': ''},
           pseudocode=['translate(segment, offset):', '    entry = segment_table[segment]', '    if the segment does not exist: fault',
                       '    if offset >= entry.limit: segmentation fault', '    return entry.base + offset'],
           params=[Int('memory', 'Memory size', 1000, 100, 100000),
                   Table('segments', 'Segment table', [Col('name', 'Name', kind='text'), Col('base', 'Base', 0, 100000), Col('limit', 'Limit', 1, 100000)],
                         [{'id': 'code', 'name': 'code', 'base': 0, 'limit': 300}, {'id': 'data', 'name': 'data', 'base': 500, 'limit': 200},
                          {'id': 'stack', 'name': 'stack', 'base': 800, 'limit': 150}], max_rows=8, id_prefix='S'),
                   Lines('accesses', 'Logical addresses', ['code 10', 'data 199', 'data 200', 'stack 149', 'heap 0'], hint='SEGMENT OFFSET')],
           example={'memory': 1000, 'segments': [{'id': 'code', 'name': 'code', 'base': 0, 'limit': 300}, {'id': 'data', 'name': 'data', 'base': 500, 'limit': 200},
                                                  {'id': 'stack', 'name': 'stack', 'base': 800, 'limit': 150}], 'accesses': ['code 10', 'data 199', 'data 200', 'stack 149', 'heap 0']},
           random=lambda rng: _random_segments(rng),
           notes=['Segments match how programmers think (code, data, stack) but cause external fragmentation.', 'Hardware raises a trap when the offset reaches the limit.'],
           tags=['protection'])
def segmentation(p):
    memory = p['memory']
    segs = p['segments']
    by = {}
    for s in segs:
        if s['name'] in by:
            raise ValidationError('segment names must be unique')
        if s['base'] + s['limit'] > memory:
            raise ValidationError(f'{s["name"]} extends past the end of memory')
        by[s['name']] = s
    ordered = sorted(segs, key=lambda s: s['base'])
    for a, b in zip(ordered, ordered[1:]):
        if a['base'] + a['limit'] > b['base']:
            raise ValidationError(f'segments {a["name"]} and {b["name"]} overlap')
    blocks, cur = [], 0
    for s in ordered:
        if s['base'] > cur:
            blocks.append({'start': cur, 'size': s['base'] - cur, 'label': '', 'kind': 'free', 'waste': 0})
        blocks.append({'start': s['base'], 'size': s['limit'], 'label': s['name'], 'kind': 'used', 'waste': 0})
        cur = s['base'] + s['limit']
    if cur < memory:
        blocks.append({'start': cur, 'size': memory - cur, 'label': '', 'kind': 'free', 'waste': 0})
    trace, snaps, faults, rows = Trace(), [], 0, []
    for k, line in enumerate(p['accesses']):
        parts = line.split()
        if len(parts) != 2 or not parts[1].isdigit():
            raise ValidationError(f'Access {k + 1}: write "SEGMENT OFFSET"')
        name, off = parts[0], int(parts[1])
        seg = by.get(name)
        if seg is None:
            faults += 1
            note, lines, mark, res = f'({name}, {off}): there is no segment {name}. Fault.', [0, 1, 2], None, 'fault: no such segment'
        elif off >= seg['limit']:
            faults += 1
            note, lines, mark, res = f'({name}, {off}): offset {off} is not below the limit {seg["limit"]}. Segmentation fault.', [0, 1, 3], None, 'fault: beyond limit'
        else:
            mark = seg['base'] + off
            note, lines, res = f'({name}, {off}): {seg["base"]} + {off} = {mark}. Inside the limit {seg["limit"]}.', [0, 1, 3, 4], f'{mark}'
        snaps.append({'blocks': blocks, 'mark': mark})
        rows.append([{'proc': name[:6]}, off, mark if mark is not None else '-', res])
        trace.add(note, lines, k)
    holes = [b['size'] for b in blocks if b['kind'] == 'free']
    summary = [tile('Accesses', len(p['accesses'])), tile('Faults', faults, tone='bad' if faults else 'good'), tile('Free memory', sum(holes)),
               tile('Largest hole', max(holes, default=0))]
    return result('segmentation', 'memory', summary, trace, {'size': memory, 'initial': blocks, 'snapshots': snaps}, {'title': 'Translations', 'headers': ['Segment', 'Offset', 'Physical', 'Result'], 'rows': rows})


def _random_segments(rng):
    names = ['code', 'data', 'stack', 'heap', 'lib'][:rng.randint(3, 5)]
    rows, cur = [], rng.randint(0, 60)
    for n in names:
        limit = rng.randint(80, 180)
        rows.append({'id': n, 'name': n, 'base': cur, 'limit': limit})
        cur += limit + rng.randint(0, 40)
    return {'memory': 1000, 'segments': rows, 'accesses': [f'{r["name"]} {rng.randint(0, int(r["limit"] * 1.3))}' for r in (rng.choice(rows) for _ in range(8))]}
