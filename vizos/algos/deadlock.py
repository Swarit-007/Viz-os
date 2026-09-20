"""Deadlocks: Banker's algorithm, resource-request check, detection and RAG cycle finding."""

import random
from typing import Any, Dict, List

from ..core import Int, Lines, Matrix, Trace, ValidationError, Vector, algorithm, result, tile

ALLOC = [[0, 1, 0], [2, 0, 0], [3, 0, 2], [2, 1, 1], [0, 0, 2]]
MAX = [[7, 5, 3], [3, 2, 2], [9, 0, 2], [2, 2, 2], [4, 3, 3]]
AVAIL = [3, 3, 2]


def _fmt(v):
    return '[' + ', '.join(map(str, v)) + ']'


def _safety(alloc, need, available, trace, lines, snaps, label='need'):
    """Run the safety / detection loop, recording one step per check. Returns the safe sequence."""
    n, m = len(alloc), len(available)
    work, finish, order = list(available), [False] * n, []
    snaps.append({'work': list(work), 'finish': list(finish), 'focus': None, 'verdict': None, 'order': []})
    trace.add(f'Start with work = available = {_fmt(work)}. No process is finished.', [lines['start']], len(snaps) - 1)
    progress = True
    while progress:
        progress = False
        for i in range(n):
            if finish[i]:
                continue
            ok = all(need[i][j] <= work[j] for j in range(m))
            if ok:
                work = [work[j] + alloc[i][j] for j in range(m)]
                finish[i] = True
                order.append(f'P{i + 1}')
                progress = True
                snaps.append({'work': list(work), 'finish': list(finish), 'focus': i, 'verdict': 'ok', 'order': list(order)})
                trace.add(f'P{i + 1}: {label} {_fmt(need[i])} fits within work. It can run to completion and returns {_fmt(alloc[i])}. '
                          f'Work becomes {_fmt(work)}.', [lines['check'], lines['grant']], len(snaps) - 1)
            else:
                snaps.append({'work': list(work), 'finish': list(finish), 'focus': i, 'verdict': 'skip', 'order': list(order)})
                trace.add(f'P{i + 1}: {label} {_fmt(need[i])} does not fit within work {_fmt(work)}. Skip for now.',
                          [lines['check']], len(snaps) - 1)
    return order, finish


def _banker_data(n, m, alloc, mx, need, avail, snaps, extra=None):
    d = {'n': n, 'm': m, 'allocation': alloc, 'max': mx, 'need': need, 'available': avail, 'snapshots': snaps}
    d.update(extra or {})
    return d


def _random_state(rng, n=None, m=None):
    n, m = n or rng.randint(3, 5), m or rng.randint(2, 4)
    alloc = [[rng.randint(0, 3) for _ in range(m)] for _ in range(n)]
    mx = [[a + rng.randint(0, 5) for a in row] for row in alloc]
    return {'n': n, 'm': m, 'allocation': alloc, 'max': mx, 'available': [rng.randint(0, 4) for _ in range(m)]}


def _check_state(p):
    for i in range(p['n']):
        for j in range(p['m']):
            if p['allocation'][i][j] > p['max'][i][j]:
                raise ValidationError(f'Allocation exceeds Max for P{i + 1}, R{j + 1}')


def _banker_params():
    return [Int('n', 'Processes', 5, 1, 8), Int('m', 'Resource types', 3, 1, 5),
            Matrix('allocation', 'Allocation', 'n', 'm', ALLOC, 0, 30), Matrix('max', 'Max', 'n', 'm', MAX, 0, 30),
            Vector('available', 'Available', 'm', AVAIL, 0, 50)]


SAFETY_PSEUDO = ['work = available; finish = all false', 'repeat while progress is made:', '    for each unfinished process i:',
                 '        if need[i] <= work:', '            work = work + allocation[i]; finish[i] = true; append i to the safe sequence',
                 'safe if every process finished']


@algorithm(id='bankers', name='Banker\'s Algorithm', category='deadlock', viz='banker', family='deadlock',
           summary='Decide whether the system is in a safe state: can every process still finish in some order?',
           complexity={'time': 'O(n^2 x m)', 'space': 'O(n x m)', 'note': 'n processes, m resource types.'},
           pseudocode=SAFETY_PSEUDO, params=_banker_params(),
           example={'n': 5, 'm': 3, 'allocation': ALLOC, 'max': MAX, 'available': AVAIL}, random=lambda rng: _random_state(rng),
           notes=['need = max - allocation.', 'A safe state has at least one order in which every process can finish; unsafe does not mean deadlocked, only possible.'],
           tags=['avoidance'])
