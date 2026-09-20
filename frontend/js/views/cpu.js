import { post } from '../api.js';
import { gantt } from '../charts.js';
import { clear, debounce, h } from '../dom.js';
import { randomProcesses } from '../random.js';
import { store } from '../store.js';
import { button, card, chip, field, metricTiles, notice, numberInput, player, segmented, table } from '../ui.js';

const ALGORITHMS = [
    { value: 'fcfs', label: 'FCFS', title: 'First Come First Serve' },
    { value: 'sjf', label: 'SJF', title: 'Shortest Job First (non-preemptive)' },
    { value: 'srtf', label: 'SRTF', title: 'Shortest Remaining Time First (preemptive SJF)' },
    { value: 'priority', label: 'Priority', title: 'Priority, non-preemptive' },
    { value: 'priority-preemptive', label: 'Priority (P)', title: 'Priority, preemptive' },
    { value: 'roundrobin', label: 'Round Robin', title: 'Round Robin' },
];
const NOTES = {
    fcfs: 'Runs processes strictly in arrival order. Simple, but a long job delays everything behind it (the convoy effect).',
    sjf: 'Picks the ready process with the shortest burst. Minimises average waiting time among non-preemptive schedulers, but can starve long jobs.',
    srtf: 'Preemptive SJF: whenever a process arrives, the one with the least remaining time runs. Optimal for average waiting time.',
    priority: 'Runs the ready process with the smallest priority number (highest priority). Low-priority processes can starve without aging.',
    'priority-preemptive': 'A newly arrived higher-priority process immediately preempts the running one.',
    roundrobin: 'Each process gets at most one quantum before going to the back of the queue. Fair, with response time bounded by quantum × queue length.',
};

