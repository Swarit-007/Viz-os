"""CPU scheduling: FCFS, SJF, SRTF, Priority, Round Robin, HRRN, Lottery, CFS, MLFQ, multi-core."""

import math
import random
from typing import Any, Callable, Dict, List

from ..core import Choice, Col, Int, Seed, Table, Trace, ValidationError, algorithm, result, tile

# The classic four-process example used across operating-systems textbooks. Every scheduler's default input.
# Fields: arrival = when it becomes ready, burst = CPU time needed, priority = lower number runs first.
TEXTBOOK = [
    {'id': 'P1', 'arrival': 0, 'burst': 8, 'priority': 3},
    {'id': 'P2', 'arrival': 1, 'burst': 4, 'priority': 1},
    {'id': 'P3', 'arrival': 2, 'burst': 9, 'priority': 4},
    {'id': 'P4', 'arrival': 3, 'burst': 5, 'priority': 2},
]


# Build the 'Processes' table schema. Different schedulers need different extra columns:
# priority (Priority), tickets (Lottery), nice (CFS).
def procs_param(with_priority=False, with_tickets=False, with_nice=False):
    cols = [Col('arrival', 'Arrival', 0, 200), Col('burst', 'Burst', 1, 200)]
    if with_priority:
        cols.append(Col('priority', 'Priority', 0, 99))
    if with_tickets:
        cols.append(Col('tickets', 'Tickets', 1, 100))
    if with_nice:
        cols.append(Col('nice', 'Nice', -10, 10))
    return Table('processes', 'Processes', cols, TEXTBOOK if not (with_tickets or with_nice) else [
        {**p, 'tickets': t, 'nice': n} for p, t, n in zip(TEXTBOOK, (30, 10, 50, 10), (0, -2, 3, 0))], max_rows=12)


# A small random workload with the same columns; used by every scheduler's Randomise button.
def random_procs(rng: random.Random, with_priority=False, with_tickets=False, with_nice=False):
    rows = []
    for i in range(rng.randint(4, 7)):
        row = {'id': f'P{i + 1}', 'arrival': rng.randint(0, 8), 'burst': rng.randint(1, 10)}
        if with_priority:
            row['priority'] = rng.randint(1, 5)
        if with_tickets:
            row['tickets'] = rng.choice([5, 10, 20, 40])
        if with_nice:
            row['nice'] = rng.randint(-3, 4)
        rows.append(row)
    return rows


# Turn (first-run time, finish time) per process into the per-process results table.
#   turnaround = finish - arrival   waiting = turnaround - burst   response = first run - arrival
def _row(name, procs, first, fin):
    by = {p['id']: p for p in procs}
    out = []
    for pid in sorted(fin, key=lambda i: (by[i]['arrival'], i)):
        p = by[pid]
        turnaround = fin[pid] - p['arrival']
        out.append({'id': pid, 'arrival': p['arrival'], 'burst': p['burst'], 'start': first[pid],
                    'finish': fin[pid], 'turnaround': turnaround, 'waiting': turnaround - p['burst'],
                    'response': first[pid] - p['arrival']})
    return out


# Shared tail of every scheduler: compute the averages, build the tiles and table, and package the result.
# `lanes` is a list of {label, slices}: one lane for a single CPU, one per core for multi-core, one per queue for MLFQ.
# A slice is {name, start, dur}. Utilisation is measured against total core-time available.
def _finish(alg_id, name, procs, lanes, first, fin, trace, total, marks=None, extra=None, notes=None):
    rows = _row(name, procs, first, fin)
    n = len(rows)
    avg = lambda key: round(sum(r[key] for r in rows) / n, 2)  # noqa: E731
    busy = sum(p['burst'] for p in procs)
    cores = len(lanes)
    slices = [s for lane in lanes for s in lane['slices']]
    switches = max(len(lanes[0]['slices']) - 1, 0) if cores == 1 else None
    summary = [tile('Avg waiting', avg('waiting')), tile('Avg turnaround', avg('turnaround')),
               tile('Avg response', avg('response')),
               tile('CPU utilisation', f'{busy / (total * cores) * 100:.1f}%' if total else '0%')]
    if switches is not None:
        summary.append(tile('Context switches', switches))
    summary.extend(extra or [])
    table = {'title': 'Per-process results',
             'headers': ['Process', 'Arrival', 'Burst', 'Start', 'Finish', 'Turnaround', 'Waiting', 'Response'],
             'rows': [[{'proc': r['id']}, r['arrival'], r['burst'], r['start'], r['finish'], r['turnaround'],
                       r['waiting'], r['response']] for r in rows]}
    data = {'lanes': lanes, 'total': total, 'marks': marks or [
        {'t': p['arrival'], 'name': p['id'], 'kind': 'arrive'} for p in procs], 'rows': rows,
        'slices': len(slices)}
    return result(alg_id, 'timeline', summary, trace, data, table)


