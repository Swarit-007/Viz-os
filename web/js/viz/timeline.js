// viz/timeline.js: Gantt-style swim lanes. One lane per CPU, core, queue or real-time task.
// Slices come from result.data.lanes; markers (arrivals, releases, deadlines, misses) from result.data.marks.

import { svg } from '../dom.js';
import { ink } from '../util.js';

const W = 760;

// Swim-lane timeline: one row per CPU / core / queue / task. cursor = time (slices after it are faded).
// Slices that start after `cursor` are faded, the slice under the cursor is outlined, and a dashed playhead marks the time.
export function timeline(res, cursor) {
    const { lanes, total, marks = [] } = res.data;
    const T = Math.max(total, 1);
    const labelW = lanes.length > 1 || lanes[0].label !== 'CPU' ? 96 : 44;
    const padR = 16;
    const rowH = lanes.length > 1 ? 40 : 54;
    const top = 18;
    const unit = (W - labelW - padR) / T;
    const height = top + lanes.length * rowH + 44;
    const root = svg('svg', { class: 'fig timeline', viewBox: `0 0 ${W} ${height}`, role: 'img', 'aria-label': `Timeline of ${lanes.length} lane(s) over ${T} time units` });
    const x = (t) => labelW + t * unit;

    lanes.forEach((lane, r) => {
        const y = top + r * rowH;
        root.append(svg('line', { class: 'lane-rule', x1: labelW, x2: W - padR, y1: y + rowH - 3, y2: y + rowH - 3 }),
            svg('text', { class: 'lane-label', x: labelW - 10, y: y + rowH / 2, 'text-anchor': 'end' }, lane.label));
        for (const s of lane.slices) {
            const dim = s.start >= cursor;
            const live = s.start < cursor && s.start + s.dur > cursor;
            const g = svg('g', { class: `slice ${dim ? 'dim' : ''} ${live ? 'live' : ''}`, style: ink(s.name) },
                svg('title', null, `${s.name}: ${s.start} to ${s.start + s.dur}`),
                svg('rect', { class: 'slice-rect sketch', x: x(s.start), y: y + 5, width: Math.max(s.dur * unit - 2, 2), height: rowH - 14, rx: 3 }));
            if (s.dur * unit > 20) g.append(svg('text', { class: 'slice-label', x: x(s.start + s.dur / 2), y: y + rowH / 2 - 1, 'text-anchor': 'middle' }, s.name));
            root.append(g);
        }
    });

    // Markers: arrivals sit on the time axis; task releases (up arrow), deadlines (down arrow) and misses (red cross) sit on the task's own lane.
    // markers: arrivals sit on the axis; task releases / deadlines / misses sit on their own lane
    const axisY = top + lanes.length * rowH + 8;
    for (const m of marks) {
        const laneIdx = lanes.findIndex((l) => l.label === m.name);
        const faded = m.t > cursor ? 'faded' : '';
        if (m.kind === 'arrive') {
            root.append(svg('path', { class: `mark-arrive ${faded}`, d: `M${x(m.t)},${axisY - 4} l-4,8 h8 z`, style: ink(m.name) }, svg('title', null, `${m.name} arrives at ${m.t}`)));
        } else if (laneIdx >= 0) {
            const y = top + laneIdx * rowH;
            if (m.kind === 'release') root.append(svg('path', { class: `mark-release ${faded}`, d: `M${x(m.t)},${y + rowH - 4} v-${rowH - 12} m-3,5 l3,-5 l3,5` }, svg('title', null, `${m.name} released at ${m.t}`)));
            else if (m.kind === 'deadline') root.append(svg('path', { class: `mark-deadline ${faded}`, d: `M${x(m.t)},${y + 2} v${rowH - 12} m-3,-5 l3,5 l3,-5` }, svg('title', null, `${m.name} deadline ${m.t}`)));
            else root.append(svg('g', { class: `mark-miss ${faded}` }, svg('path', { d: `M${x(m.t) - 5},${y + 6} l10,10 m0,-10 l-10,10` }), svg('title', null, `${m.name} missed its deadline at ${m.t}`)));
        }
    }

    const step = T <= 30 ? 1 : T <= 80 ? 5 : T <= 200 ? 10 : 50;
    let lastX = -100;
    for (let t = 0; t <= T; t += step) {
        root.append(svg('line', { class: 'tick', x1: x(t), x2: x(t), y1: axisY - 10, y2: axisY - 6 }));
        if (x(t) - lastX > 22) { root.append(svg('text', { class: 'tick-label', x: x(t), y: axisY + 20, 'text-anchor': 'middle' }, t)); lastX = x(t); }
    }
    root.append(svg('line', { class: 'axis sketch', x1: labelW, x2: W - padR, y1: axisY - 10, y2: axisY - 10 }));
    if (cursor > 0 && cursor <= T) root.append(svg('line', { class: 'playhead', x1: x(cursor), x2: x(cursor), y1: top - 8, y2: axisY - 10 }));
    return root;
}
