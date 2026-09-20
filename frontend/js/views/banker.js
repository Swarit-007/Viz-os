import { post } from '../api.js';
import { graph } from '../charts.js';
import { clear, debounce, h } from '../dom.js';
import { badge, button, card, chip, field, matrixEditor, metricTiles, notice, numberInput, table, vectorEditor } from '../ui.js';

const TEXTBOOK = {
    n: 5, m: 3,
    allocation: [[0, 1, 0], [2, 0, 0], [3, 0, 2], [2, 1, 1], [0, 0, 2]],
    max: [[7, 5, 3], [3, 2, 2], [9, 0, 2], [2, 2, 2], [4, 3, 3]],
    available: [3, 3, 2],
};

export default {
    id: 'bankers',
    title: "Banker's Algorithm",
    group: 'Deadlocks',
    blurb: 'Safety check, safe sequence, resource requests and allocation graph.',
    mount(root) {
        const errors = notice();
        const results = h('div', { class: 'results' });
        const requestOut = h('div', { class: 'request-out' });
        let n = TEXTBOOK.n;
        let m = TEXTBOOK.m;

        const allocation = matrixEditor({ title: 'Allocation', rowLabel: 'P', colLabel: 'R', onChange: () => run() });
        const max = matrixEditor({ title: 'Max', rowLabel: 'P', colLabel: 'R', onChange: () => run() });
        const available = vectorEditor({ title: 'Available', colLabel: 'R', onChange: () => run() });
        const requestVec = vectorEditor({ title: 'Request', colLabel: 'R' });
        const processInput = numberInput({ value: 1, min: 1, max: n, label: 'Requesting process' });

        function build(state) {
            n = state.n; m = state.m;
            allocation.build(n, m, state.allocation);
            max.build(n, m, state.max);
            available.build(m, state.available);
            requestVec.build(m, Array(m).fill(0));
            processInput.max = n;
            sizeN.value = n; sizeM.value = m;
        }
        const resize = () => {
            const rows = Math.min(Math.max(Number(sizeN.value) || 1, 1), 12);
            const cols = Math.min(Math.max(Number(sizeM.value) || 1, 1), 8);
            const keep = (mat, r, c) => Array.from({ length: r }, (_, i) => Array.from({ length: c }, (_, j) => mat[i]?.[j] ?? 0));
            build({ n: rows, m: cols, allocation: keep(allocation.get(), rows, cols), max: keep(max.get(), rows, cols),
                available: Array.from({ length: cols }, (_, j) => available.get()[j] ?? 0) });
            run();
        };
        const sizeN = numberInput({ value: n, min: 1, max: 12, label: 'Processes', onInput: debounce(resize, 300) });
        const sizeM = numberInput({ value: m, min: 1, max: 8, label: 'Resource types', onInput: debounce(resize, 300) });

        const state = () => ({ allocation: allocation.get(), max: max.get(), available: available.get() });

        const run = debounce(async () => {
            clear(requestOut);
            try {
                const data = await post('/api/bankers', { num_processes: n, num_resources: m, ...state() });
                errors.hide();
                draw(data);
            } catch (e) { errors.show(e.message); }
        }, 250);

        async function submitRequest() {
            try {
                const data = await post('/api/bankers/request', {
                    ...state(), process: Number(processInput.value), request: requestVec.get(),
                });
                errors.hide();
                clear(requestOut).append(
                    h('div', { class: `verdict ${data.granted ? 'verdict-good' : 'verdict-bad'}` },
                        badge(data.granted ? 'Granted' : 'Denied', data.granted ? 'good' : 'bad'),
                        h('span', null, ` ${data.process} requests [${data.request.join(', ')}]. ${data.reason}.`)),
                    data.granted ? h('p', { class: 'note' }, 'Safe sequence after granting: ', data.safeSequence.map((p) => chip(p)),
                        ' — use “Apply granted request” to carry the new state forward.') : null,
                    data.granted ? button('Apply granted request', () => {
                        build({ n, m, allocation: data.allocation, max: max.get(), available: data.available }); run();
                    }, 'secondary') : null);
            } catch (e) { errors.show(e.message); }
        }

        function draw(data) {
            const rag = data.rag;
            const nodes = [
                ...rag.processes.map((p) => ({ id: p.name, label: p.name, side: 'left' })),
                ...rag.resources.map((r) => ({ id: r.name, label: r.name, side: 'right', square: true })),
            ];
            const edges = rag.edges.map((e) => ({ from: e.from, to: e.to, dashed: e.type === 'request', value: e.value,
                label: e.type === 'allocation' ? `${e.from} holds ${e.value} for ${e.to}` : `${e.from} may still request ${e.value} of ${e.to}` }));
            clear(results).append(
                h('div', { class: `verdict ${data.isSafe ? 'verdict-good' : 'verdict-bad'} verdict-lg` },
                    badge(data.isSafe ? 'Safe state' : 'Unsafe state', data.isSafe ? 'good' : 'bad'),
                    data.isSafe
                        ? h('span', { class: 'seq' }, data.safeSequence.map((p, i) => [i ? h('span', { class: 'arrow' }, '→') : null, chip(p)]))
                        : h('span', null, ` No process ordering can finish. Only ${data.safeSequence.length} of ${n} can complete: ${data.safeSequence.join(', ') || 'none'}.`)),
                card('Need matrix (Max − Allocation)', table(['', ...Array.from({ length: m }, (_, j) => `R${j + 1}`)],
                    data.need.map((row, i) => [chip(`P${i + 1}`), ...row]))),
                card('Safety algorithm trace', table(['Step', 'Work', 'Chosen', 'Released'],
                    data.steps.map((s, i) => [i + 1, `[${s.work.join(', ')}]`, s.chosenProcess ? chip(s.chosenProcess) : h('em', null, data.isSafe ? 'all finished' : 'none can proceed'),
                        s.chosenProcess ? `[${s.allocationsReleased.join(', ')}]` : '—']))),
                card('Resource allocation graph', [h('p', { class: 'legend' },
                    h('span', { class: 'lg lg-solid' }, 'R → P  allocated'), h('span', { class: 'lg lg-dash' }, 'P → R  remaining need')),
                graph(nodes, edges, { height: Math.max(320, Math.max(n, m) * 84), layout: 'bipartite' })]));
        }

        root.append(h('div', { class: 'split split-wide' },
            h('div', { class: 'controls' },
                card('System', [
                    h('div', { class: 'grid-2' }, field('Processes', sizeN), field('Resource types', sizeM)),
                    allocation, max, available,
                    h('div', { class: 'btn-row' },
                        button('Textbook example', () => { build(TEXTBOOK); run(); }, 'ghost'),
                        button('Random state', async () => {
                            try {
                                const data = await post('/api/bankers', { num_processes: n, num_resources: m });
                                build({ n, m, allocation: data.allocation, max: data.max, available: data.available });
                                run();
                            } catch (e) { errors.show(e.message); }
                        }, 'ghost'))]),
                card('Try a resource request', [
                    h('div', { class: 'grid-2' }, field('Process', processInput), h('span')),
                    requestVec,
                    button('Check request', submitRequest, 'primary'), requestOut]),
                errors),
            results));
        build(TEXTBOOK);
        run();
    },
};
