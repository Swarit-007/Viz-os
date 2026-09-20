"""Synchronisation: dining philosophers, producer-consumer, race conditions, readers-writers, Peterson."""

import random
from typing import Any, Dict, List

from ..core import Bool, Choice, Int, Seed, Trace, algorithm, result, tile

# ============================================================================ dining philosophers
# ---- Dining philosophers --------------------------------------------------------------------------------
# Five philosophers share five forks. To eat, one needs the fork on each side. The four variants below differ
# only in HOW they pick forks up, which decides whether a circular wait (deadlock) can happen.
# `tags` maps a kind of event (think, first fork, second fork, eat, ...) to a pseudocode line for highlighting.
DINING = {
    'naive': {
        'name': 'Dining Philosophers: naive',
        'summary': 'Everyone takes the left fork, then the right. If all get hungry together, everyone waits forever.',
        'pseudo': ['loop forever:', '    think()', '    pick up the left fork (wait if taken)', '    pick up the right fork (wait if taken)',
                   '    eat()', '    put down both forks'],
        'tags': {'think': 1, 'first': 2, 'second': 3, 'eat': 4, 'release': 5},
        'notes': ['Deadlock is possible: circular wait, hold and wait, no preemption, mutual exclusion all hold.'],
    },
    'ordered': {
        'name': 'Dining Philosophers: resource ordering',
        'summary': 'Forks are numbered; always pick up the lower-numbered one first. This breaks the circular wait.',
        'pseudo': ['loop forever:', '    think()', '    pick up the lower-numbered fork first', '    then pick up the higher-numbered fork',
                   '    eat()', '    put down both forks'],
        'tags': {'think': 1, 'first': 2, 'second': 3, 'eat': 4, 'release': 5},
        'notes': ['Deadlock is impossible: a cycle of waiting would need a fork numbered lower than itself.'],
    },
    'asymmetric': {
        'name': 'Dining Philosophers: asymmetric',
        'summary': 'Even philosophers reach left first, odd ones right first, so neighbours never wait on each other in a cycle.',
        'pseudo': ['loop forever:', '    think()', '    even philosopher: left fork first; odd: right fork first', '    then pick up the other fork',
                   '    eat()', '    put down both forks'],
        'tags': {'think': 1, 'first': 2, 'second': 3, 'eat': 4, 'release': 5},
        'notes': ['Simple and deadlock-free, but some philosophers may eat less often.'],
    },
    'waiter': {
        'name': 'Dining Philosophers: waiter',
        'summary': 'A waiter lets at most n-1 philosophers try to eat at once, so someone always gets both forks.',
        'pseudo': ['loop forever:', '    think()', '    ask the waiter for a seat (at most n-1 seated)', '    pick up left fork, then right fork',
                   '    eat()', '    put down both forks and leave the seat'],
        'tags': {'think': 1, 'seat': 2, 'first': 3, 'second': 3, 'eat': 4, 'release': 5},
        'notes': ['A counting semaphore initialised to n-1 does the waiter\'s job.'],
    },
}