# --------------------------------------------------------------------------- non-preemptive
# Engine for schedulers that never interrupt a running process (FCFS, SJF, Priority, HRRN).
# The only difference between them is `choose`, which picks the next process from the ready list.
# `lines` maps events (pick, run, idle) to pseudocode line numbers so each step can highlight the right line.
def _nonpreemptive(alg_id, name, procs, choose: Callable, reason: str, lines: Dict[str, int]):
    pending = sorted(procs, key=lambda p: (p['arrival'], p['id']))
    ready, t = [], 0
    slices, first, fin, trace = [], {}, {}, Trace()
    while pending or ready:
        while pending and pending[0]['arrival'] <= t:
            ready.append(pending.pop(0))
        if not ready:
            trace.add(f'Nothing is ready. The CPU idles until t={pending[0]["arrival"]}.', [lines['idle']], pending[0]['arrival'])
            t = pending[0]['arrival']
            continue
        # Ask the policy which ready process goes next, then run it to completion.
        p = choose(ready, t)
        ready.remove(p)
        first[p['id']] = t
        slices.append({'name': p['id'], 'start': t, 'dur': p['burst']})
        t += p['burst']
        fin[p['id']] = t
        waiting = ', '.join(r['id'] for r in ready) or 'none'
        trace.add(f'{p["id"]} runs from {t - p["burst"]} to {t} ({reason}). Still waiting: {waiting}.',
                  [lines['pick'], lines['run']], t)
    return _finish(alg_id, name, procs, [{'label': 'CPU', 'slices': slices}], first, fin, trace, t)


# Metadata shared by the non-preemptive schedulers, to avoid repeating the same dictionary four times.
def _np_meta(alg_id, name, summary, pseudocode, note_lines, complexity, notes, with_priority=False):
    return dict(id=alg_id, name=name, category='cpu', summary=summary, viz='timeline', family='cpu',
                complexity=complexity, pseudocode=pseudocode, params=[procs_param(with_priority)],
                example={'processes': TEXTBOOK}, random=lambda rng: {'processes': random_procs(rng, with_priority)},
                notes=notes, tags=['scheduling', 'non-preemptive'])


@algorithm(**_np_meta(
    'fcfs', 'First Come First Served', 'Run processes in the order they arrive, each to completion.',
    ['queue = processes ordered by arrival time', 'while the queue is not empty:', '    p = the first process in the queue',
     '    if p has not arrived: the CPU idles until it does', '    run p to completion',
     '    record p\'s start, finish and waiting time'], None,
    {'time': 'O(n log n)', 'space': 'O(n)', 'note': 'Sorting dominates.'},
    ['Simple and starvation-free.', 'The convoy effect: one long job makes every short job behind it wait.']))
def fcfs(p):
    return _nonpreemptive('fcfs', 'FCFS', p['processes'], lambda ready, t: min(ready, key=lambda x: (x['arrival'], x['id'])),
                          'arrived first', {'idle': 3, 'pick': 2, 'run': 4})


@algorithm(**_np_meta(
    'sjf', 'Shortest Job First', 'Of the processes that are ready, run the one with the shortest burst.',
    ['while any process is unfinished:', '    ready = arrived processes that have not run',
     '    if ready is empty: the CPU idles until the next arrival', '    p = the process in ready with the shortest burst',
     '    run p to completion', '    record p\'s start, finish and waiting time'], None,
    {'time': 'O(n^2)', 'space': 'O(n)', 'note': 'A heap makes selection O(log n).'},
    ['Gives the lowest average waiting time of any non-preemptive policy.', 'Needs burst times in advance, and long jobs can starve.']))
def sjf(p):
    return _nonpreemptive('sjf', 'SJF', p['processes'], lambda ready, t: min(ready, key=lambda x: (x['burst'], x['arrival'], x['id'])),
                          'shortest burst', {'idle': 2, 'pick': 3, 'run': 4})


