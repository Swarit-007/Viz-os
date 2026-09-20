// viz/banker.js: Banker's algorithm and deadlock detection. Shows the matrices with the process being examined highlighted
// (green = can finish, red = must wait), the work vector, and which processes have finished.

import { h } from '../dom.js';
import { graphFig } from './graph.js';
import { chip } from '../util.js';

const vec = (v) => `[${v.join(', ')}]`;

// Banker's / detection state: matrices with the process under test highlighted, work vector, finished flags.
export function banker(res, cursor) {
    const d = res.data;
    const snap = d.snapshots[Math.max(cursor, 0)];
    const reqMode = d.mode === 'request';
    const matrix = (title, rows, kind) => h('div', { class: 'mx' }, h('div', { class: 'mx-title' }, title),
        h('table', null, h('thead', null, h('tr', null, h('th'), Array.from({ length: d.m }, (_, j) => h('th', null, `R${j + 1}`)))),
            h('tbody', null, rows.map((row, i) => h('tr', { class: `${snap.focus === i ? `focus ${snap.verdict || ''}` : ''} ${snap.finish[i] ? 'finished' : ''}` },
                h('th', null, chip(`P${i + 1}`)), row.map((v) => h('td', null, v)))))));
    const hasMax = !reqMode;
    return h('div', { class: 'fig banker-fig' },
        h('div', { class: 'mxs' }, matrix('Allocation', d.allocation), hasMax ? matrix('Max', d.max) : null, matrix(reqMode ? 'Request' : 'Need (Max - Allocation)', d.need)),
        h('div', { class: 'work' }, h('span', null, 'Work'), h('b', null, vec(snap.work)), h('span', { class: 'work-label' }, 'Finished'),
            h('div', { class: 'flags' }, snap.finish.map((f, i) => h('span', { class: `flag ${f ? 'on' : ''}` }, `P${i + 1}`))),
            snap.order.length ? h('span', { class: 'order' }, 'order: ', snap.order.join(' -> ')) : null),
        d.graph && cursor === d.snapshots.length - 1 ? h('div', { class: 'sub-fig' }, h('div', { class: 'mx-title' }, 'Wait-for graph (Pi -> Pj: Pi waits on a resource Pj holds)'), graphFig(d.graph, {})) : null);
}
