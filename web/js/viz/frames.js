// viz/frames.js: the page-replacement table. Columns are requests, rows are physical frames.
// A yellow cell is the page just loaded, green/red headers mark hits and faults, and Clock shows its hand and reference bits.

import { h } from '../dom.js';

// Page-replacement table: one column per request, one row per frame. cursor = last request shown.
export function frames(res, cursor) {
    const { frames: n, steps, clock } = res.data;
    const head = h('tr', null, h('th', { class: 'corner' }, 'Request'), steps.map((s, i) => h('th', { class: i <= cursor ? (s.hit ? 'hit' : 'fault') : 'future' }, s.page)));
    const rows = [];
    for (let f = 0; f < n; f++) {
        rows.push(h('tr', null, h('th', { class: 'row-head' }, `Frame ${f + 1}`), steps.map((s, i) => {
            if (i > cursor) return h('td', { class: 'future' });
            const value = s.slots[f];
            const loaded = !s.hit && s.slot === f;
            return h('td', { class: `${loaded ? 'loaded' : ''} ${s.hit && s.slot === f ? 'touched' : ''}` }, value == null ? '' : value,
                clock && s.hand === f ? h('i', { class: 'hand', title: 'clock hand' }) : null,
                clock && value != null ? h('sub', { class: 'refbit', title: 'reference bit' }, s.refbits[f]) : null);
        })));
    }
    rows.push(h('tr', { class: 'outcome' }, h('th', { class: 'row-head' }, 'Result'), steps.map((s, i) => h('td', { class: i <= cursor ? (s.hit ? 'hit' : 'fault') : 'future' }, i <= cursor ? (s.hit ? 'hit' : 'fault') : ''))));
    const shown = steps.slice(0, cursor + 1);
    return h('div', { class: 'fig frames-wrap' }, h('table', { class: 'frames' }, h('thead', null, head), h('tbody', null, rows)),
        h('p', { class: 'tally' }, `${shown.filter((s) => !s.hit).length} faults, ${shown.filter((s) => s.hit).length} hits so far`));
}
