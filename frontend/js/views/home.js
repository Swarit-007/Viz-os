import { diskPath, gantt, barChart, graph } from '../charts.js';
import { clear, h } from '../dom.js';
import { chip, procStyle } from '../ui.js';

// Sample data for the previews below. These render with the same chart code the tools use.
const RR = {
    totalTime: 12,
    processes: [
        ['P1', 0, 2], ['P2', 2, 2], ['P3', 4, 2], ['P1', 6, 2], ['P2', 8, 1], ['P3', 9, 2], ['P1', 11, 1],
    ].map(([name, startTime, duration]) => ({ name, startTime, duration })),
};
const DISK_PATH = [53, 65, 67, 37, 14, 98, 122, 124, 183];
const DISK = {
    disk_size: 200, path: DISK_PATH,
    steps: DISK_PATH.slice(1).map((to, i) => ({ from: DISK_PATH[i], to, distance: Math.abs(to - DISK_PATH[i]), jump: false, serviced: true })),
};

const previews = {
    cpu: () => gantt(RR),
    disk: () => diskPath(DISK).cloneNode(true),
    paging: () => {
        const rows = [[7, 7, 7, 2, 2, 2], [null, 0, 0, 0, 0, 3], [null, null, 1, 1, 1, 1]];
        const loaded = new Set(['0-0', '1-1', '2-2', '0-3', '1-5']);
        return h('table', { class: 'frames mini' }, h('tbody', null, rows.map((row, r) => h('tr', null,
            row.map((v, c) => h('td', { class: loaded.has(`${r}-${c}`) ? 'loaded' : '' }, v == null ? '' : v))))));
    },
    alloc: () => h('div', { class: 'mini-blocks' }, [[100, [['P3', 60]]], [500, [['P2', 417]]], [300, [['P1', 212]]]].map(([size, ps]) =>
        h('div', { class: 'block-bar', style: { width: `${(size / 500) * 100}%` } },
            ps.map(([id, n]) => h('span', { class: 'seg proc', style: { ...procStyle(id), flexGrow: n } }, id)),
            h('span', { class: 'seg free', style: { flexGrow: size - ps[0][1] } }, '')))),
    bankers: () => graph(
        [{ id: 'P1', label: 'P1', side: 'left' }, { id: 'P2', label: 'P2', side: 'left' }, { id: 'P3', label: 'P3', side: 'left' },
            { id: 'R1', label: 'R1', side: 'right', square: true }, { id: 'R2', label: 'R2', side: 'right', square: true }],
        [{ from: 'R1', to: 'P1' }, { from: 'R2', to: 'P2' }, { from: 'P1', to: 'R2', dashed: true }, { from: 'P3', to: 'R1', dashed: true }],
        { height: 200, layout: 'bipartite' }),
    deadlock: () => graph(
        [{ id: 0, label: 'P1', tone: 'bad' }, { id: 1, label: 'P2', tone: 'bad' }, { id: 2, label: 'P3', tone: 'bad' }],
        [{ from: 0, to: 1 }, { from: 1, to: 2 }, { from: 2, to: 0 }], { height: 200 }),
    compare: () => barChart([
        { label: 'FIFO', value: 15 }, { label: 'LRU', value: 12 }, { label: 'Optimal', value: 9, best: true },
    ]),
};
const LAYOUT = { cpu: 'span-7', disk: 'span-5', paging: 'span-5', alloc: 'span-7', bankers: 'span-6', deadlock: 'span-6', compare: 'span-12' };

function liveDemo() {
    const chartHost = h('div', { class: 'demo-chart' });
    const status = h('div', { class: 'demo-status' });
    let t = 0;
    const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
    const draw = () => {
        clear(chartHost).append(gantt(RR, { now: t }));
        const running = RR.processes.find((s) => s.startTime <= t && t < s.startTime + s.duration);
        clear(status).append(h('span', null, 'Round Robin, quantum 2'), h('span', null, `t = ${t}`),
            running ? h('span', null, 'running ', chip(running.name)) : h('span', null, 'finished'));
    };
    draw();
    if (!reduce) {
        setInterval(() => {
            if (document.hidden || !chartHost.isConnected || chartHost.closest('.panel')?.hidden) return;
            t = t >= RR.totalTime + 2 ? 0 : t + 1;
            draw();
        }, 520);
    } else { t = RR.totalTime; draw(); }
    return h('div', { class: 'demo' }, chartHost, status);
}

export default {
    id: 'home',
    title: 'Overview',
    group: null,
    blurb: '',
    mount(root, { views }) {
        const tools = views.filter((v) => v.group);
        root.append(
            h('section', { class: 'hero' },
                h('div', { class: 'hero-copy' },
                    h('h2', null, 'Watch the operating system decide.'),
                    h('p', null, 'Step through scheduling, paging, disk and deadlock algorithms with your own numbers.'),
                    h('div', { class: 'btn-row' },
                        h('a', { class: 'btn btn-primary', href: '#/cpu' }, 'Start with CPU scheduling'),
                        h('a', { class: 'btn btn-secondary', href: '#/compare' }, 'Compare algorithms'))),
                liveDemo()),
            h('section', { class: 'bento' }, tools.map((v) => h('a', { class: `tool ${LAYOUT[v.id] || ''}`, href: `#/${v.id}` },
                h('div', { class: 'thumb', 'aria-hidden': 'true' }, previews[v.id] ? previews[v.id]() : null),
                h('div', { class: 'tool-text' }, h('strong', null, v.title), h('span', null, v.blurb))))));
    },
};