# Factory: registers one algorithm per strategy so each gets its own pseudocode and notes.
def _philosophers(strategy):
    spec = DINING[strategy]

    def run(p):
        n, ticks, rng = p['n'], p['ticks'], random.Random(p['seed'])
        # Each philosopher is a tiny state machine: thinking -> hungry -> eating -> thinking.
        # Fork k sits between philosopher k-1 and k; philosopher i's left fork is i and right fork is (i+1) % n.
        THINK, HUNGRY, EAT = 'thinking', 'hungry', 'eating'
        state, held = [THINK] * n, [[] for _ in range(n)]
        timer = [0 if p['all_hungry'] else rng.randint(1, 4) for _ in range(n)]
        owner: List[Any] = [None] * n
        meals, seated, has_seat = [0] * n, 0, [False] * n
        trace, snaps, dead_at = Trace(), [], None

        # The order in which philosopher i reaches for forks. This single function is what each strategy changes.
        def order(i):
            left, right = i, (i + 1) % n
            if strategy == 'ordered':
                return sorted([left, right])
            if strategy == 'asymmetric' and i % 2 == 1:
                return [right, left]
            return [left, right]

        for tick in range(1, ticks + 1):
            events, tags, progress = [], set(), False
            for i in range(n):
                if state[i] == THINK:
                    timer[i] -= 1
                    if timer[i] <= 0:
                        state[i] = HUNGRY
                        events.append(f'P{i + 1} is hungry')
                        tags.add('think')
                        progress = True
                elif state[i] == HUNGRY:
                    if strategy == 'waiter' and not has_seat[i]:
                        if seated < n - 1:
                            seated += 1
                            has_seat[i] = True
                            events.append(f'P{i + 1} gets a seat')
                            tags.add('seat')
                            progress = True
                        else:
                            events.append(f'P{i + 1} waits for a seat')
                            tags.add('seat')
                            continue
                    first, second = order(i)
                    if first not in held[i]:
                        if owner[first] is None:
                            owner[first] = i
                            held[i].append(first)
                            events.append(f'P{i + 1} picks up fork {first + 1}')
                            progress = True
                        else:
                            events.append(f'P{i + 1} waits for fork {first + 1}')
                        tags.add('first')
                    elif second not in held[i]:
                        tags.add('second')
                        if owner[second] is None:
                            owner[second] = i
                            held[i].append(second)
                            state[i] = EAT
                            timer[i] = rng.randint(2, 3)
                            meals[i] += 1
                            events.append(f'P{i + 1} picks up fork {second + 1} and eats')
                            tags.add('eat')
                            progress = True
                        else:
                            events.append(f'P{i + 1} holds fork {first + 1} and waits for fork {second + 1}')
                elif state[i] == EAT:
                    timer[i] -= 1
                    progress = True
                    if timer[i] <= 0:
                        for f in held[i]:
                            owner[f] = None
                        held[i] = []
                        state[i] = THINK
                        timer[i] = rng.randint(1, 4)
                        if has_seat[i]:
                            has_seat[i] = False
                            seated -= 1
                        events.append(f'P{i + 1} puts down both forks and thinks')
                        tags.add('release')
            # Deadlock = nobody could do anything this tick, and everybody is hungry holding exactly one fork.
            dead = (not progress) and all(s == HUNGRY for s in state) and all(len(h) == 1 for h in held) and strategy != 'waiter'
            snaps.append({'philosophers': [{'id': i + 1, 'state': state[i], 'holding': [f + 1 for f in held[i]], 'meals': meals[i]}
                                           for i in range(n)],
                          'forks': [{'id': f + 1, 'owner': None if owner[f] is None else owner[f] + 1} for f in range(n)],
                          'deadlock': dead})
            trace.add(f'Tick {tick}: ' + ('; '.join(events) if events else 'nothing happens') + ('. DEADLOCK.' if dead else '.'),
                      sorted(spec['tags'][t] for t in tags if t in spec['tags']), tick - 1)
            if dead:
                dead_at = tick
                break
        summary = [tile('Meals eaten', sum(meals)), tile('Deadlock', 'yes' if dead_at else 'no', f'tick {dead_at}' if dead_at else None,
                                                          'bad' if dead_at else 'good'),
                   tile('Fewest meals', min(meals)), tile('Most meals', max(meals))]
        verdict = {'ok': dead_at is None, 'label': 'Deadlock' if dead_at else 'No deadlock',
                   'text': (f'At tick {dead_at} every philosopher holds one fork and waits for another.' if dead_at
                            else f'{sum(meals)} meals in {len(snaps)} ticks.')}
        table = {'title': 'Meals per philosopher', 'headers': ['Philosopher', 'Meals'],
                 'rows': [[{'proc': f'P{i + 1}'}, m] for i, m in enumerate(meals)]}
        return result(f'dining-{strategy}', 'philosophers', summary, trace, {'n': n, 'snapshots': snaps}, table, verdict)

    def rnd(rng):
        return {'n': rng.randint(3, 7), 'ticks': 40, 'seed': rng.randint(1, 999), 'all_hungry': rng.random() < 0.6}

    algorithm(id=f'dining-{strategy}', name=spec['name'], category='sync', family='dining', viz='philosophers', summary=spec['summary'],
              complexity={'time': 'O(ticks x n)', 'space': 'O(n)', 'note': ''}, pseudocode=spec['pseudo'],
              params=[Int('n', 'Philosophers', 5, 2, 8), Int('ticks', 'Ticks', 40, 5, 200), Seed(),
                      Bool('all_hungry', 'Everyone hungry at tick 0', strategy == 'naive', 'Makes the naive strategy deadlock every time.')],
              example={'n': 5, 'ticks': 40, 'seed': 1, 'all_hungry': strategy == 'naive'}, random=rnd, notes=spec['notes'],
              tags=['synchronization', 'deadlock'])(run)


