"""Disk head scheduling (FCFS, SSTF, SCAN, C-SCAN, LOOK, C-LOOK) and RAID layouts."""

from typing import Any, Dict, List

from ..core import Choice, Int, IntList, Trace, ValidationError, algorithm, result, tile

# The textbook disk-scheduling example: head at cylinder 53 on a 200-cylinder disk.
REQS = [98, 183, 37, 122, 14, 124, 65, 67]
NAMES = {'fcfs': 'FCFS', 'sstf': 'SSTF', 'scan': 'SCAN', 'cscan': 'C-SCAN', 'look': 'LOOK', 'clook': 'C-LOOK'}
SUMMARY = {
    'fcfs': 'Service requests in arrival order. Fair, but the head swings wildly.',
    'sstf': 'Always go to the closest pending request. Low movement, but far requests can starve.',
    'scan': 'The elevator: sweep to the disk edge servicing requests, then reverse.',
    'cscan': 'Sweep one way only; at the edge jump back to the start. More uniform waits.',
    'look': 'Like SCAN but turns around at the last request instead of the edge.',
    'clook': 'Like C-SCAN but only travels to the last request before jumping back.',
}
NOTES = {
    'fcfs': ['No starvation, but no optimisation either.'],
    'sstf': ['Greedy shortest seek. Can starve requests at the far end.'],
    'scan': ['Requests just behind the head wait a whole sweep.', 'Cylinders in the middle are visited more often than the edges.'],
    'cscan': ['Treats the disk as a circle; the return jump is counted as movement here.'],
    'look': ['The practical version of SCAN.'],
    'clook': ['The practical version of C-SCAN; the return jump is counted as movement here.'],
}
PSEUDO = {
    'fcfs': ['for each request in arrival order:', '    move the head to the request', '    service it'],
    'sstf': ['while requests are pending:', '    next = the pending request closest to the head', '    move the head to next', '    service it and remove it'],
    'scan': ['sweep the head in the chosen direction', '    service every request it passes', 'at the disk edge: reverse direction', 'repeat until no requests remain'],
    'cscan': ['sweep the head in the chosen direction', '    service every request it passes', 'at the disk edge: jump back to the opposite edge',
              'repeat the sweep until no requests remain'],
    'look': ['sweep the head in the chosen direction', '    service every request it passes', 'after the last request in this direction: reverse',
             'repeat until no requests remain'],
    'clook': ['sweep the head in the chosen direction', '    service every request it passes', 'after the last request: jump to the farthest waiting request',
              'repeat until no requests remain'],
}


# Decide the order in which the head visits cylinders. Returns [(cylinder, kind)] where kind is:
#   req      - the head arrives at a request and services it
#   edge     - the head travels to the physical end of the disk (SCAN / C-SCAN) without a request there
#   jump     - a non-servicing return seek to the opposite end (C-SCAN)
#   jumpreq  - a return seek that lands on the farthest waiting request (C-LOOK)
# `above` are requests at/above the head (ascending), `below_desc` those below it (descending), etc.
def head_order(alg: str, reqs: List[int], head: int, size: int, up: bool):
    """[(cylinder, kind)] with kind in req, edge, jump, jumpreq."""
    R = lambda cs: [(c, 'req') for c in cs]  # noqa: E731
    above = sorted(r for r in reqs if r >= head)
    below_desc = sorted((r for r in reqs if r < head), reverse=True)
    at_below = sorted((r for r in reqs if r <= head), reverse=True)
    strictly_above = sorted(r for r in reqs if r > head)
    if alg == 'fcfs':
        return R(reqs)
    if alg == 'sstf':
        pending, pos, out = list(reqs), head, []
        while pending:
            nearest = min(pending, key=lambda r: (abs(r - pos), r))
            pending.remove(nearest)
            out.append(nearest)
            pos = nearest
        return R(out)
    if alg == 'scan':
        first, end, rest = (above, size - 1, below_desc) if up else (at_below, 0, strictly_above)
        order = R(first)
        if not order or order[-1][0] != end:
            order.append((end, 'edge'))
        return order + R(rest)
    if alg == 'cscan':
        first, end, rest, restart = (above, size - 1, sorted(below_desc), 0) if up else (at_below, 0, strictly_above[::-1], size - 1)
        order = R(first)
        if not order or order[-1][0] != end:
            order.append((end, 'edge'))
        if rest:
            order.append((restart, 'jump'))
            order += R(rest)
        return order
    if alg == 'look':
        return R(above + below_desc) if up else R(at_below + strictly_above)
    first, rest = (above, sorted(below_desc)) if up else (at_below, strictly_above[::-1])
    order = R(first)
    if rest:
        order.append((rest[0], 'jumpreq'))
        order += R(rest[1:])
    return order


