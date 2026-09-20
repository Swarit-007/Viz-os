import { post } from '../api.js';
import { clear, debounce, h } from '../dom.js';
import { icon } from '../icons.js';
import { pseudocode } from '../pseudo.js';
import { button, card, chip, field, metricTiles, notice, numberInput, player, procStyle, segmented, table } from '../ui.js';

const int = (lo, hi) => lo + Math.floor(Math.random() * (hi - lo + 1));

const BUDDY_LINES = ['alloc(size):', '    n = round size up to a power of two (at least the minimum block)',
    '    find the smallest free block that is >= n', '    while block > n: split it into two buddies',
    '    mark the block used', 'free(block):', '    mark the block free',
    '    while its buddy is also free: merge the two into one block'];
const SEG_LINES = ['translate(segment, offset):', '    entry = segment_table[segment]', '    if the segment does not exist: fault',
    '    if offset >= entry.limit: segmentation fault', '    return entry.base + offset'];

function parseOps(text) {
    const ops = [];
    for (const [i, raw] of text.split('\n').entries()) {
        const line = raw.trim();
        if (!line) continue;
        const [op, name, size] = line.split(/\s+/);
        if (op === 'alloc' && name && Number.isInteger(Number(size))) ops.push({ op, name, size: Number(size) });
        else if (op === 'free' && name) ops.push({ op, name });
        else throw new Error(`Line ${i + 1}: write "alloc NAME SIZE" or "free NAME".`);
    }
    return ops;
}

function memoryBar(blocks, total, { mark = null } = {}) {
    const bar = h('div', { class: 'mem-bar' }, blocks.map((b) => {
        const hue = b.name ? { style: procStyle(b.name) } : {};
        const wasted = b.status === 'used' ? b.size - b.requested : 0;
        return h('div', { class: `mem-block ${b.status} ${b.name ? 'proc' : ''}`, style: { flexGrow: b.size, flexBasis: 0, ...(hue.style || {}) },
            title: `${b.name || 'free'}: ${b.size} at ${b.start}${wasted ? ` (wasted ${wasted})` : ''}` },
        h('span', { class: 'mem-name' }, b.name || ''), h('span', { class: 'mem-size' }, b.size),
        wasted ? h('i', { class: 'waste', style: { height: `${(wasted / b.size) * 100}%` } }) : null);
    }));
    const wrap = h('div', { class: 'mem-wrap' }, bar);
    if (mark != null) wrap.append(h('div', { class: 'mem-mark', style: { left: `${(mark / total) * 100}%` } }, h('span', null, mark)));
    return wrap;
}