def bankers(p):
    _check_state(p)
    n, m = p['n'], p['m']
    need = [[p['max'][i][j] - p['allocation'][i][j] for j in range(m)] for i in range(n)]
    trace, snaps = Trace(), []
    order, finish = _safety(p['allocation'], need, p['available'], trace, {'start': 0, 'check': 3, 'grant': 4}, snaps)
    safe = len(order) == n
    trace.add('Every process finished: the state is SAFE.' if safe else
              f'No remaining process fits: {n - len(order)} cannot finish, so the state is UNSAFE.', [5], len(snaps) - 1)
    summary = [tile('State', 'Safe' if safe else 'Unsafe', tone='good' if safe else 'bad'), tile('Processes finished', f'{len(order)}/{n}')]
    verdict = {'ok': safe, 'label': 'Safe state' if safe else 'Unsafe state',
               'text': 'Safe sequence: ' + ' -> '.join(order) if safe else 'Finished in order: ' + (' -> '.join(order) or 'none') + '.'}
    return result('bankers', 'banker', summary, trace, _banker_data(n, m, p['allocation'], p['max'], need, p['available'], snaps, {'mode': 'need'}),
                  None, verdict)


@algorithm(id='bankers-request', name='Banker\'s: resource request', category='deadlock', viz='banker', family='deadlock',
           summary='A process asks for more resources. Grant it only if the resulting state is still safe.',
           complexity={'time': 'O(n^2 x m)', 'space': 'O(n x m)', 'note': ''},
           pseudocode=['if request > need: error, the process exceeded its claim', 'if request > available: the process must wait',
                       'pretend to allocate: available -= request; allocation += request; need -= request', 'run the safety algorithm on the new state',
                       'safe: grant the request', 'unsafe: roll back and make the process wait'],
           params=_banker_params() + [Int('process', 'Requesting process', 2, 1, 8), Vector('request', 'Request', 'm', [1, 0, 2], 0, 30)],
           example={'n': 5, 'm': 3, 'allocation': ALLOC, 'max': MAX, 'available': AVAIL, 'process': 2, 'request': [1, 0, 2]},
           random=lambda rng: {**_random_state(rng, 4, 3), 'process': rng.randint(1, 4), 'request': [rng.randint(0, 2) for _ in range(3)]},
           notes=['Being available is not enough: the grant must leave the system safe.'], tags=['avoidance'])
def bankers_request(p):
    _check_state(p)
    n, m = p['n'], p['m']
    if p['process'] > n:
        raise ValidationError(f'Requesting process must be between 1 and {n}')
    i = p['process'] - 1
    need = [[p['max'][r][c] - p['allocation'][r][c] for c in range(m)] for r in range(n)]
    trace, snaps = Trace(), []
    req = p['request']

    def outcome(ok, reason, at_snaps):
        summary = [tile('Decision', 'Granted' if ok else 'Denied', tone='good' if ok else 'bad')]
        return result('bankers-request', 'banker', summary, trace,
                      _banker_data(n, m, p['allocation'], p['max'], need, p['available'], at_snaps, {'mode': 'need', 'request': {'process': i, 'vector': req}}),
                      None, {'ok': ok, 'label': 'Granted' if ok else 'Denied', 'text': reason})
    base = {'work': list(p['available']), 'finish': [False] * n, 'focus': i, 'verdict': None, 'order': []}
    if any(req[j] > need[i][j] for j in range(m)):
        snaps.append(base)
        trace.add(f'Request {_fmt(req)} exceeds P{i + 1}\'s need {_fmt(need[i])}: error.', [0], 0)
        return outcome(False, 'The request exceeds the maximum claim.', snaps)
    if any(req[j] > p['available'][j] for j in range(m)):
        snaps.append(base)
        trace.add(f'Request {_fmt(req)} is more than available {_fmt(p["available"])}: P{i + 1} must wait.', [1], 0)
        return outcome(False, 'Not enough resources available right now.', snaps)
    new_avail = [p['available'][j] - req[j] for j in range(m)]
    new_alloc = [row[:] for row in p['allocation']]
    new_need = [row[:] for row in need]
    for j in range(m):
        new_alloc[i][j] += req[j]
        new_need[i][j] -= req[j]
    snaps.append(base)
    trace.add(f'Both checks pass. Pretend to grant: available becomes {_fmt(new_avail)}, P{i + 1} now holds {_fmt(new_alloc[i])}.', [2], 0)
    order, _ = _safety(new_alloc, new_need, new_avail, trace, {'start': 3, 'check': 3, 'grant': 3}, snaps)
    safe = len(order) == n
    trace.add('The new state is safe: grant the request.' if safe else 'The new state is unsafe: roll back, P%d waits.' % (i + 1), [4 if safe else 5], len(snaps) - 1)
    return outcome(safe, 'Resulting safe sequence: ' + ' -> '.join(order) if safe else 'Granting would leave the system unsafe.', snaps)