# Walk the visiting order and add up the distance moved. Return jumps are counted as movement here.
def simulate_disk(alg: str, reqs: List[int], head: int, size: int, up: bool):
    order = head_order(alg, reqs, head, size, up)
    steps, pos, total, jump_total = [], head, 0, 0
    for c, kind in order:
        d = abs(c - pos)
        total += d
        jump = kind in ('jump', 'jumpreq')
        if jump:
            jump_total += d
        steps.append({'from': pos, 'to': c, 'dist': d, 'jump': jump, 'serviced': kind in ('req', 'jumpreq'), 'edge': kind == 'edge'})
        pos = c
    return steps, total, jump_total


# Factory: registers one algorithm per scheduling policy.
def _disk(alg):
    def run(p):
        if p['head'] >= p['size']:
            raise ValidationError('Head position must be below the number of cylinders')
        if max(p['requests']) >= p['size']:
            raise ValidationError('Every request must be below the number of cylinders')
        steps, total, jump = simulate_disk(alg, p['requests'], p['head'], p['size'], p['direction'] == 'up')
        trace = Trace()
        for i, s in enumerate(steps):
            if s['jump']:
                trace.add(f'Jump from {s["from"]} to {s["to"]} ({s["dist"]} cylinders).', [2], i)
            elif s['edge']:
                trace.add(f'Continue to the disk edge at {s["to"]} ({s["dist"]} cylinders) before turning.', [0, 2], i)
            else:
                trace.add(f'Move {s["from"]} to {s["to"]} ({s["dist"]} cylinders) and service the request.',
                          {'fcfs': [1, 2], 'sstf': [1, 2, 3]}.get(alg, [0, 1]), i)
        n = len(p['requests'])
        summary = [tile('Total head movement', total, 'cylinders'), tile('Average seek', f'{total / n:.2f}', 'per request')]
        if jump:
            summary.append(tile('Return jump', jump))
        table = {'title': 'Service order', 'headers': ['#', 'From', 'To', 'Distance', 'Kind'],
                 'rows': [[i + 1, s['from'], s['to'], s['dist'], 'return jump' if s['jump'] else 'disk edge' if s['edge'] else 'serviced'] for i, s in enumerate(steps)]}
        return result(f'disk-{alg}', 'disk', summary, trace, {'size': p['size'], 'head': p['head'], 'steps': steps, 'requests': p['requests']}, table)

    algorithm(id=f'disk-{alg}', name=f'{NAMES[alg]} Disk Scheduling', category='disk', family='disk', viz='disk', summary=SUMMARY[alg],
              complexity={'time': 'O(n log n)', 'space': 'O(n)', 'note': ''}, pseudocode=PSEUDO[alg],
              params=[IntList('requests', 'Request queue', REQS, 0, 9999, 1, 24), Int('head', 'Head position', 53, 0, 9999),
                      Int('size', 'Cylinders', 200, 10, 10000), Choice('direction', 'Initial direction', [('up', 'Toward higher cylinders'), ('down', 'Toward lower cylinders')])],
              example={'requests': REQS, 'head': 53, 'size': 200, 'direction': 'up'},
              random=lambda rng: _random_disk(rng), notes=NOTES[alg], tags=['seek'])(run)


def _random_disk(rng):
    size = rng.choice([100, 200, 256])
    return {'requests': [rng.randint(0, size - 1) for _ in range(rng.randint(6, 10))], 'head': rng.randint(0, size - 1), 'size': size,
            'direction': rng.choice(['up', 'down'])}


for _a in NAMES:
    _disk(_a)


# --------------------------------------------------------------------------- RAID
# Random but always valid RAID configuration (each level has its own rule about how many disks it needs).
def _random_raid(rng):
    level = rng.choice(['0', '1', '5', '10'])
    disks = {'0': rng.randint(2, 6), '1': 2, '5': rng.randint(3, 6), '10': rng.choice([4, 6])}[level]
    return {'level': level, 'disks': disks, 'blocks': rng.randint(6, 20), 'failed': rng.randint(0, disks)}


@algorithm(id='raid', name='RAID Levels', category='disk', viz='grid', family='raid',
           summary='Spread blocks over several disks for speed, redundancy, or both. Fail a disk and see what survives.',
           complexity={'time': 'O(blocks)', 'space': 'O(disks)', 'note': ''},
           pseudocode=['RAID 0: stripe blocks across all disks (no redundancy)', 'RAID 1: write every block to two disks (mirror)',
                       'RAID 5: stripe blocks and rotate one parity block per stripe (parity = XOR of the data)',
                       'RAID 10: mirror pairs, then stripe across the pairs', 'a failed disk is rebuilt from the mirror or from parity XOR'],
           params=[Choice('level', 'RAID level', [('0', 'RAID 0 (striping)'), ('1', 'RAID 1 (mirror)'), ('5', 'RAID 5 (striping + parity)'), ('10', 'RAID 10')], '5'),
                   Int('disks', 'Disks', 4, 2, 8), Int('blocks', 'Data blocks', 12, 1, 60), Int('failed', 'Failed disk (0 = none)', 2, 0, 8)],
           example={'level': '5', 'disks': 4, 'blocks': 12, 'failed': 2},
           random=lambda rng: _random_raid(rng),
           notes=['Capacity, throughput and fault tolerance trade against each other.', 'RAID 5 tolerates one failed disk; RAID 0 tolerates none.'], tags=['storage', 'redundancy'])