for _s in DINING:
    _philosophers(_s)


# ============================================================================ producer-consumer
# ---- Producer-consumer -----------------------------------------------------------------------------------
# A bounded buffer shared by producers and consumers. With semaphores (`safe`), a producer waits on `empty` and a
# consumer waits on `full`. Without them the same timing overflows the buffer and reads from an empty one.
def _prodcons(safe: bool):
    def run(p):
        size, n_p, n_c = p['buffer'], p['producers'], p['consumers']
        rng = random.Random(p['seed'])
        count, empty, full = 0, size, 0
        produced = consumed = over = under = 0
        cool = {('P', i): rng.randint(0, p['p_period']) for i in range(n_p)}
        cool.update({('C', i): rng.randint(0, p['c_period']) for i in range(n_c)})
        trace, snaps = Trace(), []
        for tick in range(1, p['ticks'] + 1):
            events, blocked, lines = [], [], set()
            for kind, idx in sorted(cool):
                name = f'{kind}{idx + 1}'
                if cool[(kind, idx)] > 0:
                    cool[(kind, idx)] -= 1
                    continue
                period = p['p_period'] if kind == 'P' else p['c_period']
                if kind == 'P':
                    if safe and empty == 0:
                        blocked.append(name)
                        events.append(f'{name} blocks on wait(empty): the buffer is full')
                        lines.add(2)
                        continue
                    if safe:
                        empty, full = empty - 1, full + 1
                    count += 1
                    produced += 1
                    lines.update([1, 3] if safe else [1, 2])
                    if count > size:
                        over += 1
                        events.append(f'{name} inserts into a full buffer: OVERFLOW ({count}/{size})')
                    else:
                        events.append(f'{name} inserts an item ({count}/{size})')
                else:
                    if safe and full == 0:
                        blocked.append(name)
                        events.append(f'{name} blocks on wait(full): the buffer is empty')
                        lines.add(6)
                        continue
                    if safe:
                        full, empty = full - 1, empty + 1
                    if count == 0:
                        under += 1
                        events.append(f'{name} reads an empty buffer: UNDERFLOW')
                    else:
                        count -= 1
                        consumed += 1
                        events.append(f'{name} removes an item ({count}/{size})')
                    lines.update([6, 7] if safe else [4])
                cool[(kind, idx)] = period - 1 + rng.randint(0, 1)
            snaps.append({'buffer': count, 'empty': empty, 'full': full, 'blocked': blocked, 'over': count > size})
            trace.add(f'Tick {tick}: ' + ('; '.join(events) if events else 'everyone is resting') + '.', sorted(lines), tick - 1)
        broken = over + under > 0
        summary = [tile('Produced', produced), tile('Consumed', consumed),
                   tile('Overflows', over, tone='bad' if over else None), tile('Underflows', under, tone='bad' if under else None)]
        verdict = {'ok': not broken, 'label': 'Unsafe' if broken else 'Safe',
                   'text': ('Without semaphores the buffer overflows and consumers read nothing.' if broken
                            else 'Semaphores keep the buffer between empty and full; blocked threads just wait.')}
        return result('prodcons-' + ('semaphore' if safe else 'unsafe'), 'buffer', summary, trace,
                      {'capacity': size, 'snapshots': snaps, 'producers': n_p, 'consumers': n_c}, None, verdict)

    def rnd(rng):
        return {'buffer': rng.randint(2, 8), 'producers': rng.randint(1, 3), 'consumers': rng.randint(1, 3),
                'p_period': rng.randint(1, 3), 'c_period': rng.randint(1, 4), 'ticks': 40, 'seed': rng.randint(1, 999)}

    pseudo = (['producer: loop', '    item = produce()', '    wait(empty)', '    insert(item)', '    signal(full)',
               'consumer: loop', '    wait(full)', '    item = remove()', '    signal(empty)'] if safe else
              ['producer: loop', '    item = produce()', '    insert(item)   // no check', 'consumer: loop', '    item = remove()   // no check'])
    algorithm(id='prodcons-' + ('semaphore' if safe else 'unsafe'),
              name='Producer-Consumer' + (': semaphores' if safe else ': unsynchronised'), category='sync', family='prodcons',
              viz='buffer', summary=('A bounded buffer guarded by counting semaphores: producers wait when it is full, consumers when empty.'
                                     if safe else 'The same buffer with no synchronisation: it overflows and underflows.'),
              complexity={'time': 'O(ticks x threads)', 'space': 'O(1)', 'note': ''}, pseudocode=pseudo,
              params=[Int('buffer', 'Buffer size', 4, 1, 20), Int('producers', 'Producers', 1, 1, 4), Int('consumers', 'Consumers', 1, 1, 4),
                      Int('p_period', 'Producer period', 1, 1, 20), Int('c_period', 'Consumer period', 2, 1, 20),
                      Int('ticks', 'Ticks', 40, 5, 200), Seed()],
              example={'buffer': 4, 'producers': 2 if not safe else 1, 'consumers': 1, 'p_period': 1, 'c_period': 2, 'ticks': 40, 'seed': 1},
              random=rnd, notes=(['empty counts free slots, full counts filled slots; both start consistent with an empty buffer.'] if safe
                                 else ['Compare with the semaphore version: identical timing, completely different safety.']),
              tags=['synchronization', 'semaphore'])(run)


