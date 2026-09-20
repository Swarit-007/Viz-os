// viz/graph.js: directed graphs on a circle (resource-allocation graph, wait-for graph). Cycle nodes and edges turn red.

import { svg } from '../dom.js';

const W = 640;

// Directed graph on a circle (or bipartite when nodes have kind res). highlight = { path, cycle } node ids.
export function graphFig(graph, highlight = {}) {
    const nodes = graph.nodes;
    const H = Math.max(300, nodes.length > 8 ? 380 : 320);
    const pos = new Map();
    const R = Math.min(H / 2 - 44, 150);
    nodes.forEach((n, i) => {
        const a = (2 * Math.PI * i) / nodes.length - Math.PI / 2;
        pos.set(n.id, { x: W / 2 + R * Math.cos(a) * 1.6, y: H / 2 + R * Math.sin(a) });
    });
    const root = svg('svg', { class: 'fig graph', viewBox: `0 0 ${W} ${H}`, role: 'img', 'aria-label': 'Directed graph' },
        svg('defs', null, svg('marker', { id: 'arrowhead', viewBox: '0 0 10 10', refX: 9, refY: 5, markerWidth: 7, markerHeight: 7, orient: 'auto-start-reverse' }, svg('path', { d: 'M0,0 L10,5 L0,10 z', class: 'arrow-head' }))));
    const cyc = new Set(highlight.cycle || []);
    const onPath = new Set(highlight.path || []);
    const r = 24;
    for (const e of graph.edges) {
        const a = pos.get(e.from);
        const b = pos.get(e.to);
        if (!a || !b) continue;
        const dx = b.x - a.x;
        const dy = b.y - a.y;
        const len = Math.hypot(dx, dy) || 1;
        const bend = 24;
        const mx = (a.x + b.x) / 2 - (dy / len) * bend;
        const my = (a.y + b.y) / 2 + (dx / len) * bend;
        const d1 = Math.hypot(mx - a.x, my - a.y) || 1;
        const d2 = Math.hypot(b.x - mx, b.y - my) || 1;
        const hot = cyc.has(e.from) && cyc.has(e.to) && highlight.cycle;
        root.append(svg('path', { class: `edge sketch ${e.dashed ? 'edge-dashed' : ''} ${hot ? 'edge-hot' : ''}`, 'marker-end': 'url(#arrowhead)',
            d: `M${a.x + ((mx - a.x) / d1) * r},${a.y + ((my - a.y) / d1) * r} Q${mx},${my} ${b.x - ((b.x - mx) / d2) * (r + 4)},${b.y - ((b.y - my) / d2) * (r + 4)}` }));
    }
    for (const n of nodes) {
        const p = pos.get(n.id);
        const kind = n.kind || 'proc';
        const cls = `node node-${kind} ${cyc.has(n.id) ? 'node-hot' : ''} ${onPath.has(n.id) ? 'node-path' : ''}`;
        root.append(kind.startsWith('res') ? svg('rect', { class: `${cls} sketch`, x: p.x - r, y: p.y - r, width: r * 2, height: r * 2, rx: 4 }) : svg('circle', { class: `${cls} sketch`, cx: p.x, cy: p.y, r }),
            svg('text', { class: 'node-label', x: p.x, y: p.y + 1, 'text-anchor': 'middle' }, n.label));
    }
    return root;
}

export function graph(res, cursor) {
    const snap = res.data.snapshots[Math.max(cursor, 0)];
    return graphFig(res.data.graph, { path: snap.path, cycle: snap.cycle });
}
