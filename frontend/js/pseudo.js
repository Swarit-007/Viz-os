import { h } from './dom.js';

// Pseudocode with per-role line numbers. `roles` maps an event name to the lines to highlight.
export const PSEUDO = {
    fcfs: {
        lines: ['queue = processes sorted by arrival time', 'while queue is not empty:', '    p = first process in queue',
            '    if p has not arrived yet: CPU idles until it does', '    run p to completion',
            '    record start, finish and waiting = start - arrival'],
        roles: { select: [2], idle: [3], run: [4], finish: [5] },
    },
    sjf: {
        lines: ['while any process is unfinished:', '    ready = arrived processes not yet run',
            '    if ready is empty: CPU idles until the next arrival', '    p = process in ready with the shortest burst',
            '    run p to completion', '    record start, finish and waiting'],
        roles: { select: [1, 3], idle: [2], run: [4], finish: [5] },
    },
    priority: {
        lines: ['while any process is unfinished:', '    ready = arrived processes not yet run',
            '    if ready is empty: CPU idles until the next arrival', '    p = process in ready with the lowest priority number',
            '    run p to completion', '    record start, finish and waiting'],
        roles: { select: [1, 3], idle: [2], run: [4], finish: [5] },
    },
    srtf: {
        lines: ['at every arrival and completion:', '    ready = arrived processes with time left',
            '    p = process in ready with the least remaining time', '    if p differs from the running process: preempt it',
            '    run p until the next arrival or until it finishes', '    if p is finished: record finish and waiting'],
        roles: { select: [1, 2], preempt: [3], run: [4], idle: [1], finish: [5] },
    },
    'priority-preemptive': {
        lines: ['at every arrival and completion:', '    ready = arrived processes with time left',
            '    p = process in ready with the lowest priority number', '    if p differs from the running process: preempt it',
            '    run p until the next arrival or until it finishes', '    if p is finished: record finish and waiting'],
        roles: { select: [1, 2], preempt: [3], run: [4], idle: [1], finish: [5] },
    },
    roundrobin: {
        lines: ['queue = arrived processes in arrival order', 'while queue is not empty:', '    p = dequeue()',
            '    run p for min(quantum, p.remaining)', '    enqueue processes that arrived meanwhile',
            '    if p.remaining > 0: enqueue(p)', '    else: record finish and waiting'],
        roles: { select: [2], run: [3], idle: [1], preempt: [4, 5], finish: [4, 6] },
    },
    mlfq: {
        lines: ['every tick:', '    new arrivals join queue 1', '    if a process waited >= aging in a lower queue: promote it',
            '    if a higher queue is non-empty: preempt the running process',
            '    run the head of the highest non-empty queue for one tick', '    if it finished: record completion',
            '    else if it used its whole quantum: demote it one queue'],
        roles: { arrive: [1], promote: [2], preempt: [3], run: [4], finish: [5], demote: [6], requeue: [6] },
    },
    multicore: {
        lines: ['every tick:', '    add new arrivals to the shared ready queue', '    for each idle core:',
            '        take the next process by policy (FCFS order, shortest job, ...)',
            '    every busy core runs its process for one tick', '    finished processes free their core'],
        roles: { arrive: [1], select: [2, 3], run: [4], finish: [5] },
    },
    disk: {
        fcfs: {
            lines: ['for each request in arrival order:', '    move the head to the request', '    service the request'],
            roles: { move: [1], serviced: [2] },
        },
        sstf: {
            lines: ['while requests are pending:', '    next = pending request closest to the head', '    move the head to next',
                '    service next and remove it'],
            roles: { move: [2], serviced: [3], select: [1] },
        },
        scan: {
            lines: ['sweep the head in the chosen direction', '    service every request it passes',
                'at the disk edge: reverse direction', 'repeat until no requests remain'],
            roles: { move: [0], serviced: [1], edge: [2] },
        },
        cscan: {
            lines: ['sweep the head in the chosen direction', '    service every request it passes',
                'at the disk edge: jump back to the opposite edge', 'repeat the sweep until no requests remain'],
            roles: { move: [0], serviced: [1], edge: [2], jump: [2] },
        },
        look: {
            lines: ['sweep the head in the chosen direction', '    service every request it passes',
                'after the last request in this direction: reverse', 'repeat until no requests remain'],
            roles: { move: [0], serviced: [1], edge: [2] },
        },
        clook: {
            lines: ['sweep the head in the chosen direction', '    service every request it passes',
                'after the last request: jump to the farthest waiting request', 'repeat until no requests remain'],
            roles: { move: [0], serviced: [1], jump: [2] },
        },
    },
    paging: {
        common: ['for each page request:', '    if the page is in a frame: HIT', '    else: PAGE FAULT',
            '        if a frame is free: use it', '        else: evict a victim page', '        load the page into the frame'],
        victim: {
            fifo: 'evict the page that has been resident longest',
            lru: 'evict the page unused for the longest time',
            optimal: 'evict the page whose next use is farthest away',
            clock: 'sweep the hand: clear reference bits until one is 0, evict it',
        },
        hit: { fifo: '', lru: ' (and mark it most recently used)', optimal: '', clock: ' (and set its reference bit)' },
    },
};

// Pseudocode panel. `set(lines)` highlights zero-based line indexes.
export function pseudocode(lines) {
    const rows = lines.map((text, i) => h('li', { 'data-line': i },
        h('code', null, text.replace(/^ +/, (m) => ' '.repeat(m.length)))));
    const el = h('ol', { class: 'pseudo', 'aria-label': 'Pseudocode' }, rows);
    el.set = (active = []) => {
        const on = new Set(active);
        rows.forEach((row, i) => {
            row.classList.toggle('on', on.has(i));
            if (on.has(i)) row.setAttribute('aria-current', 'step'); else row.removeAttribute('aria-current');
        });
    };
    el.replace = (next) => {
        el.replaceChildren(...next.map((text, i) => h('li', { 'data-line': i },
            h('code', null, text.replace(/^ +/, (m) => ' '.repeat(m.length))))));
    };
    return el;
}