_prodcons(True)
_prodcons(False)


# ============================================================================ race condition
# ---- Race condition ----------------------------------------------------------------------------------------
# `counter += 1` is really three steps: load, add, store. A seeded scheduler interleaves the threads one step at a
# time. Without a lock two threads can load the same value, so one increment overwrites the other (a lost update).
# With a lock, load-add-store form a critical section that only one thread can be inside.
def _race(lock: bool):
    def run(p):
        threads, incs, rng = p['threads'], p['increments'], random.Random(p['seed'])
        counter, regs, pc, done, owner = 0, [None] * threads, [0] * threads, [0] * threads, None
        trace, snaps = Trace(), []
        before = 0
        while any(d < incs for d in done):
            runnable = [t for t in range(threads) if done[t] < incs and not (lock and pc[t] == 0 and owner not in (None, t))]
            t = rng.choice(runnable)
            lost, ln = False, 0
            # pc[t] is which of the three instructions thread t executes next (0 load, 1 add, 2 store).
            if pc[t] == 0:
                if lock:
                    owner = t
                regs[t] = counter
                op, ln = f'load counter ({counter})', 1 if lock else 0
            elif pc[t] == 1:
                regs[t] += 1
                op, ln = f'add 1 (register = {regs[t]})', 2 if lock else 1
            else:
                counter = regs[t]
                # A store is a lost update when it does not equal the previous counter value plus one.
                lost = counter != before + 1
                op, ln = f'store counter = {counter}', 3 if lock else 2
                done[t] += 1
                if lock:
                    owner = None
            pc[t] = (pc[t] + 1) % 3
            before = counter
            snaps.append({'counter': counter, 'regs': list(regs), 'thread': t + 1, 'op': op, 'lost': lost,
                          'owner': None if owner is None else owner + 1})
            lines = [ln] + ([0] if lock and pc[t] == 1 else []) + ([4] if lock and pc[t] == 0 else [])
            trace.add(f'T{t + 1}: {op}' + ('. This overwrites another thread\'s update.' if lost else '.'), lines, len(snaps) - 1)
        lost_n = threads * incs - counter
        summary = [tile('Final counter', counter), tile('Expected', threads * incs), tile('Lost updates', lost_n, tone='bad' if lost_n else 'good')]
        verdict = {'ok': lost_n == 0, 'label': 'Correct' if lost_n == 0 else 'Race condition',
                   'text': 'No update was lost.' if lost_n == 0 else f'{lost_n} increments were lost because threads interleaved read, add and write.'}
        return result('race-lock' if lock else 'race-unlocked', 'race', summary, trace,
                      {'threads': threads, 'expected': threads * incs, 'snapshots': snaps}, None, verdict)

    algorithm(id='race-lock' if lock else 'race-unlocked', name='Race Condition: ' + ('mutex lock' if lock else 'no lock'), category='sync',
              family='race', viz='race',
              summary=('Threads increment a shared counter inside a lock; every update survives.' if lock else
                       'Threads increment a shared counter with no lock; interleaved load, add and store lose updates.'),
              complexity={'time': 'O(threads x increments)', 'space': 'O(threads)', 'note': ''},
              pseudocode=(['acquire(lock)', 'load  reg, counter', 'add   reg, 1', 'store counter, reg', 'release(lock)'] if lock
                          else ['load  reg, counter', 'add   reg, 1', 'store counter, reg']),
              params=[Int('threads', 'Threads', 2, 2, 4), Int('increments', 'Increments each', 5, 1, 20), Seed()],
              example={'threads': 2, 'increments': 5, 'seed': 1},
              random=lambda rng: {'threads': rng.randint(2, 4), 'increments': rng.randint(3, 8), 'seed': rng.randint(1, 999)},
              notes=['counter += 1 is three machine steps, not one.'], tags=['synchronization', 'mutex'])(run)


