import { svg } from './dom.js';
import { procStyle } from './ui.js';

const W = 760;

// Gantt chart. `now` (optional) dims everything after that time and draws a playhead.
export function gantt(data, { now = null, compact = false } = {}) {
    const slices = data.processes;
    const total = Math.max(data.totalTime, 1);
    const padL = 12;
    const padR = 12;
    const unit = (W - padL - padR) / total;
    const barY = compact ? 4 : 14;
    const barH = compact ? 26 : 44;
    const height = compact ? 44 : 104;
    const root = svg('svg', {
        class: 'chart gantt', viewBox: `0 0 ${W} ${height}`, role: 'img',
        'aria-label': `Gantt chart, total time ${total}`, preserveAspectRatio: 'xMinYMin meet',
    });

    // idle gaps
    let cursor = 0;
    const gaps = [];
    for (const s of [...slices].sort((a, b) => a.startTime - b.startTime)) {
        if (s.startTime > cursor) gaps.push([cursor, s.startTime]);
        cursor = Math.max(cursor, s.startTime + s.duration);
    }
    for (const [a, b] of gaps) {
        root.append(svg('rect', { class: 'idle', x: padL + a * unit, y: barY, width: (b - a) * unit, height: barH, rx: 2 }));
    }

    for (const [index, s] of slices.entries()) {
        const x = padL + s.startTime * unit;
        const w = s.duration * unit;
        const dim = now != null && s.startTime >= now;
        const partial = now != null && s.startTime < now && s.startTime + s.duration > now;
        const g = svg('g', { class: `slice proc ${dim ? 'dim' : ''}`, style: { ...procStyle(s.name), '--i': index } },
            svg('title', null, `${s.name}: ${s.startTime} → ${s.startTime + s.duration}`),
            svg('rect', { x, y: barY, width: Math.max(w - 1, 1), height: barH, rx: 2, class: 'slice-rect' }));
        if (w > 18) {
            g.append(svg('text', { x: x + w / 2, y: barY + barH / 2 + 5, class: 'slice-label',
                'text-anchor': 'middle' }, s.name));
        }
        if (partial) g.setAttribute('class', 'slice proc partial');
        root.append(g);
    }

    if (!compact) {
        const ticks = new Set([0, total]);
        for (const s of slices) { ticks.add(s.startTime); ticks.add(s.startTime + s.duration); }
        let lastX = -100;
        for (const t of [...ticks].sort((a, b) => a - b)) {
            const x = padL + t * unit;
            root.append(svg('line', { class: 'tick', x1: x, x2: x, y1: barY + barH, y2: barY + barH + 8 }));
            if (x - lastX > 22 || t === total) {
                root.append(svg('text', { class: 'tick-label', x, y: barY + barH + 24, 'text-anchor': 'middle' }, t));
                lastX = x;
            }
        }
    }
    if (now != null) {
        const x = padL + now * unit;
        root.append(svg('line', { class: 'playhead', x1: x, x2: x, y1: 2, y2: height - 20 }));
    }
    return root;
}

// Horizontal bars for comparing one metric across algorithms.
export function barChart(items, { format = (v) => v, lowerIsBetter = true } = {}) {
    const rowH = 34;
    const labelW = 170;
    const barMax = W - labelW - 90;
    const max = Math.max(...items.map((i) => i.value), 1);
    const root = svg('svg', { class: 'chart bars', viewBox: `0 0 ${W} ${items.length * rowH + 6}`, role: 'img',
        'aria-label': lowerIsBetter ? 'Comparison, lower is better' : 'Comparison, higher is better' });
    items.forEach((item, i) => {
        const y = i * rowH + 4;
        const w = Math.max((item.value / max) * barMax, 2);
        root.append(
            svg('text', { class: 'bar-label', x: labelW - 12, y: y + 20, 'text-anchor': 'end' }, item.label),
            svg('rect', { class: `bar ${item.best ? 'bar-best' : ''}`, x: labelW, y, width: w, height: rowH - 10, rx: 2, style: { '--i': i } }),
            svg('text', { class: 'bar-value', x: labelW + w + 8, y: y + 20 }, format(item.value)),
        );
    });
    return root;
}

