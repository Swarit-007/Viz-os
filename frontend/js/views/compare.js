import { post } from '../api.js';
import { barChart, gantt } from '../charts.js';
import { clear, debounce, h } from '../dom.js';
import { store } from '../store.js';
import { badge, card, metricTiles, notice, segmented, table } from '../ui.js';

const MODES = [
    { value: 'scheduling', label: 'CPU scheduling' },
    { value: 'page-replacement', label: 'Page replacement' },
    { value: 'disk', label: 'Disk scheduling' },
];
const SOURCE = {
    scheduling: 'the processes and quantum from CPU Scheduling',
    'page-replacement': 'the frames and reference string from Page Replacement',
    disk: 'the request queue, head and direction from Disk Scheduling',
};
const EDIT_VIEW = { scheduling: 'cpu', 'page-replacement': 'paging', disk: 'disk' };

const bestCell = (r, text) => h('span', null, text, r.isBest ? badge('best', 'good') : null);

export default {
    id: 'compare',
    title: 'Compare',
    group: 'Analysis',
    blurb: 'Run every algorithm on the same input and rank them.',
    mount(root) {
        let mode = 'scheduling';
        const errors = notice();
        const results = h('div', { class: 'results' });
        const source = h('p', { class: 'note' });

        const body = () => {
            if (mode === 'scheduling') return { processes: store.processes, time_quantum: store.quantum };
            if (mode === 'page-replacement') return { frames: store.frames, page_requests: store.pages };
            const d = store.disk;
            return { requests: d.requests, head: d.head, disk_size: d.size, direction: d.direction };
        };

        const run = debounce(async () => {
            try {
                const data = await post(`/api/compare/${mode}`, body());
                errors.hide();
                draw(data);
            } catch (e) { errors.show(e.message); }
        }, 100);

        function draw(data) {
            const best = data.best.join(' and ');
            const rows = data.results;
            clear(source).append(`Comparing on ${SOURCE[mode]}. `, h('a', { href: `#/${EDIT_VIEW[mode]}` }, 'Edit inputs →'));
            const rowClass = (r) => (r.isBest ? 'best' : '');

            if (mode === 'scheduling') {
                clear(results).append(
                    metricTiles([{ label: 'Lowest average waiting time', value: best, tone: 'good' }]),
                    card('Average waiting time', barChart(
                        rows.map((r) => ({ label: r.algorithm, value: r.avgWaitingTime, best: r.isBest })),
                        { format: (v) => v.toFixed(2) })),
                    card('All metrics', table(
                        ['Algorithm', 'Avg waiting', 'Avg turnaround', 'Avg response', 'CPU util.', 'Context switches'],
                        rows.map((r) => ({ className: rowClass(r), cells: [
                            bestCell(r, r.algorithm), r.avgWaitingTime, r.avgTurnaroundTime, r.avgResponseTime,
                            `${(r.cpuUtilization * 100).toFixed(1)}%`, r.contextSwitches] })))),
                    card('Timelines', h('div', { class: 'mini-gantts' }, rows.map((r) => h('div', { class: 'mini-gantt' },
                        h('span', { class: 'mini-label' }, r.algorithm), gantt(r.ganttChart, { compact: true }))))));
            } else if (mode === 'page-replacement') {
                clear(results).append(
                    metricTiles([{ label: 'Fewest page faults', value: best, tone: 'good' }]),
                    card('Page faults', barChart(rows.map((r) => ({ label: r.algorithm, value: r.faults, best: r.isBest })))),
                    card('All metrics', table(['Algorithm', 'Faults', 'Hits', 'Hit ratio'],
                        rows.map((r) => ({ className: rowClass(r), cells: [
                            bestCell(r, r.algorithm), r.faults, r.hits, `${(r.hitRatio * 100).toFixed(1)}%`] })))));
            } else {
                clear(results).append(
                    metricTiles([{ label: 'Least head movement', value: best, tone: 'good' }]),
                    card('Total head movement (cylinders)', barChart(
                        rows.map((r) => ({ label: r.algorithm, value: r.totalMovement, best: r.isBest })))),
                    card('All metrics', table(['Algorithm', 'Total movement', 'Average seek'],
                        rows.map((r) => ({ className: rowClass(r), cells: [
                            bestCell(r, r.algorithm), r.totalMovement, r.averageSeek] })))));
            }
        }

        const picker = segmented(MODES, mode, (v) => { mode = v; run(); }, 'Comparison type');
        root.append(h('div', { class: 'stack' }, card('Compare algorithms', [picker, source]), errors, results));
        root.refresh = run; // inputs may have changed in other views
        run();
    },
};