@algorithm(**_np_meta(
    'priority', 'Priority Scheduling', 'Run the ready process with the smallest priority number, to completion.',
    ['while any process is unfinished:', '    ready = arrived processes that have not run',
     '    if ready is empty: the CPU idles until the next arrival', '    p = the process in ready with the lowest priority number',
     '    run p to completion', '    record p\'s start, finish and waiting time'], None,
    {'time': 'O(n^2)', 'space': 'O(n)', 'note': ''},
    ['Lower number means higher priority.', 'Low-priority processes can starve; aging fixes that.'], with_priority=True))
def priority(p):
    return _nonpreemptive('priority', 'Priority', p['processes'], lambda ready, t: min(ready, key=lambda x: (x['priority'], x['arrival'], x['id'])),
                          'highest priority', {'idle': 2, 'pick': 3, 'run': 4})


@algorithm(**_np_meta(
    'hrrn', 'Highest Response Ratio Next', 'Pick the process whose (waiting + burst) / burst is largest, so long waiters catch up.',
    ['while any process is unfinished:', '    ready = arrived processes that have not run',
     '    if ready is empty: the CPU idles until the next arrival',
     '    ratio(p) = (time waited + burst) / burst', '    p = the process in ready with the highest ratio',
     '    run p to completion'], None,
    {'time': 'O(n^2)', 'space': 'O(n)', 'note': ''},
    ['A compromise between SJF and FCFS: short jobs are favoured, but waiting raises a job\'s ratio until it runs.']))
def hrrn(p):
    def choose(ready, t):
        return max(ready, key=lambda x: ((t - x['arrival'] + x['burst']) / x['burst'], -x['arrival']))
    return _nonpreemptive('hrrn', 'HRRN', p['processes'], choose, 'highest response ratio', {'idle': 2, 'pick': 4, 'run': 5})


# --------------------------------------------------------------------------- preemptive
# Engine for schedulers that may interrupt (SRTF, preemptive Priority).
# `rank` gives each ready process a sort key; the smallest key runs. The choice is re-made at every arrival,
# so a running process is only ever run until the next arrival or until it finishes.
def _preemptive(alg_id, name, procs, rank: Callable, reason: str, lines: Dict[str, int]):
    pending = sorted(procs, key=lambda p: (p['arrival'], p['id']))
    rem = {p['id']: p['burst'] for p in procs}
    ready, t = [], 0
    slices, first, fin, trace = [], {}, {}, Trace()
    last = None
    while pending or ready:
        while pending and pending[0]['arrival'] <= t:
            ready.append(pending.pop(0))
        if not ready:
            trace.add(f'Nothing is ready. The CPU idles until t={pending[0]["arrival"]}.', [lines['idle']], pending[0]['arrival'])
            t = pending[0]['arrival']
            continue
        p = min(ready, key=lambda x: (rank(x, rem), x['arrival'], x['id']))
        first.setdefault(p['id'], t)
        # Run until the process ends or the next process arrives, whichever is first.
        run = rem[p['id']]
        if pending:
            run = min(run, pending[0]['arrival'] - t)
        # Consecutive runs of the same process are merged into one bar in the chart.
        if slices and slices[-1]['name'] == p['id'] and slices[-1]['start'] + slices[-1]['dur'] == t:
            slices[-1]['dur'] += run
        else:
            slices.append({'name': p['id'], 'start': t, 'dur': run})
        preempted = last is not None and last != p['id'] and rem[last] > 0
        rem[p['id']] -= run
        t += run
        note = f'{p["id"]} runs {t - run} to {t} ({reason}); {rem[p["id"]]} left.'
        if preempted:
            note = f'{last} is preempted. ' + note
        trace.add(note, [lines['pick'], lines['preempt'], lines['run']] if preempted else [lines['pick'], lines['run']], t)
        last = p['id']
        if rem[p['id']] == 0:
            ready.remove(p)
            fin[p['id']] = t
            trace.steps[-1]['lines'].append(lines['done'])
    return _finish(alg_id, name, procs, [{'label': 'CPU', 'slices': slices}], first, fin, trace, t)