export default {
    id: 'cpu',
    title: 'CPU Scheduling',
    group: 'Processes',
    blurb: 'FCFS, SJF, SRTF, Priority and Round Robin with Gantt playback.',
    mount(root) {
        let algorithm = 'srtf';
        const uses = () => ({ priority: algorithm.startsWith('priority'), quantum: algorithm === 'roundrobin' });
        const errors = notice();
        const results = h('div', { class: 'results' });
        const rowsEl = h('div', { class: 'proc-rows' });
        const quantumInput = numberInput({
            value: store.quantum, min: 1, label: 'Time quantum',
            onInput: (v) => { store.quantum = v; run(); },
        });
        const quantumField = field('Time quantum', quantumInput);
        const note = h('p', { class: 'note' });

        const renumber = () => store.processes.forEach((p, i) => { p.id = `P${i + 1}`; });

        function renderRows() {
            clear(rowsEl);
            rowsEl.append(h('div', { class: 'proc-row proc-head' },
                ...['Process', 'Arrival', 'Burst', 'Priority', ''].map((t) => h('span', null, t))));
            store.processes.forEach((p, i) => {
                rowsEl.append(h('div', { class: 'proc-row' },
                    chip(p.id),
                    numberInput({ value: p.arrival, min: 0, label: `${p.id} arrival`, onInput: (v) => { p.arrival = v; run(); } }),
                    numberInput({ value: p.burst, min: 1, label: `${p.id} burst`, onInput: (v) => { p.burst = v; run(); } }),
                    numberInput({ value: p.priority, label: `${p.id} priority`, onInput: (v) => { p.priority = v; run(); } }),
                    h('button', {
                        type: 'button', class: 'icon-btn', 'aria-label': `Remove ${p.id}`, title: 'Remove',
                        disabled: store.processes.length === 1,
                        onClick: () => { store.processes.splice(i, 1); renumber(); renderRows(); run(); },
                    }, '×')));
            });
            rowsEl.classList.toggle('no-priority', !uses().priority);
        }

        function preset() {
            store.processes = [
                { id: 'P1', arrival: 0, burst: 8, priority: 3 }, { id: 'P2', arrival: 1, burst: 4, priority: 1 },
                { id: 'P3', arrival: 2, burst: 9, priority: 4 }, { id: 'P4', arrival: 3, burst: 5, priority: 2 },
            ];
            renderRows(); run();
        }
        function random() {
            store.processes = randomProcesses();
            store.quantum = 2 + Math.floor(Math.random() * 3);
            quantumInput.value = store.quantum;
            renderRows(); run();
        }

        const run = debounce(async () => {
            const bad = store.processes.some((p) => !Number.isInteger(p.arrival) || p.arrival < 0
                || !Number.isInteger(p.burst) || p.burst < 1 || !Number.isInteger(p.priority));
            if (bad) { errors.show('Arrival must be ≥ 0, burst ≥ 1, priority a whole number.'); return; }
            if (uses().quantum && !(store.quantum >= 1)) { errors.show('Time quantum must be at least 1.'); return; }
            try {
                const data = await post(`/api/scheduling/${algorithm}`, {
                    processes: store.processes, time_quantum: store.quantum,
                });
                errors.hide();
                draw(data);
            } catch (e) { errors.show(e.message); }
        }, 200);

        function draw(data) {
            root.result = data;
            const m = data.metrics;
            const total = data.ganttChart.totalTime;
            const chartHost = h('div', { class: 'chart-scroll' });
            const status = h('div', { class: 'now' });
            const slices = data.ganttChart.processes;
            const rows = data.processResults;

            const onFrame = (t) => {
                clear(chartHost).append(gantt(data.ganttChart, { now: t }));
                const running = slices.find((s) => s.startTime <= t && t < s.startTime + s.duration);
                const waiting = rows.filter((r) => r.arrivalTime <= t && r.completionTime > t
                    && (!running || r.id !== running.name));
                const done = rows.filter((r) => r.completionTime <= t);
                clear(status).append(
                    h('span', null, `t = ${t}`),
                    h('span', null, 'Running: ', running ? chip(running.name) : h('em', null, t >= total ? 'finished' : 'idle')),
                    h('span', null, 'Waiting: ', waiting.length ? waiting.map((r) => chip(r.id)) : h('em', null, 'none')),
                    h('span', null, 'Done: ', done.length ? done.map((r) => chip(r.id)) : h('em', null, 'none')));
            };
            const controls = player({ count: total, onFrame, interval: 450 });

            clear(results).append(
                metricTiles([
                    { label: 'Avg waiting time', value: m.avgWaitingTime.toFixed(2) },
                    { label: 'Avg turnaround', value: m.avgTurnaroundTime.toFixed(2) },
                    { label: 'Avg response', value: m.avgResponseTime.toFixed(2) },
                    { label: 'CPU utilisation', value: `${(m.cpuUtilization * 100).toFixed(1)}%` },
                ]),
                card('Gantt chart', [chartHost, status, controls]),
                card('Per-process results', table(
                    ['Process', 'Arrival', 'Burst', ...(data.processResults[0].priority != null ? ['Priority'] : []),
                        'Start', 'Finish', 'Turnaround', 'Waiting', 'Response'],
                    [...rows].sort((a, b) => a.id.localeCompare(b.id, undefined, { numeric: true })).map((r) => [
                        chip(r.id), r.arrivalTime, r.burstTime, ...(r.priority != null ? [r.priority] : []),
                        r.startTime, r.completionTime, r.turnaroundTime, r.waitingTime, r.responseTime]))),
            );
        }

        const picker = segmented(ALGORITHMS, algorithm, (v) => {
            algorithm = v;
            note.textContent = NOTES[v];
            quantumField.hidden = !uses().quantum;
            rowsEl.classList.toggle('no-priority', !uses().priority);
            run();
        }, 'Scheduling algorithm');
        note.textContent = NOTES[algorithm];
        quantumField.hidden = !uses().quantum;
        renderRows();

        root.append(h('div', { class: 'split' },
            h('div', { class: 'controls' },
                card('Algorithm', [picker, note, quantumField]),
                card('Processes', [rowsEl,
                    h('div', { class: 'btn-row' },
                        button('Add process', () => {
                            const n = store.processes.length + 1;
                            store.processes.push({ id: `P${n}`, arrival: 0, burst: 4, priority: 1 });
                            renderRows(); run();
                        }, 'secondary'),
                        button('Textbook example', preset, 'ghost'),
                        button('Randomise', random, 'ghost'))]),
                errors),
            results));
        root.random = random;
        root.sync = () => { quantumInput.value = store.quantum; renderRows(); run(); };
        run();
    },
};
