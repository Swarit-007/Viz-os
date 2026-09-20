"""Processes and caches: fork() trees and set-associative cache simulation."""

from ..core import Choice, Int, IntList, Lines, Trace, ValidationError, algorithm, result, tile

PROGRAM = ['fork', 'fork', 'print']


@algorithm(id='fork-tree', name='fork() Process Tree', category='misc', viz='tree', family='fork',
           summary='Every fork() splits a process in two. Trace a small program and count the processes it creates.',
           complexity={'time': 'O(processes x lines)', 'space': 'O(processes)', 'note': 'n unconditional forks make 2^n processes.'},
           pseudocode=['each line runs once in every process that reaches it', 'fork: the parent continues; a new child starts at the next line',
                       'fork-if-parent / fork-if-child: fork only when the condition holds', 'print: every process that reaches it prints once',
                       'a child is the process for which fork() returned 0'],
           params=[Lines('program', 'Program', PROGRAM, 16, 'Lines: fork, fork-if-parent, fork-if-child, print', 'fork')],
           example={'program': PROGRAM}, random=lambda rng: {'program': [rng.choice(['fork', 'fork', 'fork-if-parent', 'fork-if-child', 'print']) for _ in range(rng.randint(3, 5))]},
           notes=['Two unconditional forks create 4 processes, not 3.', 'if (fork() == 0) style code is fork-if-child in this notation.'], tags=['process'])
def fork_tree(p):
    prog = p['program']
    for line in prog:
        if line not in ('fork', 'fork-if-parent', 'fork-if-child', 'print'):
            raise ValidationError(f'Unknown instruction "{line}"')
    nodes = [{'id': 'P0', 'parent': None, 'line': None, 'prints': 0}]
    counter = [1]
    prints = []
    trace = Trace()
    snaps = []

    def execute(pid, pc, is_child):
        for i in range(pc, len(prog)):
            ins = prog[i]
            if ins == 'print':
                node = next(n for n in nodes if n['id'] == pid)
                node['prints'] += 1
                prints.append(pid)
            else:
                cond = ins == 'fork' or (ins == 'fork-if-child' and is_child) or (ins == 'fork-if-parent' and not is_child)
                if cond:
                    cid = f'P{counter[0]}'
                    counter[0] += 1
                    nodes.append({'id': cid, 'parent': pid, 'line': i + 1, 'prints': 0})
                    snaps.append([dict(n) for n in nodes])
                    trace.add(f'{pid} executes line {i + 1} ({ins}) and creates {cid}.', [1 if ins == 'fork' else 2], len(snaps) - 1)
                    execute(cid, i + 1, True)
                    is_child = False
    execute('P0', 0, False)
    snaps.append([dict(n) for n in nodes])
    trace.add(f'Done: {len(nodes)} processes, {len(prints)} lines printed.', [3], len(snaps) - 1)
    summary = [tile('Processes', len(nodes)), tile('Prints', len(prints)), tile('fork() calls', len(nodes) - 1)]
    return result('fork-tree', 'tree', summary, trace, {'snapshots': snaps, 'program': prog})


@algorithm(id='cache', name='CPU Cache', category='misc', viz='grid', family='cache',
           summary='Map memory addresses onto cache sets. Compare direct-mapped and set-associative caches on the same access pattern.',
           complexity={'time': 'O(accesses x ways)', 'space': 'O(lines)', 'note': ''},
           pseudocode=['block = address / block size', 'set = block mod number of sets; tag = block / number of sets',
                       'if a way in the set holds the tag: HIT', 'else: MISS', '    if a way is empty: fill it', '    else: evict the least recently used way'],
           params=[Int('lines', 'Cache lines', 8, 2, 32), Choice('ways', 'Associativity', [('1', 'Direct-mapped'), ('2', '2-way'), ('4', '4-way'), ('8', '8-way')], '2'),
                   Int('block_size', 'Block size (bytes)', 16, 4, 256), IntList('addresses', 'Addresses', [0, 16, 32, 48, 0, 16, 32, 48, 128, 256, 0, 128, 256], 0, 65535, 1, 40)],
           example={'lines': 8, 'ways': '2', 'block_size': 16, 'addresses': [0, 16, 32, 48, 0, 16, 32, 48, 128, 256, 0, 128, 256]},
           random=lambda rng: {'lines': 8, 'ways': rng.choice(['1', '2', '4']), 'block_size': 16, 'addresses': [rng.choice([0, 128, 256, 384]) + rng.choice([0, 16, 32]) for _ in range(12)]},
           notes=['Addresses whose blocks share a set collide: conflict misses. More ways relieve them.', 'The first touch of any block is a compulsory miss no cache can avoid.'],
           tags=['cache'])
def cache(p):
    ways = int(p['ways'])
    if p['lines'] % ways:
        raise ValidationError('Cache lines must be a multiple of the associativity')
    sets = p['lines'] // ways
    grid = [[None] * ways for _ in range(sets)]
    stamp = [[0] * ways for _ in range(sets)]
    seen, hits, comp, trace, snaps = set(), 0, 0, Trace(), []
    for k, addr in enumerate(p['addresses']):
        block = addr // p['block_size']
        s, tag = block % sets, block // sets
        row = grid[s]
        if tag in row:
            hits += 1
            w = row.index(tag)
            kind = 'hit'
            lines = [0, 1, 2]
            note = f'Address {addr}: block {block} maps to set {s}, tag {tag}. HIT in way {w}.'
        else:
            if None in row:
                w = row.index(None)
                lines = [0, 1, 3, 4]
            else:
                w = min(range(ways), key=lambda i: stamp[s][i])
                lines = [0, 1, 3, 5]
            first = block not in seen
            comp += first
            note = (f'Address {addr}: block {block} maps to set {s}, tag {tag}. MISS ' + ('(first touch, compulsory)' if first else '(the block was evicted earlier)')
                    + f'. Placed in way {w}' + (f', replacing tag {row[w]}.' if row[w] is not None else '.'))
            row[w] = tag
            kind = 'miss'
        seen.add(block)
        stamp[s][w] = k
        snaps.append([{'label': '' if t is None else f't{t}', 'kind': 'free' if t is None else ('data' if not (ss == s and ww == w) else ('data' if kind == 'hit' else 'index')),
                       'owner': None if t is None else f'B{t * sets + ss}', 'sub': ''} for ss, r in enumerate(grid) for ww, t in enumerate(r)])
        trace.add(note, lines, k)
    n = len(p['addresses'])
    summary = [tile('Hit ratio', f'{hits / n * 100:.1f}%', tone='good'), tile('Hits', hits), tile('Misses', n - hits, tone='bad'), tile('Compulsory misses', comp)]
    return result('cache', 'grid', summary, trace, {'columns': ways, 'colLabels': [f'Way {i}' for i in range(ways)], 'rowLabels': [f'Set {s}' for s in range(sets)],
                                                    'snapshots': snaps, 'start': [{'label': '', 'kind': 'free', 'sub': ''} for _ in range(sets * ways)]})