@algorithm(id='srtf', name='Shortest Remaining Time First', category='cpu', family='cpu', viz='timeline',
           summary='Preemptive SJF: whenever a job arrives, the one with the least time left runs.',
           complexity={'time': 'O(n^2)', 'space': 'O(n)', 'note': ''},
           pseudocode=['at every arrival and every completion:', '    ready = arrived processes with time left',
                       '    p = the process in ready with the least remaining time',
                       '    if p is not the running process: preempt the running one', '    run p until the next arrival or until it finishes',
                       '    if p is finished: record its finish and waiting time'],
           params=[procs_param()], example={'processes': TEXTBOOK}, random=lambda rng: {'processes': random_procs(rng)},
           notes=['Optimal for average waiting time.', 'Preempting on every arrival causes many context switches.'],
           tags=['scheduling', 'preemptive'])
def srtf(p):
    return _preemptive('srtf', 'SRTF', p['processes'], lambda x, rem: rem[x['id']], 'least remaining time',
                       {'idle': 0, 'pick': 2, 'preempt': 3, 'run': 4, 'done': 5})


@algorithm(id='priority-preemptive', name='Preemptive Priority', category='cpu', family='cpu', viz='timeline',
           summary='A newly arrived higher-priority process immediately takes the CPU.',
           complexity={'time': 'O(n^2)', 'space': 'O(n)', 'note': ''},
           pseudocode=['at every arrival and every completion:', '    ready = arrived processes with time left',
                       '    p = the process in ready with the lowest priority number',
                       '    if p is not the running process: preempt the running one', '    run p until the next arrival or until it finishes',
                       '    if p is finished: record its finish and waiting time'],
           params=[procs_param(True)], example={'processes': TEXTBOOK},
           random=lambda rng: {'processes': random_procs(rng, True)},
           notes=['Good for urgent work, but a steady stream of high-priority jobs starves the rest.'],
           tags=['scheduling', 'preemptive'])
def priority_preemptive(p):
    return _preemptive('priority-preemptive', 'Priority (preemptive)', p['processes'], lambda x, rem: x['priority'],
                       'highest priority', {'idle': 0, 'pick': 2, 'preempt': 3, 'run': 4, 'done': 5})


# --------------------------------------------------------------------------- round robin
# ---- Round Robin ---------------------------------------------------------------------------------------
# Processes wait in a FIFO queue. Each gets at most `quantum` time units, then goes to the back if unfinished.
# Subtle rule: processes that arrive while another is running join the queue BEFORE the preempted one is re-queued.
@algorithm(id='rr', name='Round Robin', category='cpu', family='cpu', viz='timeline',
           summary='Each process gets one time quantum, then goes to the back of the queue.',
           complexity={'time': 'O(total burst / quantum)', 'space': 'O(n)', 'note': 'One step per time slice.'},
           pseudocode=['queue = arrived processes in arrival order', 'while the queue is not empty:', '    p = dequeue()',
                       '    run p for min(quantum, p.remaining)', '    enqueue processes that arrived meanwhile',
                       '    if p.remaining > 0: enqueue(p)', '    else: record finish and waiting time'],
           params=[procs_param(), Int('quantum', 'Time quantum', 2, 1, 50)],
           example={'processes': TEXTBOOK, 'quantum': 3},
           random=lambda rng: {'processes': random_procs(rng), 'quantum': rng.randint(2, 4)},
           notes=['Fair and responsive; response time is bounded by quantum x queue length.',
                  'A tiny quantum wastes time switching; a huge one degenerates to FCFS.'], tags=['scheduling', 'preemptive'])
def rr(p):
    procs, q = p['processes'], p['quantum']
    pending = sorted(procs, key=lambda x: (x['arrival'], x['id']))
    rem = {x['id']: x['burst'] for x in procs}
    queue, t = [], 0
    slices, first, fin, trace = [], {}, {}, Trace()

    def admit():
        while pending and pending[0]['arrival'] <= t:
            queue.append(pending.pop(0))
    while pending or queue:
        admit()
        if not queue:
            trace.add(f'Queue empty. The CPU idles until t={pending[0]["arrival"]}.', [1], pending[0]['arrival'])
            t = pending[0]['arrival']
            continue
        x = queue.pop(0)
        first.setdefault(x['id'], t)
        ran = min(q, rem[x['id']])
        slices.append({'name': x['id'], 'start': t, 'dur': ran})
        rem[x['id']] -= ran
        t += ran
        admit()
        if rem[x['id']] > 0:
            queue.append(x)
            trace.add(f'{x["id"]} runs {t - ran} to {t}, {rem[x["id"]]} left, goes to the back. Queue: {", ".join(y["id"] for y in queue)}.',
                      [2, 3, 4, 5], t)
        else:
            fin[x['id']] = t
            trace.add(f'{x["id"]} runs {t - ran} to {t} and finishes.', [2, 3, 6], t)
    return _finish('rr', 'Round Robin', procs, [{'label': 'CPU', 'slices': slices}], first, fin, trace, t)


