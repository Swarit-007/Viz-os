"""Synchronisation simulations: dining philosophers, producer-consumer, race condition.

All simulations are deterministic for a given `seed` and produce one snapshot per tick.
"""

import random
from typing import Any, Dict, List

from .common import ValidationError, require_int

STRATEGIES = ('naive', 'ordered', 'asymmetric', 'waiter')
MAX_TICKS = 300


class SyncModule:
    # ------------------------------------------------------------------ philosophers
    def philosophers(self, n: Any = 5, strategy: str = 'naive', ticks: Any = 60, seed: Any = 1,
                     synchronized_start: Any = False) -> Dict[str, Any]:
        """Simulate n philosophers sharing n forks.

        Fork i lies between philosopher i-1 and i; philosopher i's "left" fork is i and
        "right" fork is (i+1) % n. Picking up the two forks takes two ticks (a context
        switch can happen in between), which is what makes the naive strategy deadlock.

        strategy:
            naive       left fork first, then right (can deadlock)
            ordered     always the lower-numbered fork first (breaks the cycle)
            asymmetric  even philosophers left first, odd right first
            waiter      at most n-1 philosophers may try to eat at once
        synchronized_start: everyone becomes hungry on tick 0 (makes naive deadlock certain).
        """
        n = require_int(n, 'n', 2, 8)
        ticks = require_int(ticks, 'ticks', 1, MAX_TICKS)
        seed = require_int(seed, 'seed', 0, 10_000_000)
        if not isinstance(strategy, str) or strategy.lower() not in STRATEGIES:
            raise ValidationError(f'Unknown strategy: {strategy}. Must be one of: {", ".join(STRATEGIES)}')
        strategy = strategy.lower()
        rng = random.Random(seed)

        THINK, HUNGRY, EAT = 'thinking', 'hungry', 'eating'
        state = [THINK] * n
        timer = [0 if synchronized_start else rng.randint(1, 4) for _ in range(n)]
        held: List[List[int]] = [[] for _ in range(n)]
        owner: List[Any] = [None] * n
        meals = [0] * n
        seated = 0  # waiter semaphore (philosophers currently allowed to compete)
        has_seat = [False] * n
        snapshots, deadlock_at = [], None

        def order(i: int) -> List[int]:
            left, right = i, (i + 1) % n
            if strategy == 'ordered':
                return sorted([left, right])
            if strategy == 'asymmetric' and i % 2 == 1:
                return [right, left]
            return [left, right]

        for tick in range(1, ticks + 1):
            events, progress = [], False
            for i in range(n):
                if state[i] == THINK:
                    timer[i] -= 1
                    if timer[i] <= 0:
                        state[i] = HUNGRY
                        events.append(f'P{i + 1} is hungry')
                        progress = True
                elif state[i] == HUNGRY:
                    if strategy == 'waiter' and not has_seat[i]:
                        if seated < n - 1:
                            seated += 1
                            has_seat[i] = True
                            events.append(f'P{i + 1} gets a seat from the waiter')
                            progress = True
                        else:
                            events.append(f'P{i + 1} waits for a seat')
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
                    elif second not in held[i]:
                        if owner[second] is None:
                            owner[second] = i
                            held[i].append(second)
                            state[i] = EAT
                            timer[i] = rng.randint(2, 3)
                            meals[i] += 1
                            events.append(f'P{i + 1} picks up fork {second + 1} and eats')
                            progress = True
                        else:
                            events.append(f'P{i + 1} holds fork {first + 1}, waits for fork {second + 1}')
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

            deadlocked = (not progress) and all(s == HUNGRY for s in state) and \
                all(len(h) == 1 for h in held) and strategy != 'waiter'
            snapshots.append({
                'tick': tick,
                'philosophers': [{'id': i + 1, 'state': state[i], 'holding': [f + 1 for f in held[i]],
                                  'meals': meals[i]} for i in range(n)],
                'forks': [{'id': f + 1, 'owner': None if owner[f] is None else owner[f] + 1} for f in range(n)],
                'events': events,
                'deadlock': deadlocked,
            })
            if deadlocked:
                deadlock_at = tick
                break

        return {
            'success': True, 'simulation': 'philosophers', 'n': n, 'strategy': strategy, 'seed': seed,
            'steps': snapshots, 'deadlock': deadlock_at is not None, 'deadlockTick': deadlock_at,
            'meals': meals, 'totalMeals': sum(meals),
        }

    # ------------------------------------------------------------------ producer-consumer
    def producer_consumer(self, buffer_size: Any = 3, producers: Any = 1, consumers: Any = 1,
                          ticks: Any = 40, seed: Any = 1, synchronized: Any = True,
                          producer_period: Any = 1, consumer_period: Any = 2) -> Dict[str, Any]:
        """Bounded-buffer producer/consumer with counting semaphores.

        Semaphores: empty (starts at buffer_size), full (0). A producer does wait(empty),
        inserts, signal(full); a consumer does wait(full), removes, signal(empty).
        With synchronized=False the semaphores are ignored, so the buffer overflows and
        consumers read from an empty buffer.
        """
        size = require_int(buffer_size, 'buffer_size', 1, 20)
        n_prod = require_int(producers, 'producers', 1, 4)
        n_cons = require_int(consumers, 'consumers', 1, 4)
        ticks = require_int(ticks, 'ticks', 1, MAX_TICKS)
        seed = require_int(seed, 'seed', 0, 10_000_000)
        p_period = require_int(producer_period, 'producer_period', 1, 20)
        c_period = require_int(consumer_period, 'consumer_period', 1, 20)
        rng = random.Random(seed)

        count, empty, full = 0, size, 0
        produced = consumed = overflows = underflows = 0
        # each actor rests `period` ticks after acting, with a little seeded jitter
        cooldown = {('P', i): rng.randint(0, p_period) for i in range(n_prod)}
        cooldown.update({('C', i): rng.randint(0, c_period) for i in range(n_cons)})
        snapshots = []

        for tick in range(1, ticks + 1):
            events, blocked = [], []
            for kind, idx in sorted(cooldown):
                name = f'{kind}{idx + 1}'
                if cooldown[(kind, idx)] > 0:
                    cooldown[(kind, idx)] -= 1
                    continue
                period = p_period if kind == 'P' else c_period
                if kind == 'P':
                    if synchronized and empty == 0:
                        blocked.append(name)
                        events.append(f'{name} blocks on wait(empty): buffer is full')
                        continue
                    if synchronized:
                        empty -= 1
                        full += 1
                    count += 1
                    produced += 1
                    if count > size:
                        overflows += 1
                        events.append(f'{name} inserts an item: BUFFER OVERFLOW ({count}/{size})')
                    else:
                        events.append(f'{name} produces an item ({count}/{size})')
                else:
                    if synchronized and full == 0:
                        blocked.append(name)
                        events.append(f'{name} blocks on wait(full): buffer is empty')
                        continue
                    if synchronized:
                        full -= 1
                        empty += 1
                    if count == 0:
                        underflows += 1
                        events.append(f'{name} reads an empty buffer: UNDERFLOW')
                    else:
                        count -= 1
                        consumed += 1
                        events.append(f'{name} consumes an item ({count}/{size})')
                cooldown[(kind, idx)] = period - 1 + rng.randint(0, 1)
            snapshots.append({'tick': tick, 'buffer': count, 'empty': empty, 'full': full,
                              'blocked': blocked, 'events': events})

        return {
            'success': True, 'simulation': 'producer-consumer', 'bufferSize': size,
            'synchronized': bool(synchronized), 'producers': n_prod, 'consumers': n_cons,
            'steps': snapshots, 'produced': produced, 'consumed': consumed,
            'overflows': overflows, 'underflows': underflows,
        }

    # ------------------------------------------------------------------ race condition
    def race(self, threads: Any = 2, increments: Any = 5, use_lock: Any = False, seed: Any = 1) -> Dict[str, Any]:
        """Threads each run `counter += 1` `increments` times, interleaved by a seeded scheduler.

        Each increment is three instructions (load, add, store). Without a lock the
        scheduler can interleave them and updates get lost; with a lock the
        three instructions form a critical section and the result is exact.
        """
        threads = require_int(threads, 'threads', 2, 4)
        increments = require_int(increments, 'increments', 1, 20)
        seed = require_int(seed, 'seed', 0, 10_000_000)
        rng = random.Random(seed)

        counter = 0
        registers = [None] * threads
        pc = [0] * threads              # instruction index in the current increment: 0 load, 1 add, 2 store
        done = [0] * threads            # completed increments
        lock_owner = None
        steps = []

        while any(d < increments for d in done):
            runnable = [t for t in range(threads) if done[t] < increments
                        and not (use_lock and pc[t] == 0 and lock_owner not in (None, t))]
            if not runnable:  # cannot happen (owner always runnable) but stay safe
                break
            # a lock owner keeps being chosen only by chance: scheduling is still random
            t = rng.choice(runnable)
            note = ''
            if pc[t] == 0:
                if use_lock:
                    lock_owner = t
                    note = 'acquire lock, '
                registers[t] = counter
                op = f'load counter ({counter})'
            elif pc[t] == 1:
                registers[t] += 1
                op = f'add 1 (register = {registers[t]})'
            else:
                counter = registers[t]
                op = f'store counter = {counter}'
                if use_lock:
                    lock_owner = None
                    op += ', release lock'
                done[t] += 1
            pc[t] = (pc[t] + 1) % 3
            steps.append({'step': len(steps) + 1, 'thread': t + 1, 'op': note + op, 'counter': counter,
                          'registers': list(registers), 'lockOwner': None if lock_owner is None else lock_owner + 1})

        expected = threads * increments
        return {
            'success': True, 'simulation': 'race', 'threads': threads, 'increments': increments,
            'useLock': bool(use_lock), 'seed': seed, 'steps': steps,
            'final': counter, 'expected': expected, 'lostUpdates': expected - counter,
        }
