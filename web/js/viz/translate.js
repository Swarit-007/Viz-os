// viz/translate.js: address translation figures. translate() walks one virtual address through TLB, page table and frame;
// multilevel() shows the outer index / inner index / offset split and which inner tables exist.

import { h } from '../dom.js';

const box = (label, value, cls = '') => h('div', { class: `flow-box ${cls}` }, h('small', null, label), h('b', null, value));

// Address translation with a TLB and page table. cursor = index of the current access (-1 = none yet).
export function translate(res, cursor) {
    const d = res.data;
    const acc = cursor < 0 ? null : d.accesses[Math.min(cursor, d.accesses.length - 1)];
    const table = acc?.tableAfter || d.initialTable;
    const tlb = acc ? acc.tlbAfter : [];
    const flow = acc ? h('div', { class: 'flow' },
        box('virtual address', acc.va), h('span', { class: 'flow-arrow' }), box('page', acc.page), box('offset', acc.offset),
        h('span', { class: 'flow-arrow' }), box('TLB', acc.invalid ? 'invalid' : acc.tlb, acc.tlb === 'hit' ? 'good' : acc.invalid ? 'bad' : 'warn'),
        acc.fault ? box('page table', 'page fault', 'bad') : null, h('span', { class: 'flow-arrow' }), box('frame', acc.frame ?? '-'),
        h('span', { class: 'flow-arrow' }), box('physical address', acc.pa ?? '-', 'strong')) : h('p', { class: 'hint' }, 'Press play to translate each address.');
    return h('div', { class: 'fig translate-fig' }, flow,
        h('div', { class: 'two' },
            h('div', null, h('div', { class: 'mx-title' }, `TLB (${d.tlbSize} entries)`), h('table', { class: 'mini' }, h('thead', null, h('tr', null, h('th', null, 'page'), h('th', null, 'frame'))),
                h('tbody', null, tlb.length ? tlb.map((e) => h('tr', { class: acc && e.page === acc.page ? 'focus' : '' }, h('td', null, e.page), h('td', null, e.frame))) : h('tr', null, h('td', { colspan: 2, class: 'empty' }, 'empty'))))),
            h('div', null, h('div', { class: 'mx-title' }, 'Page table'), h('table', { class: 'mini' }, h('thead', null, h('tr', null, h('th', null, 'page'), h('th', null, 'frame'))),
                h('tbody', null, table.map((f, p) => h('tr', { class: acc && acc.page === p ? 'focus' : '' }, h('td', null, p), h('td', null, f < 0 ? h('em', null, 'not in memory') : f))))))));
}

export function multilevel(res, cursor) {
    const d = res.data;
    const acc = cursor < 0 ? null : d.accesses[Math.min(cursor, d.accesses.length - 1)];
    const total = d.bitsOuter + d.bitsInner + d.bitsOffset;
    const bits = acc ? acc.va.toString(2).padStart(total, '0') : '0'.repeat(total);
    const part = (from, to, cls, label) => h('span', { class: `bits ${cls}` }, h('code', null, bits.slice(from, to)), h('small', null, label));
    const outer = Array.from({ length: d.outerSize }, (_, i) => i);
    const made = new Set(acc ? acc.innerTables : []);
    return h('div', { class: 'fig multilevel-fig' },
        h('div', { class: 'addr' }, part(0, d.bitsOuter, 'b-outer', `outer ${acc ? acc.outer : '-'}`), part(d.bitsOuter, d.bitsOuter + d.bitsInner, 'b-inner', `inner ${acc ? acc.inner : '-'}`),
            part(d.bitsOuter + d.bitsInner, total, 'b-off', `offset ${acc ? acc.offset : '-'}`)),
        h('div', { class: 'outer-table' }, outer.map((i) => h('span', { class: `cell ${made.has(i) ? 'used' : ''} ${acc && acc.outer === i ? 'now' : ''}`, title: made.has(i) ? `Inner table ${i} allocated` : 'no inner table' }, i))),
        h('p', { class: 'hint' }, acc ? acc.note : 'Press play to walk the tables.'),
        acc ? h('div', { class: 'flow' }, box('outer index', acc.outer), h('span', { class: 'flow-arrow' }), box('inner index', acc.inner), h('span', { class: 'flow-arrow' }), box('frame', acc.frame),
            h('span', { class: 'flow-arrow' }), box('physical address', `0x${acc.pa.toString(16).toUpperCase()}`, 'strong')) : null);
}