# Lottery draws tickets with a seeded random generator, so a given seed always produces the same schedule.
# --------------------------------------------------------------------------- lottery and CFS
@algorithm(id='lottery', name='Lottery Scheduling', category='cpu', family='cpu', viz='timeline',
           summary='Each quantum, draw a random ticket; the holder runs. More tickets, more CPU on average.',
           complexity={'time': 'O(total burst / quantum x n)', 'space': 'O(n)', 'note': ''},
           pseudocode=['every quantum:', '    total = tickets held by ready processes', '    winner = a random number in [0, total)',
                       '    walk the ready list, summing tickets, until the sum passes winner', '    run that process for one quantum'],
           params=[procs_param(with_tickets=True), Int('quantum', 'Time quantum', 2, 1, 20), Seed()],
           example={'processes': procs_param(with_tickets=True)['default'], 'quantum': 2, 'seed': 3},
           random=lambda rng: {'processes': random_procs(rng, with_tickets=True), 'quantum': rng.randint(1, 3), 'seed': rng.randint(1, 999)},
           notes=['Probabilistic fairness: shares converge to ticket ratios over time.', 'Easy to add priorities or transfer tickets.'],
           tags=['scheduling', 'randomised'])
def lottery(p):
    rng = random.Random(p['seed'])
    procs, q = p['processes'], p['quantum']
    pending = sorted(procs, key=lambda x: (x['arrival'], x['id']))
    rem = {x['id']: x['burst'] for x in procs}
    ready, t = [], 0
    slices, first, fin, trace = [], {}, {}, Trace()
    while pending or ready:
        while pending and pending[0]['arrival'] <= t:
            ready.append(pending.pop(0))
        if not ready:
            trace.add(f'Nobody is ready. Idle until t={pending[0]["arrival"]}.', [0], pending[0]['arrival'])
            t = pending[0]['arrival']
            continue
        # Draw a winning ticket number in [0, total) and find whose ticket range contains it.
        total = sum(x['tickets'] for x in ready)
        draw = rng.randrange(total)
        acc, winner = 0, None
        for x in ready:
            acc += x['tickets']
            if draw < acc:
                winner = x
                break
        first.setdefault(winner['id'], t)
        ran = min(q, rem[winner['id']])
        if slices and slices[-1]['name'] == winner['id'] and slices[-1]['start'] + slices[-1]['dur'] == t:
            slices[-1]['dur'] += ran
        else:
            slices.append({'name': winner['id'], 'start': t, 'dur': ran})
        rem[winner['id']] -= ran
        t += ran
        trace.add(f'Ticket {draw} of {total} is held by {winner["id"]} ({winner["tickets"]} tickets). It runs {t - ran} to {t}.',
                  [1, 2, 3, 4], t)
        if rem[winner['id']] == 0:
            fin[winner['id']] = t
            ready.remove(winner)
    return _finish('lottery', 'Lottery', procs, [{'label': 'CPU', 'slices': slices}], first, fin, trace, t)


@algorithm(id='cfs', name='Completely Fair Scheduler', category='cpu', family='cpu', viz='timeline',
           summary='Linux-style: always run the process with the smallest virtual runtime; nice values scale how fast it grows.',
           complexity={'time': 'O(log n) per pick', 'space': 'O(n)', 'note': 'Linux keeps processes in a red-black tree.'},
           pseudocode=['weight = 1024 / 1.25^nice', 'p = the ready process with the smallest vruntime',
                       'slice = max(min_slice, latency x weight / total weight)', 'run p for slice',
                       'p.vruntime += slice x 1024 / weight', 'a process that wakes up starts at the smallest vruntime'],
           params=[procs_param(with_nice=True), Int('latency', 'Target latency', 12, 2, 100, 'Time in which every ready process should run once.'),
                   Int('min_slice', 'Minimum slice', 1, 1, 20)],
           example={'processes': procs_param(with_nice=True)['default'], 'latency': 12, 'min_slice': 1},
           random=lambda rng: {'processes': random_procs(rng, with_nice=True), 'latency': rng.choice([8, 12, 16]), 'min_slice': 1},
           notes=['A lower nice value means a bigger weight and slower vruntime growth, so more CPU time.',
                  'Fairness is by weighted virtual time, not by equal time.'], tags=['scheduling', 'linux'])
