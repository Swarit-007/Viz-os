import { post } from '../api.js';
import { lanes } from '../charts.js';
import { processError, processTable } from '../components.js';
import { clear, debounce, h } from '../dom.js';
import { PSEUDO, pseudocode } from '../pseudo.js';
import { randomProcesses } from '../random.js';
import { store } from '../store.js';
import { button, card, chip, field, metricTiles, notice, numberInput, player, segmented, table } from '../ui.js';

const POLICIES = [
    { value: 'fcfs', label: 'FCFS' }, { value: 'sjf', label: 'SJF' },
    { value: 'srtf', label: 'SRTF' }, { value: 'rr', label: 'Round Robin' },
];

export default {
    id: 'multicore',
    title: 'Multi-core Scheduling',
    group: 'Processes',
    blurb: 'One ready queue, several cores. See the speedup and idle time.',
    mount(root) {
        let cores = 2;
        let policy = 'fcfs';
        const errors = notice();
        const results = h('div', { class: 'results' });
        const editor = processTable({ priority: false, onChange: () => run() });
        const quantumInput = numberInput({ value: store.quantum, min: 1, label: 'Time quantum', onInput: (v) => { store.quantum = v; run(); } });
        const quantumField = field('Time quantum', quantumInput);

        const run = debounce(async () => {
            const bad = processError();
            if (bad) { errors.show(bad); return; }
            const body = { processes: store.processes, policy, time_quantum: store.quantum };
            try {
                const [data, single] = await Promise.all([
                    post('/api/scheduling/multicore', { ...body, cores }),
                    post('/api/scheduling/multicore', { ...body, cores: 1 }),
                ]);
                errors.hide();
                draw(data, single);
            } catch (e) { errors.show(e.message); }
        }, 200);

        function draw(data, single) {
            root.result = data;
            const m = data.metrics;
            const total = data.ganttChart.totalTime;
            const speedup = single.ganttChart.totalTime / total;
            const rows = data.coreLanes.map((slices, c) => ({ label: `Core ${c + 1}`, slices }));
            const chartHost = h('div', { class: 'chart-scroll' });
            const status = h('div', { class: 'now' });
            const code = pseudocode(PSEUDO.multicore.lines);
            const onFrame = (t) => {
                clear(chartHost).append(lanes({ lanes: rows, totalTime: total, now: t }));
                const running = data.coreLanes.map((sl, c) => [c, sl.find((s) => s.startTime <= t && t < s.startTime + s.duration)]);
                clear(status).append(h('span', null, `t = ${t}`), ...running.map(([c, s]) =>
                    h('span', null, `Core ${c + 1} `, s ? chip(s.name) : h('em', null, 'idle'))));
                const arriving = data.processResults.some((r) => r.arrivalTime === t);
                const finishing = data.processResults.some((r) => r.completionTime === t);
                const busy = running.some(([, s]) => s);
                code.set([...(arriving ? PSEUDO.multicore.roles.arrive : []), ...(busy ? [...PSEUDO.multicore.roles.select, ...PSEUDO.multicore.roles.run] : []),
                    ...(finishing ? PSEUDO.multicore.roles.finish : [])]);
            };
            const controls = player({ count: total, onFrame, interval: 420 });
            clear(results).append(
                metricTiles([
                    { label: 'Finish time', value: total, hint: `1 core: ${single.ganttChart.totalTime}` },
                    { label: 'Speedup vs 1 core', value: `${speedup.toFixed(2)}x`, tone: speedup > 1.05 ? 'good' : undefined },
                    { label: 'Avg waiting', value: m.avgWaitingTime.toFixed(2) },
                    { label: 'Core utilisation', value: `${(m.cpuUtilization * 100).toFixed(1)}%` },
                ]),
                h('div', { class: 'playback' },
                    card('Cores over time', [chartHost, status, controls]),
                    card('Pseudocode', code)),
                card('Load per core', h('div', { class: 'core-load' }, data.perCoreUtilization.map((u, c) => h('div', { class: 'load-row' },
                    h('span', null, `Core ${c + 1}`),
                    h('div', { class: 'load-track', role: 'img', 'aria-label': `${(u * 100).toFixed(0)} percent busy` }, h('div', { class: 'load-fill', style: { width: `${u * 100}%` } })),
                    h('b', null, `${(u * 100).toFixed(0)}%`))))),
                card('Per-process results', table(['Process', 'Arrival', 'Burst', 'Start', 'Finish', 'Turnaround', 'Waiting', 'Response'],
                    [...data.processResults].sort((a, b) => a.id.localeCompare(b.id, undefined, { numeric: true })).map((r) => [
                        chip(r.id), r.arrivalTime, r.burstTime, r.startTime, r.completionTime, r.turnaroundTime, r.waitingTime, r.responseTime]))));
        }

        function random() {
            store.processes = randomProcesses();
            cores = 2 + Math.floor(Math.random() * 3);
            corePicker.set(cores);
            editor.render(); run();
        }

        const corePicker = segmented([1, 2, 3, 4].map((n) => ({ value: n, label: `${n} ${n === 1 ? 'core' : 'cores'}` })), cores, (v) => { cores = v; run(); }, 'Number of cores');
        const policyPicker = segmented(POLICIES, policy, (v) => { policy = v; quantumField.hidden = v !== 'rr'; run(); }, 'Scheduling policy');
        quantumField.hidden = true;

        root.append(h('div', { class: 'split' },
            h('div', { class: 'controls' },
                card('Machine', [field('Cores', corePicker), field('Policy', policyPicker), quantumField]),
                card('Processes', [editor, h('div', { class: 'btn-row' }, editor.addButton,
                    button('Textbook example', () => {
                        store.processes = [{ id: 'P1', arrival: 0, burst: 8, priority: 3 }, { id: 'P2', arrival: 1, burst: 4, priority: 1 },
                            { id: 'P3', arrival: 2, burst: 9, priority: 4 }, { id: 'P4', arrival: 3, burst: 5, priority: 2 }];
                        editor.render(); run();
                    }, 'ghost'))]),
                errors),
            results));
        root.random = random;
        root.sync = () => { quantumInput.value = store.quantum; editor.render(); run(); };
        run();
    },
};