_race(False)
_race(True)


# ============================================================================ readers-writers
# ---- Readers-writers -----------------------------------------------------------------------------------------
# Any number of readers may read together, but a writer needs the data alone. Giving readers priority lets a
# steady stream of readers starve writers; giving writers priority can starve readers.
@algorithm(id='readers-writers', name='Readers-Writers', category='sync', viz='sync-state', family='rw',
           summary='Many readers may share data, but a writer needs it alone. Reader priority can starve writers.',
           complexity={'time': 'O(ticks x threads)', 'space': 'O(threads)', 'note': ''},
           pseudocode=['reader:', '    wait(mutex); readers++; if readers == 1: wait(write); signal(mutex)', '    read()',
                       '    wait(mutex); readers--; if readers == 0: signal(write); signal(mutex)', 'writer:', '    wait(write)',
                       '    write()', '    signal(write)'],
           params=[Choice('priority', 'Priority', [('readers', 'Readers first'), ('writers', 'Writers first')]),
                   Int('readers', 'Readers', 4, 1, 6), Int('writers', 'Writers', 2, 1, 4), Int('ticks', 'Ticks', 30, 5, 100), Seed()],
           example={'priority': 'readers', 'readers': 4, 'writers': 2, 'ticks': 30, 'seed': 2},
           random=lambda rng: {'priority': rng.choice(['readers', 'writers']), 'readers': rng.randint(2, 6), 'writers': rng.randint(1, 3),
                               'ticks': 30, 'seed': rng.randint(1, 999)},
           notes=['With readers first a steady stream of readers keeps a writer waiting indefinitely.',
                  'Writers first fixes writer starvation but can starve readers instead.'], tags=['synchronization', 'semaphore'])