# Lay blocks out over the disks stripe by stripe:
#   RAID 0  data striped across all disks       RAID 1  every block mirrored on two disks
#   RAID 5  data striped + one rotating parity block per stripe (parity = XOR of the stripe's data)
#   RAID 10 mirrored pairs, striped across the pairs
# Then fail one disk and check whether every lost block can be rebuilt (from the mirror or from parity).
def raid(p):
    level, n, blocks, failed = p['level'], p['disks'], p['blocks'], p['failed']
    if failed > n:
        raise ValidationError('Failed disk must be one of the disks (or 0 for none)')
    if level == '1' and n != 2:
        n = 2
    if level == '5' and n < 3:
        raise ValidationError('RAID 5 needs at least 3 disks')
    if level == '10' and (n < 4 or n % 2):
        raise ValidationError('RAID 10 needs an even number of disks, at least 4')
    if level == '1' and failed > 2:
        raise ValidationError('RAID 1 here uses 2 disks')
    per_stripe = {'0': n, '1': 1, '5': n - 1, '10': n // 2}[level]
    stripes = -(-blocks // per_stripe)
    grid = [[{'label': '', 'kind': 'free'} for _ in range(n)] for _ in range(stripes)]
    trace, snaps, block = Trace(), [], 0
    for s in range(stripes):
        placed = []
        if level == '5':
            parity = (n - 1 - s) % n
            data_cols = [c for c in range(n) if c != parity]
            grid[s][parity] = {'label': 'P%d' % s, 'kind': 'parity'}
        else:
            data_cols = list(range(n))
        take = data_cols[:per_stripe] if level != '10' else data_cols
        if level == '1':
            if block < blocks:
                grid[s][0] = {'label': f'D{block}', 'kind': 'data', 'owner': f'D{block}'}
                grid[s][1] = {'label': f'D{block}', 'kind': 'mirror', 'owner': f'D{block}'}
                placed.append(f'D{block}')
                block += 1
        elif level == '10':
            for pair in range(n // 2):
                if block < blocks:
                    grid[s][2 * pair] = {'label': f'D{block}', 'kind': 'data', 'owner': f'D{block}'}
                    grid[s][2 * pair + 1] = {'label': f'D{block}', 'kind': 'mirror', 'owner': f'D{block}'}
                    placed.append(f'D{block}')
                    block += 1
        else:
            for c in take:
                if block < blocks:
                    grid[s][c] = {'label': f'D{block}', 'kind': 'data', 'owner': f'D{block}'}
                    placed.append(f'D{block}')
                    block += 1
        snaps.append([[dict(c) for c in row] for row in grid])
        trace.add(f'Stripe {s}: ' + (', '.join(placed) or 'nothing') + (f' with parity P{s} on disk {parity + 1}' if level == '5' else '') + '.', [{'0': 0, '1': 1, '5': 2, '10': 3}[level]], s)
    survives = True
    note = 'No disk has failed.'
    if failed:
        col = failed - 1
        lost_rows = 0
        for s in range(stripes):
            cell = grid[s][col]
            if cell['kind'] == 'free':
                continue
            if level == '0':
                lost_rows += 1
                grid[s][col] = {**cell, 'kind': 'lost'}
            elif level in ('1', '10'):
                pair = col ^ 1
                if grid[s][pair]['kind'] == 'free':
                    lost_rows += 1
                grid[s][col] = {**cell, 'kind': 'lost-recoverable'}
            else:
                grid[s][col] = {**cell, 'kind': 'lost-recoverable'}
        survives = lost_rows == 0
        note = (f'Disk {failed} fails. ' + ('Every lost block can be rebuilt' + (' from its mirror.' if level in ('1', '10') else ' by XOR of the other disks.')
                                           if survives else f'{lost_rows} blocks are gone for good: RAID 0 has no redundancy.'))
        snaps.append([[dict(c) for c in row] for row in grid])
        trace.add(note, [4], stripes)
    usable = {'0': n, '1': 1, '5': n - 1, '10': n // 2}[level]
    summary = [tile('Usable capacity', f'{usable}/{n} disks', f'{usable / n * 100:.0f}%'), tile('Stripes', stripes),
               tile('Survives 1 failure', 'no' if level == '0' else 'yes', tone='bad' if level == '0' else 'good'),
               tile('After failure', 'data intact' if survives else 'data lost', tone='good' if survives else 'bad')]
    verdict = {'ok': survives, 'label': 'Data intact' if survives else 'Data lost', 'text': note}
    return result('raid', 'grid', summary, trace, {'columns': n, 'colLabels': [f'Disk {i + 1}' for i in range(n)], 'rowLabels': [f'Stripe {s}' for s in range(stripes)],
                                                   'snapshots': [[c for row in snap for c in row] for snap in snaps], 'initial': None}, None, verdict)
