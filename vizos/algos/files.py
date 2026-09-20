"""File systems: contiguous, linked and indexed allocation, and the Unix inode."""

from typing import Any, Dict, List

from ..core import Col, Int, IntList, Table, Trace, ValidationError, algorithm, result, tile

FILES = [{'id': 'A', 'size': 4}, {'id': 'B', 'size': 5}, {'id': 'C', 'size': 3}, {'id': 'D', 'size': 6}]
RESERVED = [2, 3, 7, 8, 12, 13, 20, 26]


def _params():
    return [Int('blocks', 'Disk blocks', 32, 8, 128), IntList('reserved', 'Reserved blocks', RESERVED, 0, 127, 0, 60, 'Already in use, so free space is fragmented.'),
            Table('files', 'Files, allocated in order', [Col('size', 'Blocks', 1, 64)], FILES, max_rows=10, id_prefix='F')]


def _random(rng):
    total = rng.choice([32, 48, 64])
    return {'blocks': total, 'reserved': sorted(set(rng.randint(0, total - 1) for _ in range(rng.randint(4, total // 3)))),
            'files': [{'id': chr(65 + i), 'size': rng.randint(2, 8)} for i in range(rng.randint(3, 6))]}


def _alloc(method):
    def run(p):
        total, reserved = p['blocks'], set(p['reserved'])
        if any(b >= total for b in reserved):
            raise ValidationError('Reserved blocks must be below the disk size')
        cells = [{'label': '', 'kind': 'reserved' if i in reserved else 'free', 'sub': ''} for i in range(total)]
        trace, snaps, placed, failed = Trace(), [], [], []
        for k, f in enumerate(p['files']):
            size = f['size']
            free = [i for i, c in enumerate(cells) if c['kind'] == 'free']
            blocks: List[int] = []
            extra = ''
            if method == 'contiguous':
                run_len, start = 0, None
                for i, c in enumerate(cells):
                    run_len = run_len + 1 if c['kind'] == 'free' else 0
                    if run_len == size:
                        start = i - size + 1
                        break
                if start is not None:
                    blocks = list(range(start, start + size))
                    extra = f'run of {size} free blocks starting at {start}'
                lines = [0, 1, 3] if blocks else [0, 1, 2]
            elif method == 'linked':
                if len(free) >= size:
                    blocks = free[:size]
                    extra = 'the first free blocks, chained by pointers'
                lines = [0, 1, 3] if blocks else [0, 1, 2]
            else:
                if len(free) >= size + 1:
                    idx, blocks = free[0], free[1:size + 1]
                    extra = f'index block {idx} plus {size} data blocks'
                lines = [0, 1, 2, 3] if blocks else [0, 1]
            if not blocks:
                failed.append(f['id'])
                reason = ('no run of %d free blocks exists (%d blocks are free but fragmented)' % (size, len(free)) if method == 'contiguous' and len(free) >= size
                          else 'not enough free blocks')
                trace.add(f'{f["id"]} ({size} blocks) fails: {reason}.', lines, k)
            else:
                for pos, b in enumerate(blocks):
                    nxt = blocks[pos + 1] if method == 'linked' and pos + 1 < len(blocks) else None
                    cells[b] = {'label': f['id'], 'owner': f['id'], 'kind': 'data', 'sub': f'to {nxt}' if nxt is not None else ''}
                if method == 'indexed':
                    cells[idx] = {'label': f'{f["id"]}*', 'owner': f['id'], 'kind': 'index', 'sub': ''}
                placed.append({'id': f['id'], 'size': size, 'blocks': blocks, 'index': idx if method == 'indexed' else None})
                trace.add(f'{f["id"]} ({size} blocks) placed in {extra}.', lines, k)
            snaps.append([dict(c) for c in cells])
        free = [c for c in cells if c['kind'] == 'free']
        runs, cur = [], 0
        for c in cells:
            cur = cur + 1 if c['kind'] == 'free' else 0
            if cur == 1:
                runs.append(1)
            elif cur:
                runs[-1] = cur
        summary = [tile('Files placed', f'{len(placed)}/{len(p["files"])}', tone='bad' if failed else 'good'), tile('Free blocks', len(free)),
                   tile('Largest free run', max(runs, default=0)), tile('Free fragments', len(runs))]
        rows = []
        for f in p['files']:
            pl = next((x for x in placed if x['id'] == f['id']), None)
            reads = 'fails' if pl is None else {'contiguous': '1', 'linked': str(pl['size']), 'indexed': '2'}[method]
            rows.append([{'proc': f['id']}, f['size'], reads])
        table = {'title': 'Reads needed to reach each file\'s last block', 'headers': ['File', 'Blocks', 'Disk reads'], 'rows': rows}
        verdict = None
        if failed:
            verdict = {'ok': False, 'label': f'{len(failed)} file(s) not placed', 'text': 'Could not place ' + ', '.join(failed) + '.'}
        return result(f'file-{method}', 'grid', summary, trace, {'columns': 8 if total <= 32 else 16, 'snapshots': snaps, 'initial': [dict(c) for c in snaps[0]] if False else None,
                                                                  'start': [{'label': '', 'kind': 'reserved' if i in reserved else 'free', 'sub': ''} for i in range(total)]}, table, verdict)

    meta = {
        'contiguous': ('Contiguous Allocation', 'Every file occupies one unbroken run of blocks. Reads are fast; free space fragments.',
                       ['for each file, in order:', '    scan the disk for a run of free blocks as long as the file', '    if none exists: allocation fails',
                        '    else: mark the whole run as the file'],
                       ['One seek reaches any block.', 'External fragmentation can reject a file even when enough blocks are free in total.']),
        'linked': ('Linked Allocation', 'Any free block will do; each block stores a pointer to the next. No fragmentation, slow random access.',
                   ['for each file, in order:', '    take the first free blocks, one per file block', '    if too few are free: allocation fails',
                    '    link each block to the next with a pointer'],
                   ['Reaching block k means following k pointers.', 'One damaged pointer loses the rest of the file.']),
        'indexed': ('Indexed Allocation', 'One index block lists every data block of a file. Random access needs just two reads.',
                    ['for each file, in order:', '    take one free block as the index block', '    take one free block per file block',
                     '    store the data block numbers in the index block'],
                    ['Any block is two reads away.', 'Small files still pay for a whole index block.']),
    }[method]
    algorithm(id=f'file-{method}', name=meta[0], category='files', family='files', viz='grid', summary=meta[1],
              complexity={'time': 'O(files x blocks)', 'space': 'O(blocks)', 'note': ''}, pseudocode=meta[2], params=_params(),
              example={'blocks': 32, 'reserved': RESERVED, 'files': FILES}, random=_random, notes=meta[3], tags=['allocation'])(run)


for _m in ('contiguous', 'linked', 'indexed'):
    _alloc(_m)


@algorithm(id='inode', name='Unix Inode', category='files', viz='inode', family='inode',
           summary='An inode holds direct pointers, then single, double and triple indirect blocks. See how big a file each level reaches.',
           complexity={'time': 'O(1)', 'space': 'O(1)', 'note': 'At most 4 disk reads per block.'},
           pseudocode=['blocks needed = ceil(file size / block size)', 'the first D blocks are reached by direct pointers',
                       'the next P blocks go through the single indirect block', 'the next P^2 blocks go through the double indirect block',
                       'the rest go through the triple indirect block', 'P = block size / pointer size'],
           params=[Int('block_size', 'Block size (bytes)', 4096, 512, 65536), Int('pointer', 'Pointer size (bytes)', 4, 2, 8), Int('direct', 'Direct pointers', 12, 1, 15),
                   Int('file_size', 'File size (KiB)', 5000, 1, 100000000), Int('probe', 'Read at offset (KiB)', 4200, 0, 100000000)],
           example={'block_size': 4096, 'pointer': 4, 'direct': 12, 'file_size': 5000, 'probe': 4200},
           random=lambda rng: {'block_size': rng.choice([1024, 4096]), 'pointer': 4, 'direct': 12, 'file_size': rng.choice([20, 500, 5000, 900000]), 'probe': rng.randint(0, 5000)},
           notes=['Small files (the common case) need no indirection at all.', 'Each extra level adds one disk read for the pointer block.'], tags=['unix'])
def inode(p):
    bs, ptr, direct = p['block_size'], p['pointer'], p['direct']
    per = bs // ptr
    caps = [direct, per, per ** 2, per ** 3]
    names = ['Direct', 'Single indirect', 'Double indirect', 'Triple indirect']
    need = -(-p['file_size'] * 1024 // bs)
    left, levels = need, []
    for name, cap in zip(names, caps):
        used = min(left, cap)
        levels.append({'name': name, 'capacity': cap, 'used': used})
        left -= used
    max_bytes = sum(caps) * bs
    if left > 0:
        raise ValidationError('File does not fit: the maximum file size for this layout is %.0f KiB' % (max_bytes / 1024))
    probe_block = p['probe'] * 1024 // bs
    idx, level_hit = probe_block, 0
    for i, cap in enumerate(caps):
        if idx < cap:
            level_hit = i
            break
        idx -= cap
    else:
        level_hit = 3
    reads = 1 + level_hit
    trace = Trace()
    trace.add(f'File of {p["file_size"]} KiB needs {need} blocks of {bs} bytes. Each pointer block holds {per} pointers.', [0, 5], 0)
    for i, lv in enumerate(levels):
        if lv['used']:
            trace.add(f'{lv["name"]}: {lv["used"]} of {lv["capacity"]} blocks used.', [1 + i if i else 1], i + 1)
    trace.add(f'Byte at offset {p["probe"]} KiB is block {probe_block}, reached through the {names[level_hit].lower()} level: {reads} disk read(s).', [level_hit + 1], len(levels) + 1)
    summary = [tile('Blocks needed', need), tile('Deepest level', names[max((i for i, l in enumerate(levels) if l['used']), default=0)]),
               tile('Max file size', _human(max_bytes)), tile('Probe reads', reads)]
    return result('inode', 'inode', summary, trace, {'levels': levels, 'perBlock': per, 'blockSize': bs, 'probe': {'block': probe_block, 'level': level_hit, 'reads': reads}})


def _human(n):
    for unit, size in (('TiB', 1024 ** 4), ('GiB', 1024 ** 3), ('MiB', 1024 ** 2), ('KiB', 1024)):
        if n >= size:
            return f'{n / size:.1f} {unit}'
    return f'{n} B'