def readers_writers(p):
    rng = random.Random(p['seed'])
    actors = ([{'id': f'R{i + 1}', 'kind': 'reader'} for i in range(p['readers'])]
              + [{'id': f'W{i + 1}', 'kind': 'writer'} for i in range(p['writers'])])
    for a in actors:
        a.update(state='idle', left=rng.randint(0, 4), waited=0, served=0)
    active_r, writer, trace, snaps = 0, None, Trace(), []
    starved = 0
    for tick in range(1, p['ticks'] + 1):
        events, lines = [], set()
        for a in actors:  # progress running and idle actors
            if a['state'] == 'reading' or a['state'] == 'writing':
                a['left'] -= 1
                if a['left'] <= 0:
                    if a['kind'] == 'reader':
                        active_r -= 1
                        lines.add(3)
                    else:
                        writer = None
                        lines.add(7)
                    a['state'], a['left'] = 'idle', rng.randint(1, 5)
                    events.append(f'{a["id"]} finishes')
            elif a['state'] == 'idle':
                a['left'] -= 1
                if a['left'] <= 0:
                    a['state'] = 'waiting'
                    events.append(f'{a["id"]} wants access')
        waiting_w = [a for a in actors if a['kind'] == 'writer' and a['state'] == 'waiting']
        for a in actors:
            if a['state'] != 'waiting':
                continue
            if a['kind'] == 'reader':
                blocked = writer is not None or (p['priority'] == 'writers' and waiting_w)
                if not blocked:
                    a.update(state='reading', left=rng.randint(1, 3))
                    active_r += 1
                    a['served'] += 1
                    events.append(f'{a["id"]} starts reading ({active_r} readers)')
                    lines.update([1, 2])
                else:
                    a['waited'] += 1
            else:
                if writer is None and active_r == 0:
                    a.update(state='writing', left=rng.randint(1, 3))
                    writer = a['id']
                    a['served'] += 1
                    events.append(f'{a["id"]} starts writing')
                    lines.update([5, 6])
                    waiting_w = [w for w in waiting_w if w is not a]
                else:
                    a['waited'] += 1
        snaps.append({'actors': [{'id': a['id'], 'kind': a['kind'], 'state': a['state'], 'detail': f'served {a["served"]}, waited {a["waited"]}'}
                                 for a in actors],
                      'vars': [{'label': 'readers inside', 'value': active_r}, {'label': 'writer inside', 'value': writer or 'none'}],
                      'alert': False})
        trace.add(f'Tick {tick}: ' + ('; '.join(events) if events else 'no change') + '.', sorted(lines), tick - 1)
    w_served = sum(a['served'] for a in actors if a['kind'] == 'writer')
    r_served = sum(a['served'] for a in actors if a['kind'] == 'reader')
    max_w = max(a['waited'] for a in actors if a['kind'] == 'writer')
    starved = w_served == 0
    summary = [tile('Read sessions', r_served), tile('Write sessions', w_served, tone='bad' if starved else None),
               tile('Longest writer wait', max_w, 'ticks')]
    verdict = {'ok': not starved, 'label': 'Writers starved' if starved else 'Everyone served',
               'text': 'No writer ever got the data.' if starved else f'{r_served} reads and {w_served} writes completed.'}
    return result('readers-writers', 'sync-state', summary, trace, {'snapshots': snaps}, None, verdict)