def cfs(p):
    procs = p['processes']
    # Linux maps nice values to weights: each nice step changes CPU share by about 25%. Nice 0 has weight 1024.
    weight = {x['id']: 1024 / (1.25 ** x['nice']) for x in procs}
    pending = sorted(procs, key=lambda x: (x['arrival'], x['id']))
    rem = {x['id']: x['burst'] for x in procs}
    vr: Dict[str, float] = {}
    ready, t = [], 0
    slices, first, fin, trace = [], {}, {}, Trace()
    while pending or ready:
        while pending and pending[0]['arrival'] <= t:
            x = pending.pop(0)
            # A newly arrived process starts at the smallest vruntime in the queue so it cannot monopolise the CPU.
            vr[x['id']] = min((vr[r['id']] for r in ready), default=0.0)
            ready.append(x)
        if not ready:
            trace.add(f'Nothing is ready. Idle until t={pending[0]["arrival"]}.', [1], pending[0]['arrival'])
            t = pending[0]['arrival']
            continue
        # The heart of CFS: run whoever has had the least (weighted) CPU so far.
        x = min(ready, key=lambda r: (vr[r['id']], r['arrival'], r['id']))
        total_w = sum(weight[r['id']] for r in ready)
        slice_ = max(p['min_slice'], int(p['latency'] * weight[x['id']] / total_w))
        ran = min(slice_, rem[x['id']])
        first.setdefault(x['id'], t)
        if slices and slices[-1]['name'] == x['id'] and slices[-1]['start'] + slices[-1]['dur'] == t:
            slices[-1]['dur'] += ran
        else:
            slices.append({'name': x['id'], 'start': t, 'dur': ran})
        # Virtual runtime grows slower for heavier (lower nice) processes, so they get picked more often.
        vr[x['id']] += ran * 1024 / weight[x['id']]
        rem[x['id']] -= ran
        t += ran
        trace.add(f'{x["id"]} has the smallest vruntime and runs {ran} ({t - ran} to {t}). Its vruntime becomes {vr[x["id"]]:.1f}.',
                  [1, 2, 3, 4], t)
        if rem[x['id']] == 0:
            fin[x['id']] = t
            ready.remove(x)
    return _finish('cfs', 'CFS', procs, [{'label': 'CPU', 'slices': slices}], first, fin, trace, t)


# ---- Multilevel Feedback Queue --------------------------------------------------------------------------
# Simulated one tick at a time because preemption and aging can change the decision at every tick.
# State per process: its current queue level, time remaining, and when it last entered a queue (for aging).
# --------------------------------------------------------------------------- MLFQ
@algorithm(id='mlfq', name='Multilevel Feedback Queue', category='cpu', family='cpu', viz='timeline',
           summary='Queues with rising quanta. Using a whole quantum demotes a process; waiting too long promotes it (aging).',
           complexity={'time': 'O(total burst x levels)', 'space': 'O(n)', 'note': 'Simulated tick by tick.'},
           pseudocode=['every tick:', '    new arrivals join queue 1', '    if a process waited >= aging in a lower queue: promote it',
                       '    if a higher queue is non-empty: preempt the running process',
                       '    run the head of the highest non-empty queue for one tick', '    if it finished: record completion',
                       '    else if it used its whole quantum: demote it one queue'],
           params=[procs_param(), Int('q1', 'Queue 1 quantum', 2, 1, 50), Int('q2', 'Queue 2 quantum', 4, 1, 50),
                   Int('q3', 'Queue 3 quantum', 8, 1, 50), Int('aging', 'Aging threshold', 0, 0, 500, '0 turns aging off.')],
           example={'processes': TEXTBOOK, 'q1': 2, 'q2': 4, 'q3': 8, 'aging': 0},
           random=lambda rng: {'processes': random_procs(rng), 'q1': rng.randint(1, 3), 'q2': rng.randint(3, 6),
                               'q3': rng.randint(6, 12), 'aging': rng.choice([0, 0, 6, 10])},
           notes=['Short jobs finish in the top queue; long jobs sink to the bottom.', 'Without aging, a stream of short jobs can starve a long one.'],
           tags=['scheduling', 'preemptive', 'aging'])
