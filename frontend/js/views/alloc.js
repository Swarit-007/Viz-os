import { post } from '../api.js';
import { clear, debounce, h } from '../dom.js';
import { randomMemory } from '../random.js';
import { parseInts } from '../store.js';
import { button, card, field, metricTiles, notice, procStyle, segmented, table } from '../ui.js';

const STRATEGIES = [
    { value: 'first', label: 'First Fit', title: 'First block that is large enough' },
    { value: 'best', label: 'Best Fit', title: 'Smallest block that is large enough' },
    { value: 'worst', label: 'Worst Fit', title: 'Largest block' },
    { value: 'next', label: 'Next Fit', title: 'First Fit resuming from the last allocation' },
];
const NOTES = {
    first: 'Scans from the start and takes the first block that fits. Fast, but fragments the front of memory.',
    best: 'Takes the smallest block that fits, leaving the least waste per allocation but many tiny unusable holes.',
    worst: 'Takes the largest block, hoping the leftover stays big enough to be useful.',
    next: 'Like First Fit but resumes scanning where the previous allocation ended.',
};

export default {
    id: 'alloc',
    title: 'Memory Allocation',
    group: 'Memory',
    blurb: 'First, Best, Worst and Next Fit placed into fixed partitions.',
    mount(root) {
        let strategy = 'best';
        let blocks = [100, 500, 200, 300, 600];
        let procs = [212, 417, 112, 426];
        const errors = notice();
        const results = h('div', { class: 'results' });
        const note = h('p', { class: 'note' }, NOTES[strategy]);
        const parse = (setter) => (e) => {
            const values = parseInts(e.target.value);
            if (values) { setter(values); run(); } else errors.show('Enter whole numbers separated by spaces or commas.');
        };
        const blocksInput = h('input', { type: 'text', value: blocks.join(' '), spellcheck: 'false', 'aria-label': 'Block sizes', onInput: parse((v) => { blocks = v; }) });
        const procsInput = h('input', { type: 'text', value: procs.join(' '), spellcheck: 'false', 'aria-label': 'Process sizes', onInput: parse((v) => { procs = v; }) });

        function random() {
            const r = randomMemory(); blocks = r.blocks; procs = r.procs;
            blocksInput.value = blocks.join(' '); procsInput.value = procs.join(' '); run();
        }

        const run = debounce(async () => {
            try {
                const data = await post('/api/memory-allocation', { strategy, blocks, processes: procs });
                errors.hide();
                draw(data);
            } catch (e) { errors.show(e.message); }
        }, 200);

        function draw(data) {
            root.result = data;
            const perBlock = data.blocks.map(() => []);
            data.allocation.forEach((a, i) => { if (a.block) perBlock[a.block - 1].push({ id: `P${i + 1}`, size: a.process }); });
            const largest = Math.max(...data.blocks);
            const bars = data.final_block_status.map((b, i) => h('div', { class: 'block-row' },
                h('span', { class: 'block-name' }, `Block ${b.block_number}`, h('small', null, b.size)),
                h('div', { class: 'block-track' },
                    h('div', { class: 'block-bar', style: { width: `${(b.size / largest) * 100}%` } },
                        perBlock[i].map((p) => h('span', { class: 'seg proc', style: { ...procStyle(p.id), flexGrow: p.size }, title: `${p.id}: ${p.size}` }, p.id)),
                        b.remaining > 0 ? h('span', { class: 'seg free', style: { flexGrow: b.remaining }, title: `Free: ${b.remaining}` }, b.remaining) : null))));
            const failed = data.allocation.map((a, i) => (a.block ? null : `P${i + 1} (${a.process})`)).filter(Boolean);
            const s = data.summary;
            clear(results).append(
                metricTiles([
                    { label: 'Allocated', value: s.allocated_count, tone: 'good' },
                    { label: 'Not allocated', value: s.unallocated_count, tone: s.unallocated_count ? 'bad' : undefined },
                    { label: 'Total free', value: s.total_free, hint: 'across all blocks' },
                    { label: 'Largest free block', value: s.largest_free_block, hint: 'external fragmentation' },
                ]),
                card('Memory layout', [bars, failed.length ? h('p', { class: 'note warn' }, `Could not place: ${failed.join(', ')}. Total free space (${s.total_free}) may still exceed a request but is fragmented.`) : null]),
                card('Steps', table(['Process', 'Size', 'Result'], data.steps.map((st) => [`P${st.process_index}`, st.process, st.description]))));
        }

        root.append(h('div', { class: 'split' },
            h('div', { class: 'controls' },
                card('Strategy', [segmented(STRATEGIES, strategy, (v) => { strategy = v; note.textContent = NOTES[v]; run(); }, 'Allocation strategy'), note]),
                card('Memory', [
                    field('Block sizes', blocksInput, 'Free partitions, space or comma separated'),
                    field('Process sizes', procsInput, 'Requests, in arrival order'),
                    h('div', { class: 'btn-row' }, button('Randomise', random, 'secondary'), button('Textbook example', () => {
                        blocks = [100, 500, 200, 300, 600]; procs = [212, 417, 112, 426];
                        blocksInput.value = blocks.join(' '); procsInput.value = procs.join(' '); run();
                    }, 'ghost'))]),
                errors),
            results));
        root.random = random;
        root.sync = () => run();
        run();
    },
};
