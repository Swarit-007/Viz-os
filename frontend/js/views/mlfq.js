import { post } from '../api.js';
import { lanes } from '../charts.js';
import { eventLog, processError, processTable } from '../components.js';
import { clear, debounce, h } from '../dom.js';
import { PSEUDO, pseudocode } from '../pseudo.js';
import { randomProcesses } from '../random.js';
import { store } from '../store.js';
import { badge, button, card, chip, field, metricTiles, notice, numberInput, player, segmented, table } from '../ui.js';

const EVENT_TEXT = {
    arrive: (e) => ['arrives in queue 1', 'neutral'],
    promote: (e) => [`promoted to queue ${e.to - 1} after waiting (aging)`, 'good'],
    preempt: (e) => [`preempted in queue ${e.level} by a higher queue`, 'bad'],
    demote: (e) => [`used its quantum in queue ${e.level}, demoted to queue ${e.to}`, 'neutral'],
    requeue: (e) => [`used its quantum in the last queue ${e.level}, goes to the back`, 'neutral'],
    finish: (e) => [`finished in queue ${e.level}`, 'good'],
};

export default {
    id: 'mlfq',
    title: 'Multilevel Feedback Queue',
    group: 'Processes',
    blurb: 'Queues with rising quanta. See demotion, preemption and aging.',
    mount(root) {
        let levels = 3;
        let quanta = [2, 4, 8];
        let aging = 0;
        const errors = notice();
        const results = h('div', { class: 'results' });
        const editor = processTable({ priority: false, onChange: () => run() });
        const quantaBox = h('div', { class: 'level-inputs' });
        const agingInput = numberInput({ value: aging, min: 0, max: 1000, label: 'Aging threshold', onInput: (v) => { aging = v; run(); } });

        function renderQuanta() {
            clear(quantaBox).append(...quanta.slice(0, levels).map((q, i) => field(`Queue ${i + 1} quantum`,
                numberInput({ value: q, min: 1, max: 100, label: `Queue ${i + 1} quantum`, onInput: (v) => { quanta[i] = v; run(); } }))));
        }
        const levelPicker = segmented([2, 3, 4].map((n) => ({ value: n, label: `${n} queues` })), levels, (v) => {
            levels = v;
            while (quanta.length < v) quanta.push(quanta[quanta.length - 1] * 2);
            renderQuanta(); run();
        }, 'Number of queues');

        const run = debounce(async () => {
            const bad = processError();
            if (bad) { errors.show(bad); return; }
            try {
                const data = await post('/api/scheduling/mlfq', { processes: store.processes, quanta: quanta.slice(0, levels), aging });
                errors.hide();
                draw(data);
            } catch (e) { errors.show(e.message); }
        }, 200);

        function draw(data) {
            root.result = data;
            const m = data.metrics;
            const total = data.ganttChart.totalTime;
            const slices = data.ganttChart.processes;
            const laneRows = Array.from({ length: data.levels }, (_, l) => ({
                label: `Queue ${l + 1}  (q=${data.quanta[l]})`,
                slices: slices.filter((s) => s.level === l + 1),
            }));
            const chartHost = h('div', { class: 'chart-scroll' });
            const status = h('div', { class: 'now' });
            const code = pseudocode(PSEUDO.mlfq.lines);
            const log = eventLog(data.events.map((e) => {
                const [text, tone] = EVENT_TEXT[e.event](e);
                return { time: e.time, node: h('span', null, h('span', { class: 't' }, `t=${e.time}`), chip(e.process), text, badge(e.event, tone)) };
            }));
            const onFrame = (t) => {
                clear(chartHost).append(lanes({ lanes: laneRows, totalTime: total, now: t }));
                const running = slices.find((s) => s.startTime <= t && t < s.startTime + s.duration);
                clear(status).append(h('span', null, `t = ${t}`),
                    h('span', null, 'Running ', running ? [chip(running.name), ` in queue ${running.level}`] : h('em', null, t >= total ? 'finished' : 'idle')));
                log.upTo(t);
                const now = data.events.filter((e) => e.time === t).map((e) => e.event);
                const lines = new Set();
                if (running) PSEUDO.mlfq.roles.run.forEach((i) => lines.add(i));
                now.forEach((ev) => (PSEUDO.mlfq.roles[ev] || []).forEach((i) => lines.add(i)));
                code.set([...lines]);
            };
            const controls = player({ count: total, onFrame, interval: 380 });
            const promoted = data.events.filter((e) => e.event === 'promote').length;
            clear(results).append(
                metricTiles([
                    { label: 'Avg waiting', value: m.avgWaitingTime.toFixed(2) },
                    { label: 'Avg turnaround', value: m.avgTurnaroundTime.toFixed(2) },
                    { label: 'Avg response', value: m.avgResponseTime.toFixed(2) },
                    { label: 'Promotions by aging', value: promoted },
                ]),
                h('div', { class: 'playback' },
                    card('Queues over time', [chartHost, status, controls, h('h4', { class: 'sub' }, 'Event log'), log]),
                    card('Pseudocode', code)),
                card('Per-process results', table(['Process', 'Arrival', 'Burst', 'Start', 'Finish', 'Turnaround', 'Waiting', 'Response'],
                    [...data.processResults].sort((a, b) => a.id.localeCompare(b.id, undefined, { numeric: true })).map((r) => [
                        chip(r.id), r.arrivalTime, r.burstTime, r.startTime, r.completionTime, r.turnaroundTime, r.waitingTime, r.responseTime]))));
        }

        function random() {
            store.processes = randomProcesses();
            aging = [0, 4, 6, 10][Math.floor(Math.random() * 4)];
            agingInput.value = aging;
            editor.render(); run();
        }

        renderQuanta();
        root.append(h('div', { class: 'split' },
            h('div', { class: 'controls' },
                card('Queues', [
                    h('p', { class: 'note' }, 'Every process starts in queue 1. Using a whole quantum demotes it. A higher queue always preempts a lower one.'),
                    levelPicker, quantaBox,
                    field('Aging threshold', agingInput, 'Promote a process after it waits this long in a lower queue. 0 turns aging off.')]),
                card('Processes', [editor, h('div', { class: 'btn-row' }, editor.addButton,
                    button('Starvation example', () => {
                        store.processes = [{ id: 'P1', arrival: 0, burst: 24, priority: 1 }, { id: 'P2', arrival: 0, burst: 24, priority: 1 },
                            ...[2, 4, 6, 8, 10, 12].map((a, i) => ({ id: `P${i + 3}`, arrival: a, burst: 2, priority: 1 }))];
                        aging = 6; agingInput.value = 6; editor.render(); run();
                    }, 'ghost'))]),
                errors),
            results));
        root.random = random;
        root.sync = () => { editor.render(); run(); };
        run();
    },
};