def mlfq(p):
    procs = p['processes']
    quanta = [p['q1'], p['q2'], p['q3']]
    levels, aging = 3, p['aging']
    pending = sorted(procs, key=lambda x: (x['arrival'], x['id']))
    st = {x['id']: {'level': 0, 'rem': x['burst'], 'since': x['arrival']} for x in procs}
    queues: List[List[Dict[str, Any]]] = [[] for _ in range(levels)]
    lanes = [{'label': f'Queue {i + 1} (q={quanta[i]})', 'slices': []} for i in range(levels)]
    first, fin, trace = {}, {}, Trace()
    current, used, t, new_slice = None, 0, 0, True

    # Move every process whose arrival time has come into queue 1.
    def admit():
        while pending and pending[0]['arrival'] <= t:
            x = pending.pop(0)
            st[x['id']].update(level=0, since=t)
            queues[0].append(x)
            trace.add(f'{x["id"]} arrives and joins queue 1.', [1], t)

    while pending or any(queues) or current:
        admit()
        # Aging: anything that has waited `aging` ticks in a lower queue moves up one level (prevents starvation).
        if aging:
            for lv in range(1, levels):
                for x in list(queues[lv]):
                    if t - st[x['id']]['since'] >= aging:
                        queues[lv].remove(x)
                        st[x['id']].update(level=lv - 1, since=t)
                        queues[lv - 1].append(x)
                        trace.add(f'{x["id"]} waited {aging} in queue {lv + 1}: promoted to queue {lv} (aging).', [2], t)
        # Preemption: if any higher queue has work, the running process is put back and the higher one runs.
        if current is not None:
            lv = st[current['id']]['level']
            if any(queues[k] for k in range(lv)):
                trace.add(f'{current["id"]} is preempted: a higher queue has work.', [3], t)
                st[current['id']]['since'] = t
                queues[lv].append(current)
                current, used, new_slice = None, 0, True
        if current is None:
            lv = next((k for k in range(levels) if queues[k]), None)
            if lv is None:
                t = pending[0]['arrival']
                continue
            current = queues[lv].pop(0)
            used, new_slice = 0, True
        # Run the chosen process for exactly one tick, then decide what happens to it.
        s = st[current['id']]
        first.setdefault(current['id'], t)
        lane = lanes[s['level']]['slices']
        if new_slice:
            lane.append({'name': current['id'], 'start': t, 'dur': 0})
            new_slice = False
        lane[-1]['dur'] += 1
        s['rem'] -= 1
        used += 1
        t += 1
        admit()
        if s['rem'] == 0:
            fin[current['id']] = t
            trace.add(f'{current["id"]} finishes at t={t}.', [4, 5], t)
            current, used = None, 0
        # Used its whole quantum without finishing: demote one level (the last queue just goes round again).
        elif used == quanta[s['level']]:
            target = min(s['level'] + 1, levels - 1)
            trace.add(f'{current["id"]} used its whole quantum in queue {s["level"] + 1}: '
                      + (f'demoted to queue {target + 1}.' if target != s['level'] else 'back of the last queue.'), [4, 6], t)
            s.update(level=target, since=t)
            queues[target].append(current)
            current, used = None, 0
    promos = sum(1 for st_ in trace.steps if 'promoted' in st_['note'])
    return _finish('mlfq', 'MLFQ', procs, lanes, first, fin, trace, t, extra=[tile('Promotions', promos)])


