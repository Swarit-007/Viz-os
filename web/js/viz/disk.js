// viz/disk.js: disk-head movement. x = cylinder number, y = time (one row per seek). Dashed red lines are return jumps.

import { svg } from '../dom.js';

const W = 760;

// Head movement: x = cylinder, y = step. cursor = index of the last step drawn (-1 = none).
export function disk(res, cursor) {
    const { size, head, steps } = res.data;
    const rowH = 34;
    const padT = 34;
    const padX = 30;
    const height = padT + (steps.length + 1) * rowH + 12;
    const last = size - 1;
    const x = (c) => padX + (c / last) * (W - padX * 2);
    const y = (i) => padT + i * rowH;
    const root = svg('svg', { class: 'fig disk', viewBox: `0 0 ${W} ${height}`, role: 'img', 'aria-label': `Disk head movement over ${size} cylinders` });
    for (let i = 0; i <= 10; i++) {
        const c = Math.round((last * i) / 10);
        root.append(svg('line', { class: 'grid-line', x1: x(c), x2: x(c), y1: padT - 8, y2: height - 8 }), svg('text', { class: 'tick-label', x: x(c), y: 18, 'text-anchor': 'middle' }, c));
    }
    steps.forEach((s, i) => {
        if (i > cursor) return;
        root.append(svg('line', { class: `seek sketch ${s.jump ? 'seek-jump' : ''} ${i === cursor ? 'seek-now' : ''}`, x1: x(s.from), y1: y(i), x2: x(s.to), y2: y(i + 1) }));
    });
    const path = [head, ...steps.map((s) => s.to)];
    path.forEach((c, i) => {
        if (i > cursor + 1) return;
        const s = steps[i - 1];
        const kind = i === 0 ? 'start' : s.jump ? 'jump' : s.edge ? 'edge' : 'req';
        root.append(svg('circle', { class: `dot dot-${kind} ${i === cursor + 1 ? 'dot-now' : ''}`, cx: x(c), cy: y(i), r: i === cursor + 1 ? 7 : 5 }, svg('title', null, `Cylinder ${c}`)),
            svg('text', { class: 'dot-label', x: x(c) + 10, y: y(i) + 4 }, c));
    });
    return root;
}
