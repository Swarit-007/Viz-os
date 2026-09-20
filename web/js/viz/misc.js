// viz/misc.js: two small one-off figures: the Unix inode levels and the fork() process tree.

import { h, svg } from '../dom.js';
import { ink } from '../util.js';

export function inode(res, cursor) {
    const d = res.data;
    const probe = d.probe;
    const shown = cursor < 0 ? [] : d.levels.map((l) => l);
    return h('div', { class: 'fig inode-fig' }, d.levels.map((l, i) => {
        const frac = l.capacity ? Math.min(1, l.used / l.capacity) : 0;
        const active = cursor >= 0 && shown.length && i <= probe.level && cursor >= d.levels.length + 0;
        return h('div', { class: `level ${l.used ? 'used' : ''} ${cursor >= 1 && probe.level === i && cursor >= 5 ? 'probe' : ''}` },
            h('span', { class: 'lv-name' }, l.name), h('div', { class: 'lv-bar' }, h('div', { class: 'lv-fill', style: { width: `${Math.max(frac * 100, l.used ? 2 : 0)}%` } })),
            h('span', { class: 'lv-num' }, `${l.used.toLocaleString()} of ${l.capacity.toLocaleString()} blocks`), active ? null : null);
    }), h('p', { class: 'hint' }, `One pointer block holds ${d.perBlock.toLocaleString()} pointers. Reading block ${probe.block.toLocaleString()} goes through the ${d.levels[probe.level].name.toLowerCase()} level: ${probe.reads} disk read(s).`));
}

// Fork tree: nodes laid out by depth. cursor = snapshot index (-1 = only the first process).
// Lay out the process tree: leaves get evenly spaced x positions and every parent is centred above its children.
export function tree(res, cursor) {
    const snaps = res.data.snapshots;
    const nodes = cursor < 0 ? [{ id: 'P0', parent: null, line: null, prints: 0 }] : snaps[Math.min(cursor, snaps.length - 1)];
    const kids = new Map();
    nodes.forEach((n) => { if (n.parent) (kids.get(n.parent) || kids.set(n.parent, []).get(n.parent)).push(n); });
    const pos = new Map();
    let leaf = 0;
    const place = (n, depth) => {
        const ch = kids.get(n.id) || [];
        if (!ch.length) { pos.set(n.id, { x: leaf++, y: depth }); return; }
        ch.forEach((c) => place(c, depth + 1));
        pos.set(n.id, { x: (pos.get(ch[0].id).x + pos.get(ch[ch.length - 1].id).x) / 2, y: depth });
    };
    place(nodes[0], 0);
    const maxDepth = Math.max(...[...pos.values()].map((p) => p.y));
    const W = Math.max(360, Math.max(leaf, 1) * 84);
    const H = 70 + maxDepth * 84;
    const px = (p) => 44 + p.x * ((W - 88) / Math.max(leaf - 1, 1));
    const py = (p) => 32 + p.y * 84;
    const root = svg('svg', { class: 'fig tree', viewBox: `0 0 ${W} ${H}`, role: 'img', 'aria-label': 'Process tree' });
    nodes.forEach((n) => {
        if (!n.parent) return;
        const a = pos.get(n.parent);
        const b = pos.get(n.id);
        root.append(svg('path', { class: 'edge sketch', d: `M${px(a)},${py(a) + 20} C${px(a)},${py(a) + 50} ${px(b)},${py(b) - 50} ${px(b)},${py(b) - 20}` }),
            svg('text', { class: 'edge-label', x: (px(a) + px(b)) / 2 + 6, y: (py(a) + py(b)) / 2 }, `line ${n.line}`));
    });
    nodes.forEach((n) => root.append(svg('g', { style: ink(n.id) }, svg('circle', { class: 'tree-node sketch', cx: px(pos.get(n.id)), cy: py(pos.get(n.id)), r: 20 }),
        svg('text', { class: 'node-label', x: px(pos.get(n.id)), y: py(pos.get(n.id)) + 1, 'text-anchor': 'middle' }, n.id))));
    return root;
}