// Disk head movement: x = cylinder, y = step. Reveals path up to `upTo` steps.
export function diskPath(result, { upTo = result.steps.length } = {}) {
    const rowH = 34;
    const padT = 30;
    const padX = 34;
    const height = padT + (result.steps.length + 1) * rowH + 10;
    const size = result.disk_size - 1;
    const x = (c) => padX + (c / size) * (W - padX * 2);
    const y = (i) => padT + i * rowH;
    const root = svg('svg', { class: 'chart disk', viewBox: `0 0 ${W} ${height}`, role: 'img',
        'aria-label': `Head movement across ${result.disk_size} cylinders` });

    for (let i = 0; i <= 10; i++) {
        const c = Math.round((size * i) / 10);
        root.append(
            svg('line', { class: 'grid', x1: x(c), x2: x(c), y1: padT - 6, y2: height - 8 }),
            svg('text', { class: 'tick-label', x: x(c), y: 16, 'text-anchor': 'middle' }, c),
        );
    }
    const path = result.path;
    for (let i = 0; i < result.steps.length; i++) {
        if (i >= upTo) break;
        const s = result.steps[i];
        root.append(svg('line', {
            class: `seg ${s.jump ? 'seg-jump' : ''}`, x1: x(s.from), y1: y(i), x2: x(s.to), y2: y(i + 1),
        }));
    }
    path.forEach((c, i) => {
        if (i > upTo) return;
        const step = result.steps[i - 1];
        const serviced = i === 0 || step.serviced;
        root.append(
            svg('circle', { class: `dot ${i === 0 ? 'dot-head' : serviced ? 'dot-req' : 'dot-edge'} ${i === upTo ? 'dot-now' : ''}`,
                cx: x(c), cy: y(i), r: i === upTo ? 7 : 5 }, svg('title', null, `Step ${i}: cylinder ${c}`)),
            svg('text', { class: 'dot-label', x: x(c) + 10, y: y(i) + 4 }, c),
        );
    });
    return root;
}

// Circular graph with directed edges. nodes: [{id,label,tone}], edges: [{from,to,dashed,label}].
export function graph(nodes, edges, { height = 320, layout = 'circle', arrow = true } = {}) {
    const GW = 640;
    const cx = GW / 2;
    const cy = height / 2;
    const pos = new Map();
    if (layout === 'bipartite') {
        const left = nodes.filter((n) => n.side === 'left');
        const right = nodes.filter((n) => n.side === 'right');
        left.forEach((n, i) => pos.set(n.id, { x: GW * 0.28, y: ((i + 1) * height) / (left.length + 1) }));
        right.forEach((n, i) => pos.set(n.id, { x: GW * 0.72, y: ((i + 1) * height) / (right.length + 1) }));
    } else {
        const radius = Math.min(height / 2 - 44, 150);
        nodes.forEach((n, i) => {
            const a = (2 * Math.PI * i) / nodes.length - Math.PI / 2;
            pos.set(n.id, { x: cx + radius * Math.cos(a) * 1.7, y: cy + radius * Math.sin(a) });
        });
    }
    const root = svg('svg', { class: 'chart graph', viewBox: `0 0 ${GW} ${height}`, role: 'img' },
        svg('defs', null,
            svg('marker', { id: 'arrow', viewBox: '0 0 10 10', refX: 9, refY: 5, markerWidth: 7, markerHeight: 7,
                orient: 'auto-start-reverse' }, svg('path', { d: 'M0,0 L10,5 L0,10 z', class: 'arrow-head' }))));
    const r = 26;
    for (const e of edges) {
        const a = pos.get(e.from);
        const b = pos.get(e.to);
        if (!a || !b) continue;
        const dx = b.x - a.x;
        const dy = b.y - a.y;
        const len = Math.hypot(dx, dy) || 1;
        // curve edges slightly so opposite directions do not overlap
        const nx = -dy / len;
        const ny = dx / len;
        const bend = layout === 'circle' ? 26 : 0;
        const mx = (a.x + b.x) / 2 + nx * bend;
        const my = (a.y + b.y) / 2 + ny * bend;
        const sx = a.x + (mx - a.x) / (Math.hypot(mx - a.x, my - a.y) || 1) * r;
        const sy = a.y + (my - a.y) / (Math.hypot(mx - a.x, my - a.y) || 1) * r;
        const ex = b.x - (b.x - mx) / (Math.hypot(b.x - mx, b.y - my) || 1) * (r + 3);
        const ey = b.y - (b.y - my) / (Math.hypot(b.x - mx, b.y - my) || 1) * (r + 3);
        root.append(svg('path', {
            class: `edge ${e.dashed ? 'edge-dashed' : ''}`, d: `M${sx},${sy} Q${mx},${my} ${ex},${ey}`,
            'marker-end': arrow ? 'url(#arrow)' : null,
        }, e.label ? svg('title', null, e.label) : null));
        if (e.value != null) {
            root.append(svg('text', { class: 'edge-label', x: mx, y: my - 4, 'text-anchor': 'middle' }, e.value));
        }
    }
    for (const n of nodes) {
        const p = pos.get(n.id);
        const shape = n.square
            ? svg('rect', { x: p.x - r, y: p.y - r, width: r * 2, height: r * 2, rx: 6, class: 'node node-res' })
            : svg('circle', { cx: p.x, cy: p.y, r, class: `node ${n.tone === 'bad' ? 'node-bad' : 'node-proc'}` });
        root.append(shape, svg('text', { class: 'node-label', x: p.x, y: p.y + 5, 'text-anchor': 'middle' }, n.label));
    }
    return root;
}

