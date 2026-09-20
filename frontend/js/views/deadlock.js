import { post } from '../api.js';
import { graph } from '../charts.js';
import { clear, debounce, h } from '../dom.js';
import { badge, button, card, chip, field, matrixEditor, notice, numberInput, table, vectorEditor } from '../ui.js';

const PRESETS = {
    deadlock: { n: 3, m: 2, allocation: [[1, 0], [0, 1], [1, 1]], request: [[0, 1], [1, 0], [1, 1]], available: [0, 0] },
    safe: { n: 4, m: 3, allocation: [[0, 1, 0], [2, 0, 0], [3, 0, 3], [2, 1, 1]], request: [[0, 0, 0], [2, 0, 2], [0, 0, 0], [1, 0, 0]], available: [0, 0, 0] },
};

export default {
    id: 'deadlock',
    title: 'Deadlock Detection',
    group: 'Deadlocks',
    blurb: 'Detect deadlocked processes and see the wait-for graph.',
    mount(root) {
        const errors = notice();
        const results = h('div', { class: 'results' });
        let n = 3;
        let m = 2;
        const allocation = matrixEditor({ title: 'Allocation', rowLabel: 'P', colLabel: 'R', onChange: () => run() });
        const request = matrixEditor({ title: 'Request', rowLabel: 'P', colLabel: 'R', onChange: () => run() });
        const available = vectorEditor({ title: 'Available', colLabel: 'R', onChange: () => run() });

        function build(state) {
            n = state.n; m = state.m;
            allocation.build(n, m, state.allocation);
            request.build(n, m, state.request);
            available.build(m, state.available);
            sizeN.value = n; sizeM.value = m;
        }
        const resize = () => {
            const rows = Math.min(Math.max(Number(sizeN.value) || 1, 1), 12);
            const cols = Math.min(Math.max(Number(sizeM.value) || 1, 1), 8);
            const keep = (mat, r, c) => Array.from({ length: r }, (_, i) => Array.from({ length: c }, (_, j) => mat[i]?.[j] ?? 0));
            build({ n: rows, m: cols, allocation: keep(allocation.get(), rows, cols), request: keep(request.get(), rows, cols),
                available: Array.from({ length: cols }, (_, j) => available.get()[j] ?? 0) });
            run();
        };
        const sizeN = numberInput({ value: n, min: 1, max: 12, label: 'Processes', onInput: debounce(resize, 300) });
        const sizeM = numberInput({ value: m, min: 1, max: 8, label: 'Resource types', onInput: debounce(resize, 300) });

        const run = debounce(async () => {
            try {
                const data = await post('/api/deadlock', {
                    num_processes: n, num_resources: m, allocation: allocation.get(), request: request.get(), available: available.get(),
                });
                errors.hide();
                draw(data);
            } catch (e) { errors.show(e.message); }
        }, 250);

        function draw(data) {
            const g = data.waitForGraph;
            const nodes = g.processes.map((p) => ({ id: p.id, label: p.name, tone: p.isDeadlocked ? 'bad' : 'ok' }));
            const edges = g.edges.map((e) => ({ from: e.from, to: e.to, label: e.label }));
            clear(results).append(
                h('div', { class: `verdict ${data.hasDeadlock ? 'verdict-bad' : 'verdict-good'} verdict-lg` },
                    badge(data.hasDeadlock ? 'Deadlock' : 'No deadlock', data.hasDeadlock ? 'bad' : 'good'),
                    data.hasDeadlock
                        ? h('span', null, ' Deadlocked: ', data.deadlockedProcesses.map((p) => chip(p)))
                        : h('span', null, ' Every process can eventually obtain what it is waiting for.')),
                card('Wait-for graph', [h('p', { class: 'note' }, 'An edge Pi → Pj means Pi requests a resource type that Pj currently holds. Red nodes cannot finish.'),
                    graph(nodes, edges, { height: 340 })]),
                card('Detection trace', table(['Round', 'Work', 'Finished this round'],
                    data.steps.map((s, i) => (s.initializedFinished
                        ? ['init', '—', s.initializedFinished.length ? `${s.initializedFinished.join(', ')} (hold nothing)` : 'none']
                        : [i, `[${s.work.join(', ')}]`, s.allocated.length ? s.allocated.join(', ') : 'no progress'])))));
        }

        root.append(h('div', { class: 'split split-wide' },
            h('div', { class: 'controls' },
                card('System', [
                    h('div', { class: 'grid-2' }, field('Processes', sizeN), field('Resource types', sizeM)),
                    allocation, request, available,
                    h('div', { class: 'btn-row' },
                        button('Deadlock example', () => { build(PRESETS.deadlock); run(); }, 'ghost'),
                        button('Safe example', () => { build(PRESETS.safe); run(); }, 'ghost'))]),
                errors),
            results));
        build(PRESETS.deadlock);
        run();
    },
};