@algorithm(id='deadlock-detect', name='Deadlock Detection', category='deadlock', viz='banker', family='deadlock',
           summary='Given what processes hold and are asking for right now, which ones can never finish?',
           complexity={'time': 'O(n^2 x m)', 'space': 'O(n x m)', 'note': ''},
           pseudocode=['work = available; finish[i] = true if process i holds nothing', 'repeat while progress is made:',
                       '    for each unfinished process i:', '        if request[i] <= work:',
                       '            work = work + allocation[i]; finish[i] = true', 'unfinished processes are deadlocked'],
           params=[Int('n', 'Processes', 4, 1, 8), Int('m', 'Resource types', 3, 1, 5),
                   Matrix('allocation', 'Allocation', 'n', 'm', [[0, 1, 0], [2, 0, 0], [3, 0, 3], [2, 1, 1]], 0, 30),
                   Matrix('request', 'Request', 'n', 'm', [[0, 0, 0], [2, 0, 2], [0, 0, 1], [1, 0, 0]], 0, 30),
                   Vector('available', 'Available', 'm', [0, 0, 0], 0, 50)],
           example={'n': 4, 'm': 3, 'allocation': [[0, 1, 0], [2, 0, 0], [3, 0, 3], [2, 1, 1]],
                    'request': [[0, 0, 0], [2, 0, 2], [0, 0, 1], [1, 0, 0]], 'available': [0, 0, 0]},
           random=lambda rng: {'n': 4, 'm': 2, 'allocation': [[rng.randint(0, 2) for _ in range(2)] for _ in range(4)],
                               'request': [[rng.choice([0, 0, 1, 2]) for _ in range(2)] for _ in range(4)],
                               'available': [rng.randint(0, 1) for _ in range(2)]},
           notes=['Unlike Banker\'s, detection uses current requests, not maximum claims.', 'Run periodically; recovery means killing or rolling back a process.'],
           tags=['detection'])
def deadlock_detect(p):
    n, m = p['n'], p['m']
    alloc, req = p['allocation'], p['request']
    trace, snaps = Trace(), []
    holds_nothing = [not any(row) for row in alloc]
    work = list(p['available'])
    finish = list(holds_nothing)
    snaps.append({'work': list(work), 'finish': list(finish), 'focus': None, 'verdict': None, 'order': []})
    trace.add(f'Start with work = available = {_fmt(work)}. Processes holding nothing ({", ".join(f"P{i + 1}" for i in range(n) if holds_nothing[i]) or "none"}) cannot be part of a deadlock.', [0], 0)
    order, progress = [], True
    while progress:
        progress = False
        for i in range(n):
            if finish[i]:
                continue
            if all(req[i][j] <= work[j] for j in range(m)):
                work = [work[j] + alloc[i][j] for j in range(m)]
                finish[i] = True
                order.append(f'P{i + 1}')
                progress = True
                snaps.append({'work': list(work), 'finish': list(finish), 'focus': i, 'verdict': 'ok', 'order': list(order)})
                trace.add(f'P{i + 1}: request {_fmt(req[i])} can be met. It finishes and releases {_fmt(alloc[i])}. Work = {_fmt(work)}.', [3, 4], len(snaps) - 1)
            else:
                snaps.append({'work': list(work), 'finish': list(finish), 'focus': i, 'verdict': 'skip', 'order': list(order)})
                trace.add(f'P{i + 1}: request {_fmt(req[i])} cannot be met with work {_fmt(work)}.', [3], len(snaps) - 1)
    dead = [f'P{i + 1}' for i in range(n) if not finish[i]]
    trace.add('Deadlocked: ' + ', '.join(dead) if dead else 'Everyone can finish: no deadlock.', [5], len(snaps) - 1)
    edges = [{'from': f'P{i + 1}', 'to': f'P{k + 1}'} for i in range(n) for k in range(n)
             if i != k and any(req[i][j] > 0 and alloc[k][j] > 0 for j in range(m))]
    graph = {'nodes': [{'id': f'P{i + 1}', 'label': f'P{i + 1}', 'kind': 'dead' if f'P{i + 1}' in dead else 'proc'} for i in range(n)], 'edges': edges}
    summary = [tile('Deadlock', 'yes' if dead else 'no', tone='bad' if dead else 'good'), tile('Deadlocked processes', len(dead))]
    verdict = {'ok': not dead, 'label': 'Deadlock' if dead else 'No deadlock',
               'text': 'Deadlocked: ' + ', '.join(dead) if dead else 'Every process can obtain what it needs.'}
    return result('deadlock-detect', 'banker', summary, trace,
                  _banker_data(n, m, alloc, alloc, req, p['available'], snaps, {'mode': 'request', 'graph': graph}), None, verdict)