// Swim-lane chart: one row per lane (queue level or CPU core). Slices are coloured by process.
export function lanes({ lanes: rows, totalTime, now = null }) {
    const labelW = 92;
    const padR = 14;
    const rowH = 40;
    const total = Math.max(totalTime, 1);
    const unit = (W - labelW - padR) / total;
    const height = rows.length * rowH + 34;
    const root = svg('svg', { class: 'chart lanes', viewBox: `0 0 ${W} ${height}`, role: 'img',
        'aria-label': `${rows.length} lanes over ${total} time units` });

    rows.forEach((row, r) => {
        const y = r * rowH + 4;
        root.append(
            svg('rect', { class: 'lane-bg', x: labelW, y, width: W - labelW - padR, height: rowH - 8, rx: 2 }),
            svg('text', { class: 'lane-label', x: labelW - 12, y: y + rowH / 2 + 1, 'text-anchor': 'end' }, row.label));
        row.slices.forEach((s) => {
            const x = labelW + s.startTime * unit;
            const w = Math.max(s.duration * unit - 1, 1);
            const dim = now != null && s.startTime >= now;
            const g = svg('g', { class: `slice proc ${dim ? 'dim' : ''}`, style: procStyle(s.name) },
                svg('title', null, `${s.name}: ${s.startTime} to ${s.startTime + s.duration}`),
                svg('rect', { class: 'slice-rect', x, y, width: w, height: rowH - 8, rx: 2 }));
            if (w > 16) g.append(svg('text', { class: 'slice-label', x: x + w / 2, y: y + rowH / 2 + 1, 'text-anchor': 'middle' }, s.name));
            root.append(g);
        });
    });

    const axisY = rows.length * rowH + 14;
    let lastX = -100;
    const step = total <= 30 ? 1 : total <= 80 ? 5 : 10;
    for (let t = 0; t <= total; t += step) {
        const x = labelW + t * unit;
        root.append(svg('line', { class: 'tick', x1: x, x2: x, y1: axisY - 8, y2: axisY - 3 }));
        if (x - lastX > 24) { root.append(svg('text', { class: 'tick-label', x, y: axisY + 10, 'text-anchor': 'middle' }, t)); lastX = x; }
    }
    if (now != null) {
        const x = labelW + now * unit;
        root.append(svg('line', { class: 'playhead', x1: x, x2: x, y1: 0, y2: rows.length * rowH }));
    }
    return root;
}