# ============================================================================ Peterson
# ---- Peterson's algorithm ------------------------------------------------------------------------------------
# Two threads, two `flag` variables and a `turn` variable give mutual exclusion with no special hardware.
# Turning the protocol off lets both threads into the critical section, which the simulation flags as a collision.
@algorithm(id='peterson', name='Peterson\'s Algorithm', category='sync', viz='sync-state', family='mutex',
           summary='Two threads share a critical section using only two flags and a turn variable. Switch it off to see them collide.',
           complexity={'time': 'O(ticks)', 'space': 'O(1)', 'note': 'Works for two threads.'},
           pseudocode=['flag[i] = true', 'turn = j', 'while flag[j] and turn == j: spin', 'critical section', 'flag[i] = false'],
           params=[Bool('protocol', 'Use Peterson\'s protocol', True), Int('rounds', 'Rounds each', 3, 1, 8), Seed()],
           example={'protocol': True, 'rounds': 3, 'seed': 1},
           random=lambda rng: {'protocol': rng.random() < 0.7, 'rounds': rng.randint(2, 5), 'seed': rng.randint(1, 999)},
           notes=['Guarantees mutual exclusion, progress and bounded waiting for two threads.',
                  'Needs sequentially consistent memory; real CPUs need memory barriers.'], tags=['synchronization', 'mutex'])
def peterson(p):
    rng = random.Random(p['seed'])
    flag, turn = [False, False], 0
    pc, rounds, cs_left = [0, 0], [0, 0], [0, 0]
    trace, snaps, violations, in_cs_count = Trace(), [], 0, [0, 0]
    while any(r < p['rounds'] for r in rounds) and len(snaps) < 400:
        live = [i for i in (0, 1) if rounds[i] < p['rounds']]
        i = rng.choice(live)
        j = 1 - i
        note, line = '', 0
        if not p['protocol'] and pc[i] < 3:
            pc[i] = 3
        if pc[i] == 0:
            flag[i], pc[i], note, line = True, 1, f'T{i + 1} sets flag[{i}] = true (I want in)', 0
        elif pc[i] == 1:
            turn, pc[i], note, line = j, 2, f'T{i + 1} sets turn = {j} (you go first)', 1
        elif pc[i] == 2:
            if flag[j] and turn == j:
                note, line = f'T{i + 1} spins: T{j + 1} wants in and it is T{j + 1}\'s turn', 2
            else:
                pc[i], cs_left[i], note, line = 3, 2, f'T{i + 1} may enter', 2
        elif pc[i] == 3:
            if cs_left[i] == 0:
                cs_left[i] = 2
            cs_left[i] -= 1
            in_cs_count[i] = 1
            note, line = f'T{i + 1} is in the critical section', 3
            if cs_left[i] == 0:
                pc[i] = 4
        else:
            flag[i], pc[i], in_cs_count[i] = False, 0, 0
            rounds[i] += 1
            note, line = f'T{i + 1} leaves and sets flag[{i}] = false', 4
            if not p['protocol']:
                pc[i] = 3
        in_cs = [k for k in (0, 1) if in_cs_count[k] or (pc[k] == 3 and cs_left[k] > 0)]
        collide = len(in_cs) == 2
        if collide:
            violations += 1
            note += '. BOTH threads are in the critical section!'
        state = lambda k: ('critical section' if k in in_cs else 'spinning' if pc[k] == 2 else 'done' if rounds[k] >= p['rounds'] else 'not in CS')  # noqa: E731
        snaps.append({'actors': [{'id': f'T{k + 1}', 'kind': 'thread', 'state': state(k), 'detail': f'round {rounds[k]}/{p["rounds"]}'} for k in (0, 1)],
                      'vars': [{'label': 'flag[0]', 'value': str(flag[0]).lower()}, {'label': 'flag[1]', 'value': str(flag[1]).lower()},
                               {'label': 'turn', 'value': turn}], 'alert': collide})
        trace.add(note + '.', [line] if p['protocol'] else [3], len(snaps) - 1)
    summary = [tile('Steps', len(snaps)), tile('Collisions', violations, tone='bad' if violations else 'good')]
    verdict = {'ok': violations == 0, 'label': 'Mutual exclusion held' if violations == 0 else 'Mutual exclusion violated',
               'text': 'Never were both threads inside at once.' if violations == 0 else f'Both threads shared the critical section on {violations} steps.'}
    return result('peterson', 'sync-state', summary, trace, {'snapshots': snaps}, None, verdict)
