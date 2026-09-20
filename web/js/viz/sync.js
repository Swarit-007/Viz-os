// viz/sync.js: figures for the synchronisation chapter: the dining table, the bounded buffer, the racing counter and the
// generic 'actors and shared variables' view used by readers-writers and Peterson's algorithm.

import { h, svg } from '../dom.js';
import { chip, ink } from '../util.js';

// Philosophers sit on a circle. A fork moves toward whoever holds it, so you can literally see who has what.
// A red philosopher means the deadlock snapshot.
export function philosophers(res, cursor) {
    const { n, snapshots } = res.data;
    const snap = snapshots[Math.max(cursor, 0)];
    const size = 380;
    const c = size / 2;
    const R = 138;
    const angle = (i) => -Math.PI / 2 + (i * 2 * Math.PI) / n;
    const at = (a, r) => [c + r * Math.cos(a), c + r * Math.sin(a)];
    const root = svg('svg', { class: 'fig table-fig', viewBox: `0 0 ${size} ${size}`, role: 'img', 'aria-label': 'Dining table' }, svg('circle', { class: 'table-top sketch', cx: c, cy: c, r: 98 }));
    snap.forks.forEach((f, k) => {
        const a = angle(k) - Math.PI / n;
        let [x1, y1] = at(a, 100);
        let [x2, y2] = at(a, 66);
        const owner = f.owner == null ? null : f.owner - 1;
        if (owner != null) {
            const [px, py] = at(angle(owner), R - 32);
            [x1, y1] = [x1 + (px - x1) * 0.55, y1 + (py - y1) * 0.55];
            [x2, y2] = [x2 + (px - x2) * 0.55, y2 + (py - y2) * 0.55];
        }
        root.append(svg('line', { class: `fork ${owner != null ? 'held' : ''} sketch`, x1, y1, x2, y2 }, svg('title', null, `Fork ${f.id}${owner != null ? ` held by P${owner + 1}` : ' is free'}`)));
    });
    snap.philosophers.forEach((p, i) => {
        const [x, y] = at(angle(i), R);
        root.append(svg('g', { class: `phil phil-${p.state} ${snap.deadlock ? 'phil-dead' : ''}` }, svg('circle', { class: 'sketch', cx: x, cy: y, r: 29 }),
            svg('text', { class: 'phil-name', x, y: y - 1, 'text-anchor': 'middle' }, `P${p.id}`),
            svg('text', { class: 'phil-state', x, y: y + 13, 'text-anchor': 'middle' }, p.state === 'hungry' && p.holding.length ? 'waiting' : p.state)));
    });
    return root;
}

export function buffer(res, cursor) {
    const d = res.data;
    const snap = d.snapshots[Math.max(cursor, 0)];
    const fill = cursor < 0 ? 0 : snap.buffer;
    const slots = h('div', { class: 'slots' }, Array.from({ length: Math.max(d.capacity, fill) }, (_, k) => h('span', { class: `slot ${k < fill ? 'full' : ''} ${k >= d.capacity ? 'over' : ''}` })));
    const W = 640;
    const H = 130;
    const top = Math.max(d.capacity, ...d.snapshots.map((s) => s.buffer));
    const px = (i) => 30 + (i / Math.max(d.snapshots.length - 1, 1)) * (W - 40);
    const py = (v) => H - 20 - (v / top) * (H - 36);
    const pts = d.snapshots.slice(0, Math.max(cursor + 1, 1)).map((s, i) => `${px(i)},${py(s.buffer)}`).join(' ');
    const chart = svg('svg', { class: 'fig level', viewBox: `0 0 ${W} ${H}`, role: 'img', 'aria-label': 'Buffer level over time' },
        svg('line', { class: 'cap-line', x1: 30, x2: W - 10, y1: py(d.capacity), y2: py(d.capacity) }), svg('text', { class: 'tick-label', x: 4, y: py(d.capacity) + 4 }, d.capacity),
        svg('text', { class: 'tick-label', x: 10, y: py(0) + 4 }, 0), svg('polyline', { class: 'line line-0 sketch', points: pts }));
    return h('div', { class: 'fig buffer-fig' }, slots,
        h('div', { class: 'sems' }, h('span', null, 'empty ', h('b', null, cursor < 0 ? d.capacity : snap.empty)), h('span', null, 'full ', h('b', null, cursor < 0 ? 0 : snap.full)),
            h('span', null, 'items ', h('b', null, `${fill}/${d.capacity}`)), snap.blocked?.length ? h('span', { class: 'blocked' }, 'blocked: ', snap.blocked.join(', ')) : null), chart);
}

// Shows the shared counter, each thread's private register, and the last few instructions, flagging lost updates.
export function race(res, cursor) {
    const d = res.data;
    const snap = cursor < 0 ? null : d.snapshots[Math.min(cursor, d.snapshots.length - 1)];
    const seen = d.snapshots.slice(Math.max(0, cursor - 6), cursor + 1);
    return h('div', { class: 'fig race-fig' },
        h('div', { class: 'counter' }, h('span', null, 'shared counter'), h('b', null, snap ? snap.counter : 0), h('small', null, `should end at ${d.expected}`)),
        h('div', { class: 'threads' }, Array.from({ length: d.threads }, (_, t) => h('div', { class: `thread ${snap && snap.thread === t + 1 ? 'active' : ''}` },
            h('span', null, chip(`T${t + 1}`)), h('small', null, 'register'), h('b', null, snap && snap.regs[t] != null ? snap.regs[t] : '-'), snap && snap.owner === t + 1 ? h('em', null, 'holds lock') : null))),
        h('ol', { class: 'recent' }, seen.map((s, i) => h('li', { class: `${s.lost ? 'lost' : ''} ${i === seen.length - 1 ? 'now' : ''}` }, chip(`T${s.thread}`), s.op, s.lost ? h('em', null, 'overwrote an update') : null))));
}

export function syncState(res, cursor) {
    const snap = res.data.snapshots[Math.max(cursor, 0)];
    return h('div', { class: `fig sync-fig ${snap.alert ? 'alert' : ''}` },
        h('div', { class: 'actors' }, snap.actors.map((a) => h('div', { class: `actor actor-${a.state.replace(/\s+/g, '-')}` }, chip(a.id), h('b', null, a.state), h('small', null, a.detail)))),
        h('dl', { class: 'vars' }, snap.vars.flatMap((v) => [h('dt', null, v.label), h('dd', null, String(v.value))])),
        snap.alert ? h('p', { class: 'stamp' }, 'both inside!') : null);
}
