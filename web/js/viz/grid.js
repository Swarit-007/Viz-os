// viz/grid.js: a grid of blocks: file-system disks, RAID stripes and cache sets. Each snapshot is the whole grid after one step.
// Cell kinds (free, reserved, data, index, parity, mirror, lost) decide the styling; `owner` decides the highlighter colour.

import { h } from '../dom.js';
import { ink } from '../util.js';

// Rectangular block grid (disk blocks, RAID stripes, cache sets). cursor = snapshot index (-1 = start).
export function grid(res, cursor) {
    const d = res.data;
    const cells = cursor < 0 ? (d.start || d.snapshots[0].map((c) => ({ ...c, kind: 'free', label: '' }))) : d.snapshots[Math.min(cursor, d.snapshots.length - 1)];
    const cols = d.columns;
    const rows = Math.ceil(cells.length / cols);
    const body = h('div', { class: `block-grid ${d.colLabels ? 'labelled' : ''}`, style: { '--cols': cols } });
    if (d.colLabels) { body.append(h('span')); d.colLabels.forEach((l) => body.append(h('span', { class: 'bg-head' }, l))); }
    for (let r = 0; r < rows; r++) {
        if (d.rowLabels) body.append(h('span', { class: 'bg-head bg-row' }, d.rowLabels[r]));
        for (let c = 0; c < cols; c++) {
            const i = r * cols + c;
            const cell = cells[i];
            if (!cell) { body.append(h('span')); continue; }
            body.append(h('div', { class: `blk blk-${cell.kind}`, style: cell.owner ? ink(cell.owner) : null, title: `${d.colLabels ? '' : `Block ${i}: `}${cell.label || cell.kind}` },
                d.colLabels ? null : h('span', { class: 'blk-n' }, i), h('span', { class: 'blk-l' }, cell.label), cell.sub ? h('span', { class: 'blk-sub' }, cell.sub) : null));
        }
    }
    return h('div', { class: 'fig grid-fig' }, body,
        h('p', { class: 'legend-row' }, ...[['data', 'data'], ['index', 'index / newest'], ['parity', 'parity'], ['mirror', 'mirror'], ['free', 'free'], ['reserved', 'reserved']].map(([k, t]) => h('span', { class: `lg lg-${k}` }, t))));
}