function buddyPanel() {
    let memory = 1024;
    let minBlock = 32;
    const errors = notice();
    const results = h('div', { class: 'results' });
    const ops = h('textarea', { class: 'code-input', rows: 9, spellcheck: 'false', 'aria-label': 'Operations',
        onInput: () => run() });
    ops.value = 'alloc A 100\nalloc B 240\nalloc C 64\nalloc D 60\nfree B\nfree A\nfree C\nfree D';

    const run = debounce(async () => {
        try {
            const data = await post('/api/memory/buddy', { memory_size: memory, min_block: minBlock, operations: parseOps(ops.value) });
            errors.hide();
            draw(data);
        } catch (e) { errors.show(e.message); }
    }, 250);

    function draw(data) {
        results.result = data;
        const code = pseudocode(BUDDY_LINES);
        const host = h('div', { class: 'mem-host' });
        const detail = h('ul', { class: 'tick-events' });
        const status = h('div', { class: 'now' });
        const startBlocks = [{ start: 0, size: data.memorySize, status: 'free', name: null, requested: 0 }];
        const onFrame = (i) => {
            const step = i === 0 ? null : data.steps[i - 1];
            clear(host).append(memoryBar(step ? step.blocks : startBlocks, data.memorySize));
            clear(detail).append(...(step ? step.detail : ['Memory starts as one free block.']).map((d) => h('li', { class: step && !step.ok ? 'bad' : '' }, d)));
            clear(status).append(h('span', null, step ? `${step.op} ${step.name}` : 'start'),
                step ? h('span', null, `internal waste ${step.internalFragmentation}`) : null,
                step ? h('span', null, `free ${step.freeMemory}`) : null,
                step ? h('span', null, `largest free ${step.largestFree}`) : null);
            const lines = new Set();
            if (step) {
                if (step.op === 'alloc') { [1, 2].forEach((x) => lines.add(x)); }
                if (step.op === 'free') lines.add(6);
                for (const d of step.detail) {
                    if (/^Split/.test(d)) lines.add(3);
                    if (/^Allocate/.test(d)) lines.add(4);
                    if (/^Merge/.test(d)) lines.add(7);
                }
            }
            code.set([...lines]);
        };
        const controls = player({ count: data.steps.length, onFrame, interval: 800, initial: 0 });
        const last = data.steps[data.steps.length - 1];
        clear(results).append(
            metricTiles([
                { label: 'Internal waste now', value: last.internalFragmentation, hint: 'rounded-up space unused' },
                { label: 'Free memory', value: last.freeMemory }, { label: 'Largest free block', value: last.largestFree },
                { label: 'Failed allocations', value: data.steps.filter((s) => !s.ok).length, tone: data.steps.some((s) => !s.ok) ? 'bad' : undefined },
            ]),
            h('div', { class: 'playback' },
                card('Memory', [h('p', { class: 'legend' }, h('span', { class: 'lg lg-req' }, 'allocated'), h('span', { class: 'lg lg-free' }, 'free'), h('span', { class: 'lg lg-waste' }, 'wasted inside block')),
                    host, status, controls, detail]),
                card('Pseudocode', code)));
    }

    function random() {
        const live = [];
        const lines = [];
        for (let i = 0; i < int(8, 12); i += 1) {
            if (live.length && Math.random() < 0.4) lines.push(`free ${live.splice(int(0, live.length - 1), 1)[0]}`);
            else { const name = String.fromCharCode(65 + i); lines.push(`alloc ${name} ${int(10, memory / 4)}`); live.push(name); }
        }
        ops.value = lines.join('\n'); run();
    }

    const controls = [
        card('Allocator', [
            field('Total memory', segmented([256, 512, 1024, 2048].map((n) => ({ value: n, label: String(n) })), memory, (v) => { memory = v; run(); }, 'Total memory')),
            field('Smallest block', segmented([8, 16, 32, 64].map((n) => ({ value: n, label: String(n) })), minBlock, (v) => { minBlock = v; run(); }, 'Smallest block'))]),
        card('Operations', [field('One per line', ops, 'alloc NAME SIZE, or free NAME'),
            h('div', { class: 'btn-row' }, button('Randomise', random, 'secondary'))]),
        errors];
    return { controls, results, run, random };
}

