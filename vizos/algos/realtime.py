"""Real-time scheduling of periodic tasks: Earliest Deadline First and Rate Monotonic."""

import math
from typing import Any, Dict, List

from ..core import Col, Int, Table, Trace, algorithm, result, tile

TASKS = [{'id': 'T1', 'period': 4, 'wcet': 1, 'deadline': 4}, {'id': 'T2', 'period': 5, 'wcet': 2, 'deadline': 5},
         {'id': 'T3', 'period': 10, 'wcet': 3, 'deadline': 10}]


def tasks_param():
    return Table('tasks', 'Periodic tasks', [Col('period', 'Period', 1, 100), Col('wcet', 'Run time (C)', 1, 100),
                                             Col('deadline', 'Deadline', 1, 100)], TASKS, max_rows=6, id_prefix='T')


def _lcm(values):
    out = 1
    for v in values:
        out = out * v // math.gcd(out, v)
    return out


def _simulate(alg_id, tasks, horizon, edf: bool):
    hyper = _lcm(t['period'] for t in tasks)
    end = min(horizon, hyper) if horizon else min(hyper, 120)
    jobs: List[Dict[str, Any]] = []
    marks = []
    for task in tasks:
        for k in range(end // task['period'] + 1):
            release = k * task['period']
            if release >= end:
                break
            jobs.append({'task': task['id'], 'job': k + 1, 'release': release, 'deadline': release + task['deadline'],
                         'rem': task['wcet'], 'period': task['period'], 'done': None})
            marks.append({'t': release, 'name': task['id'], 'kind': 'release'})
            if release + task['deadline'] <= end:
                marks.append({'t': release + task['deadline'], 'name': task['id'], 'kind': 'deadline'})
    slices, trace, misses, current = [], Trace(), [], None
    for t in range(end):
        ready = [j for j in jobs if j['release'] <= t and j['rem'] > 0]
        if not ready:
            current = None
            continue
        key = (lambda j: (j['deadline'], j['release'], j['task'])) if edf else (lambda j: (j['period'], j['release'], j['task']))
        job = min(ready, key=key)
        if slices and slices[-1]['name'] == job['task'] and slices[-1]['start'] + slices[-1]['dur'] == t and current is job:
            slices[-1]['dur'] += 1
        else:
            slices.append({'name': job['task'], 'start': t, 'dur': 1, 'job': job['job']})
            why = f'earliest deadline ({job["deadline"]})' if edf else f'shortest period ({job["period"]})'
            pre = ' It preempts the running job.' if current is not None and current['rem'] > 0 and current is not job else ''
            trace.add(f't={t}: {job["task"]}#{job["job"]} runs ({why}).{pre}', [1, 2, 3] if not pre else [1, 2, 3, 4], t + 1)
        current = job
        job['rem'] -= 1
        if job['rem'] == 0:
            job['done'] = t + 1
    for job in jobs:
        if job['deadline'] <= end and (job['done'] is None or job['done'] > job['deadline']):
            misses.append(job)
            marks.append({'t': job['deadline'], 'name': job['task'], 'kind': 'miss'})
            trace.add(f'Deadline miss: {job["task"]}#{job["job"]} needed to finish by t={job["deadline"]}.', [5], job['deadline'])
    trace.steps.sort(key=lambda s: s['at'])
    util = sum(t['wcet'] / t['period'] for t in tasks)
    n = len(tasks)
    bound = n * (2 ** (1 / n) - 1)
    if edf:
        verdict_ok = not misses
        theory = 'EDF is feasible whenever utilisation is at most 1 (with deadline = period).'
    else:
        verdict_ok = not misses
        theory = f'RMS is guaranteed when utilisation is at most {bound:.3f}; above that it can still work, as here.' \
            if util > bound and not misses else f'RMS guarantee bound for {n} tasks: {bound:.3f}.'
    summary = [tile('Utilisation', f'{util:.3f}', 'sum of C/T', 'bad' if util > 1 else None),
               tile('RMS bound', f'{bound:.3f}', f'{n} tasks'), tile('Deadline misses', len(misses), tone='bad' if misses else 'good'),
               tile('Simulated', f'{end}', f'hyperperiod {hyper}')]
    lanes = [{'label': t['id'], 'slices': [s for s in slices if s['name'] == t['id']]} for t in tasks]
    table = {'title': 'Job outcomes', 'headers': ['Job', 'Release', 'Deadline', 'Finished', 'Result'],
             'rows': [[{'proc': j['task']}, j['release'], j['deadline'], j['done'] if j['done'] is not None else '-',
                       'missed' if j in misses else ('on time' if j['done'] is not None else 'beyond horizon')]
                      for j in sorted(jobs, key=lambda j: (j['release'], j['task']))]}
    data = {'lanes': lanes, 'total': end, 'marks': marks, 'rows': [], 'tasks': tasks, 'theory': theory}
    verdict = {'ok': verdict_ok, 'label': 'All deadlines met' if verdict_ok else f'{len(misses)} deadline miss(es)', 'text': theory}
    return result(alg_id, 'timeline', summary, trace, data, table, verdict)


def _meta(alg_id, name, summary, pseudo, notes):
    return dict(id=alg_id, name=name, category='realtime', summary=summary, viz='timeline', family='realtime',
                complexity={'time': 'O(horizon x jobs)', 'space': 'O(jobs)', 'note': 'Simulated tick by tick.'},
                pseudocode=pseudo, params=[tasks_param(), Int('horizon', 'Time to simulate', 0, 0, 400, '0 = one hyperperiod (up to 120).')],
                example={'tasks': TASKS, 'horizon': 0},
                random=None, notes=notes, tags=['real-time', 'periodic'])


def _random_tasks(rng):
    while True:
        rows = []
        for i in range(rng.randint(2, 4)):
            period = rng.choice([4, 5, 6, 8, 10, 12])
            rows.append({'id': f'T{i + 1}', 'period': period, 'wcet': rng.randint(1, max(1, period // 3)), 'deadline': period})
        if sum(r['wcet'] / r['period'] for r in rows) <= 1.15:
            return {'tasks': rows, 'horizon': 0}


meta = _meta('edf', 'Earliest Deadline First', 'At every tick, run the released job whose absolute deadline is soonest.',
             ['every tick:', '    ready = released jobs with time left', '    job = the job in ready with the earliest absolute deadline',
              '    if job is not the running job: preempt', '    a job unfinished at its deadline is a miss'],
             ['Optimal for a single CPU: if any schedule meets all deadlines, EDF does.', 'Under overload it can miss many deadlines in a row.'])
meta['random'] = _random_tasks
algorithm(**meta)(lambda p: _simulate('edf', p['tasks'], p['horizon'], True))

meta = _meta('rms', 'Rate Monotonic', 'Fixed priorities: the shorter a task\'s period, the higher its priority.',
             ['assign priority by period: shorter period, higher priority', 'every tick:', '    job = the released job with the shortest period',
              '    if job is not the running job: preempt', '    a job unfinished at its deadline is a miss'],
             ['Simple, static and predictable.', 'Guaranteed only up to a utilisation bound of n(2^(1/n) - 1), about 69% for many tasks.'])
meta['random'] = _random_tasks
algorithm(**meta)(lambda p: _simulate('rms', p['tasks'], p['horizon'], False))