# ---- Multi-core -----------------------------------------------------------------------------------------
# One shared ready queue feeds several identical cores. A process keeps its core while it keeps running (core affinity).
# --------------------------------------------------------------------------- multi-core
@algorithm(id='multicore', name='Multi-core Scheduling', category='cpu', viz='timeline',
           summary='One shared ready queue feeding several cores. See the speedup and the idle time.',
           complexity={'time': 'O(total burst x cores)', 'space': 'O(n)', 'note': ''},
           pseudocode=['every tick:', '    add new arrivals to the shared ready queue', '    for each idle core:',
                       '        take the next process by policy', '    every busy core runs its process for one tick',
                       '    finished processes free their core'],
           params=[procs_param(), Int('cores', 'Cores', 2, 1, 8),
                   Choice('policy', 'Policy', [('fcfs', 'FCFS'), ('sjf', 'SJF'), ('srtf', 'SRTF'), ('rr', 'Round Robin')]),
                   Int('quantum', 'Quantum (Round Robin)', 2, 1, 20)],
           example={'processes': TEXTBOOK, 'cores': 2, 'policy': 'fcfs', 'quantum': 2},
           random=lambda rng: {'processes': random_procs(rng), 'cores': rng.randint(2, 4),
                               'policy': rng.choice(['fcfs', 'sjf', 'srtf', 'rr']), 'quantum': rng.randint(1, 3)},
           notes=['Adding cores helps only while there are enough ready processes.'], tags=['scheduling', 'multicore'])
def multicore(p):
    procs, cores, policy, q = p['processes'], p['cores'], p['policy'], p['quantum']
    by = {x['id']: x for x in procs}
    rem = {x['id']: x['burst'] for x in procs}
    order = sorted(procs, key=lambda x: (x['arrival'], x['id']))
    ready: List[str] = []
    on: List[Any] = [None] * cores
    left = [0] * cores
    lanes = [{'label': f'Core {c + 1}', 'slices': []} for c in range(cores)]
    first, fin, trace = {}, {}, Trace()
    t = nxt = 0

    def pick(cands):
        if policy == 'sjf':
            return min(cands, key=lambda i: (by[i]['burst'], by[i]['arrival'], i))
        if policy == 'srtf':
            return min(cands, key=lambda i: (rem[i], by[i]['arrival'], i))
        return cands[0]

    def admit():
        nonlocal nxt
        while nxt < len(order) and order[nxt]['arrival'] <= t:
            ready.append(order[nxt]['id'])
            nxt += 1
    while nxt < len(order) or ready or any(c is not None for c in on):
        admit()
        # SRTF re-decides every tick: gather everything runnable, keep the `cores` shortest, and put the rest back.
        if policy == 'srtf':
            pool = ready + [c for c in on if c is not None]
            chosen: List[str] = []
            for _ in range(min(cores, len(pool))):
                chosen.append(pick([i for i in pool if i not in chosen]))
            keep = {i: c for c, i in enumerate(on) if i in chosen}
            new: List[Any] = [None] * cores
            for i, c in keep.items():
                new[c] = i
            free = [c for c in range(cores) if new[c] is None]
            for i in chosen:
                if i not in keep:
                    new[free.pop(0)] = i
            ready = [i for i in pool if i not in chosen]
            on = new
        else:
            for c in range(cores):
                if on[c] is None and ready:
                    i = pick(ready)
                    ready.remove(i)
                    on[c] = i
                    left[c] = q
                    trace.add(f'Core {c + 1} takes {i} from the ready queue.', [2, 3], t)
        if all(c is None for c in on):
            t = order[nxt]['arrival']
            continue
        for c, i in enumerate(on):
            if i is None:
                continue
            first.setdefault(i, t)
            lane = lanes[c]['slices']
            if lane and lane[-1]['name'] == i and lane[-1]['start'] + lane[-1]['dur'] == t:
                lane[-1]['dur'] += 1
            else:
                lane.append({'name': i, 'start': t, 'dur': 1})
            rem[i] -= 1
        t += 1
        admit()
        for c, i in enumerate(on):
            if i is None:
                continue
            if rem[i] == 0:
                fin[i] = t
                on[c] = None
                trace.add(f'{i} finishes on core {c + 1} at t={t}.', [4, 5], t)
            elif policy == 'rr':
                left[c] -= 1
                if left[c] == 0:
                    ready.append(i)
                    on[c] = None
    # Speed-up versus one core is shown by racing this run against the one-core version in the comparison panel.
    # speed-up against one core running the same policy is shown by the front end via a second run
    busy = [sum(s['dur'] for s in lane['slices']) for lane in lanes]
    extra = [tile(f'Core {c + 1} busy', f'{b / t * 100:.0f}%') for c, b in enumerate(busy)] if t else []
    return _finish('multicore', f'{policy.upper()} x{cores}', procs, lanes, first, fin, trace, t, extra=extra)