function segmentPanel() {
    let memory = 1000;
    let segments = [{ name: 'code', base: 0, limit: 300 }, { name: 'data', base: 500, limit: 200 }, { name: 'stack', base: 800, limit: 150 }];
    const errors = notice();
    const results = h('div', { class: 'results' });
    const rowsEl = h('div', { class: 'seg-rows' });
    const accesses = h('textarea', { class: 'code-input', rows: 6, spellcheck: 'false', 'aria-label': 'Accesses', onInput: () => run() });
    accesses.value = 'code 10\ndata 199\ndata 200\nstack 149\nheap 0';
    const memInput = numberInput({ value: memory, min: 1, max: 1000000, label: 'Memory size', onInput: (v) => { memory = v; run(); } });

    function renderRows() {
        clear(rowsEl).append(h('div', { class: 'seg-row seg-head' }, ...['Segment', 'Base', 'Limit', ''].map((t) => h('span', null, t))),
            ...segments.map((s, i) => h('div', { class: 'seg-row' },
                h('input', { type: 'text', value: s.name, 'aria-label': 'Segment name', onInput: (e) => { s.name = e.target.value.trim(); run(); } }),
                numberInput({ value: s.base, min: 0, label: `${s.name} base`, onInput: (v) => { s.base = v; run(); } }),
                numberInput({ value: s.limit, min: 1, label: `${s.name} limit`, onInput: (v) => { s.limit = v; run(); } }),
                h('button', { type: 'button', class: 'icon-btn', 'aria-label': `Remove ${s.name}`, disabled: segments.length === 1,
                    onClick: () => { segments.splice(i, 1); renderRows(); run(); } }, icon('x')))));
    }

    const run = debounce(async () => {
        try {
            const accs = accesses.value.split('\n').map((l) => l.trim()).filter(Boolean).map((l, i) => {
                const [segment, offset] = l.split(/\s+/);
                if (!segment || !Number.isInteger(Number(offset))) throw new Error(`Access ${i + 1}: write "SEGMENT OFFSET".`);
                return { segment, offset: Number(offset) };
            });
            const data = await post('/api/memory/segmentation', { memory_size: memory, segments, accesses: accs });
            errors.hide();
            draw(data);
        } catch (e) { errors.show(e.message); }
    }, 250);

    function draw(data) {
        results.result = data;
        const code = pseudocode(SEG_LINES);
        const host = h('div', { class: 'mem-host' });
        const line = h('div', { class: 'now' });
        const layoutBlocks = data.layout.map((b) => ({ start: b.base, size: b.size, status: b.kind === 'hole' ? 'free' : 'used', name: b.name || null, requested: b.size }));
        const onFrame = (i) => {
            const a = data.accesses[i - 1];
            clear(host).append(memoryBar(layoutBlocks, data.memorySize, { mark: a && a.ok ? a.physical : null }));
            clear(line).append(...(a ? [h('span', null, `${a.segment}:${a.offset}`), h('span', { class: a.ok ? '' : 'bad-text' }, a.reason)] : [h('span', null, 'Press play to translate each access.')]));
            const exists = a && data.table.some((t) => t.name === a.segment);
            code.set(!a ? [] : !exists ? [1, 2] : !a.ok ? [1, 3] : [1, 4]);
        };
        const controls = player({ count: data.accesses.length, onFrame, interval: 900, initial: 0 });
        clear(results).append(
            metricTiles([
                { label: 'Accesses', value: data.accesses.length }, { label: 'Segmentation faults', value: data.faults, tone: data.faults ? 'bad' : 'good' },
                { label: 'Free memory', value: data.freeMemory }, { label: 'Largest hole', value: data.largestHole },
            ]),
            h('div', { class: 'playback' },
                card('Physical memory', [host, line, controls]),
                card('Pseudocode', code)),
            card('Translations', table(['Segment', 'Offset', 'Physical address', 'Result'],
                data.accesses.map((a) => ({ className: a.ok ? '' : 'fault-row', cells: [chip(a.segment.slice(0, 6)), a.offset, a.ok ? a.physical : '-', a.reason] })))));
    }

    function random() {
        const names = ['code', 'data', 'stack', 'heap', 'lib'].slice(0, int(3, 5));
        memory = 1000; memInput.value = memory;
        let cursor = int(0, 60);
        segments = names.map((name) => { const limit = int(80, 200); const seg = { name, base: cursor, limit }; cursor += limit + int(0, 60); return seg; });
        accesses.value = Array.from({ length: 8 }, () => { const s = segments[int(0, segments.length - 1)]; return `${s.name} ${int(0, Math.round(s.limit * 1.3))}`; }).join('\n');
        renderRows(); run();
    }
    renderRows();
    const controls = [
        card('Segment table', [field('Memory size', memInput), rowsEl,
            h('div', { class: 'btn-row' }, button('Add segment', () => { segments.push({ name: `seg${segments.length + 1}`, base: 0, limit: 50 }); renderRows(); run(); }, 'secondary'),
                button('Randomise', random, 'ghost'))]),
        card('Logical accesses', field('One per line', accesses, 'SEGMENT OFFSET')), errors];
    return { controls, results, run, random };
}

export { memoryBar };

export default {
    id: 'buddy',
    title: 'Buddy and Segments',
    group: 'Memory',
    blurb: 'Buddy-system splitting and merging, and segment-table translation.',
    mount(root) {
        const panels = { buddy: buddyPanel(), segments: segmentPanel() };
        let current = 'buddy';
        const controlsHost = h('div', { class: 'controls' });
        const resultsHost = h('div', { class: 'stack' });
        const picker = segmented([{ value: 'buddy', label: 'Buddy system' }, { value: 'segments', label: 'Segmentation' }], current, (v) => show(v), 'Model');
        function show(v) {
            current = v;
            clear(controlsHost).append(card('Model', picker), ...panels[v].controls);
            clear(resultsHost).append(panels[v].results);
            panels[v].run();
        }
        root.append(h('div', { class: 'split' }, controlsHost, resultsHost));
        root.random = () => panels[current].random();
        root.sync = () => {};
        Object.defineProperty(root, 'result', { get: () => panels[current].results.result, set: () => {}, configurable: true });
        show(current);
    },
};
