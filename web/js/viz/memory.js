// viz/memory.js: address-space bars. memory() shows buddy blocks or segments with an optional red marker for the current
// physical address; partitions() shows fixed blocks with the processes placed inside them.

import { h } from '../dom.js';
import { ink } from '../util.js';

// Address-space bar for buddy blocks and segments. cursor = snapshot index (-1 = initial).
export function memory(res, cursor) {
    const d = res.data;
    const snap = cursor < 0 ? { blocks: d.initial, mark: null } : d.snapshots[Math.min(cursor, d.snapshots.length - 1)];
    const bar = h('div', { class: 'mem-bar' }, snap.blocks.map((b) => h('div', { class: `mem-block mem-${b.kind}`, style: { flexGrow: b.size, flexBasis: 0, ...(b.label ? ink(b.label) : {}) },
        title: `${b.label || 'free'}: ${b.size} at ${b.start}${b.waste ? `, ${b.waste} wasted` : ''}` },
    h('span', { class: 'mem-name' }, b.label), h('span', { class: 'mem-size' }, b.size), b.waste ? h('i', { class: 'waste', style: { height: `${(b.waste / b.size) * 100}%` } }) : null)));
    const wrap = h('div', { class: 'mem-wrap' }, bar);
    if (snap.mark != null) wrap.append(h('div', { class: 'mem-mark', style: { left: `${(snap.mark / d.size) * 100}%` } }, h('span', null, snap.mark)));
    const ruler = h('div', { class: 'mem-ruler' }, [0, 0.25, 0.5, 0.75, 1].map((f) => h('span', { style: { left: `${f * 100}%` } }, Math.round(d.size * f))));
    return h('div', { class: 'fig memory' }, wrap, ruler,
        h('p', { class: 'legend-row' }, h('span', { class: 'lg lg-data' }, 'allocated'), h('span', { class: 'lg lg-free' }, 'free'), h('span', { class: 'lg lg-waste' }, 'wasted inside block')));
}

// Fixed partitions with the processes placed inside (memory-allocation fit strategies).
export function partitions(res, cursor) {
    const d = res.data;
    const snap = cursor < 0 ? { blocks: d.blocks.map((s) => ({ size: s, free: s, allocs: [] })), placed: null } : d.snapshots[Math.min(cursor, d.snapshots.length - 1)];
    const biggest = Math.max(...d.blocks);
    return h('div', { class: 'fig partitions' }, snap.blocks.map((b, i) => h('div', { class: `part-row ${snap.placed === i ? 'placed' : ''}` },
        h('span', { class: 'part-name' }, `Block ${i + 1}`, h('small', null, b.size)),
        h('div', { class: 'part-bar', style: { width: `${(b.size / biggest) * 100}%` } },
            b.allocs.map((a) => h('span', { class: 'part-seg', style: { ...ink(a.name), flexGrow: a.size }, title: `${a.name}: ${a.size}` }, a.name)),
            b.free > 0 ? h('span', { class: 'part-seg part-free', style: { flexGrow: b.free }, title: `free ${b.free}` }, b.free) : null))),
    h('p', { class: 'legend-row' }, h('span', { class: 'lg lg-data' }, 'process'), h('span', { class: 'lg lg-free' }, 'free space in the block')));
}
