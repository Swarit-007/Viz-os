// viz/curve.js: a small line chart (Belady's anomaly: faults vs frames; working-set size vs time). Points appear up to the cursor.

import { svg } from '../dom.js';

const W = 760;
const H = 300;

// Line chart of one or more series against x. cursor = last x index revealed (-1 = none).
export function curve(res, cursor) {
    const { x: xs, series, xLabel, yLabel, mark = [] } = res.data;
    const padL = 48;
    const padB = 44;
    const padT = 16;
    const padR = 20;
    const yMax = Math.max(1, ...series.flatMap((s) => s.y));
    const nice = Math.ceil(yMax / 4) * 4 || 4;
    const px = (i) => padL + (xs.length === 1 ? 0.5 : i / (xs.length - 1)) * (W - padL - padR);
    const py = (v) => H - padB - (v / nice) * (H - padB - padT);
    const root = svg('svg', { class: 'fig curve', viewBox: `0 0 ${W} ${H}`, role: 'img', 'aria-label': `${yLabel} against ${xLabel}` });
    for (let g = 0; g <= 4; g++) {
        const v = (nice / 4) * g;
        root.append(svg('line', { class: 'grid-line', x1: padL, x2: W - padR, y1: py(v), y2: py(v) }), svg('text', { class: 'tick-label', x: padL - 8, y: py(v) + 4, 'text-anchor': 'end' }, v % 1 ? v.toFixed(1) : v));
    }
    const every = Math.max(1, Math.ceil(xs.length / 14));
    xs.forEach((v, i) => { if (i % every === 0) root.append(svg('text', { class: 'tick-label', x: px(i), y: H - padB + 18, 'text-anchor': 'middle' }, v)); });
    root.append(svg('text', { class: 'axis-title', x: (padL + W - padR) / 2, y: H - 6, 'text-anchor': 'middle' }, xLabel),
        svg('text', { class: 'axis-title', x: 12, y: (H - padB + padT) / 2, 'text-anchor': 'middle', transform: `rotate(-90 12 ${(H - padB + padT) / 2})` }, yLabel));
    series.forEach((s, k) => {
        const pts = s.y.map((v, i) => [px(i), py(v)]).slice(0, cursor + 1);
        if (pts.length > 1) root.append(svg('polyline', { class: `line line-${k} sketch`, points: pts.map((p) => p.join(',')).join(' ') }));
        pts.forEach(([cx, cy], i) => root.append(svg('circle', { class: `pt pt-${k} ${i === cursor ? 'pt-now' : ''}`, cx, cy, r: i === cursor ? 5 : 3.5 }, svg('title', null, `${s.label}: ${s.y[i]}`))));
        if (series.length > 1) root.append(svg('text', { class: `legend legend-${k}`, x: padL + 8 + k * 96, y: padT + 10 }, s.label));
    });
    mark.forEach((m) => { const i = xs.indexOf(m); if (i >= 0 && i <= cursor) root.append(svg('circle', { class: 'pt-anomaly', cx: px(i), cy: py(series[0].y[i]), r: 10 })); });
    return root;
}