@algorithm(id='rag-cycle', name='Resource Allocation Graph', category='deadlock', viz='graph', family='deadlock',
           summary='With one instance of each resource, a deadlock is exactly a cycle in the allocation graph.',
           complexity={'time': 'O(V + E)', 'space': 'O(V)', 'note': 'Depth-first search.'},
           pseudocode=['edges: P -> R is a request, R -> P is an assignment', 'for each unvisited node: depth-first search',
                       '    mark the node as on the current path', '    follow each outgoing edge',
                       '    reaching a node already on the path means a cycle', 'no cycle: no deadlock'],
           params=[Lines('edges', 'Edges', ['R1 -> P1', 'P1 -> R2', 'R2 -> P2', 'P2 -> R1', 'R3 -> P3'], hint='One per line. P1 -> R1 requests, R1 -> P1 assigns.', placeholder='P1 -> R1')],
           example={'edges': ['R1 -> P1', 'P1 -> R2', 'R2 -> P2', 'P2 -> R1', 'R3 -> P3']},
           random=lambda rng: {'edges': _rag_random(rng)},
           notes=['With multiple instances per resource, a cycle only signals possible deadlock.'], tags=['detection', 'graph'])
def rag_cycle(p):
    edges = []
    for line in p['edges']:
        parts = line.replace('->', ' ').split()
        if len(parts) != 2:
            raise ValidationError(f'Write edges as "P1 -> R1": {line}')
        a, b = parts
        if not ((a[0] in 'Pp' and b[0] in 'Rr') or (a[0] in 'Rr' and b[0] in 'Pp')):
            raise ValidationError(f'Edges must join a process (P) and a resource (R): {line}')
        edges.append((a.upper(), b.upper()))
    nodes = sorted({x for e in edges for x in e}, key=lambda s: (s[0] != 'P', int(s[1:]) if s[1:].isdigit() else 0, s))
    adj: Dict[str, List[str]] = {x: [] for x in nodes}
    for a, b in edges:
        adj[a].append(b)
    trace, snaps = Trace(), []
    color, stack, cycle = {x: 0 for x in nodes}, [], None

    def dfs(u):
        nonlocal cycle
        color[u] = 1
        stack.append(u)
        snaps.append({'path': list(stack), 'cycle': None})
        trace.add(f'Visit {u}. Current path: {" -> ".join(stack)}.', [1, 2], len(snaps) - 1)
        for v in adj[u]:
            if cycle:
                return
            if color[v] == 1:
                cycle = stack[stack.index(v):] + [v]
                snaps.append({'path': list(stack), 'cycle': cycle})
                trace.add(f'{v} is already on the path: cycle {" -> ".join(cycle)}.', [4], len(snaps) - 1)
                return
            if color[v] == 0:
                dfs(v)
        stack.pop()
        color[u] = 2
    for x in nodes:
        if color[x] == 0 and not cycle:
            dfs(x)
    if not cycle:
        snaps.append({'path': [], 'cycle': None})
        trace.add('The search finished without finding a cycle: no deadlock.', [5], len(snaps) - 1)
    cyc_set = set(cycle or [])
    graph = {'nodes': [{'id': x, 'label': x, 'kind': ('res' if x[0] == 'R' else 'proc') + ('-dead' if x in cyc_set else '')} for x in nodes],
             'edges': [{'from': a, 'to': b, 'dashed': a[0] == 'P'} for a, b in edges]}
    summary = [tile('Cycle', 'yes' if cycle else 'no', tone='bad' if cycle else 'good'), tile('Nodes', len(nodes)), tile('Edges', len(edges))]
    verdict = {'ok': not cycle, 'label': 'Deadlock' if cycle else 'No deadlock',
               'text': 'Cycle: ' + ' -> '.join(cycle) if cycle else 'The graph has no cycle.'}
    return result('rag-cycle', 'graph', summary, trace, {'graph': graph, 'snapshots': snaps}, None, verdict)


def _rag_random(rng):
    edges = []
    for i in range(rng.randint(3, 4)):
        edges.append(f'R{i + 1} -> P{i + 1}')
        edges.append(f'P{i + 1} -> R{(i + 1) % 3 + 1 if rng.random() < 0.7 else rng.randint(1, 4)}')
    return sorted(set(edges))
