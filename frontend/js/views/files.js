import { post } from '../api.js';
import { clear, debounce, h } from '../dom.js';
import { pseudocode } from '../pseudo.js';
import { button, card, chip, field, metricTiles, notice, numberInput, player, procStyle, segmented, table } from '../ui.js';
import { parseInts } from '../store.js';

const int = (lo, hi) => lo + Math.floor(Math.random() * (hi - lo + 1));

const METHODS = [
    { value: 'contiguous', label: 'Contiguous' }, { value: 'linked', label: 'Linked' }, { value: 'indexed', label: 'Indexed' },
];
const NOTES = {
    contiguous: 'Each file needs one unbroken run of blocks. Reading any block is one seek, but free space fragments and large files may not fit even when enough blocks are free.',
    linked: 'Any free block will do, and each block points to the next. No external fragmentation, but reaching block k means following k pointers.',
    indexed: 'One index block lists every data block. Any block is two reads away and space is not fragmented, at the cost of the index block.',
};
const LINES = {
    contiguous: ['for each file, in order:', '    scan the disk for a run of free blocks as long as the file', '    if none exists: allocation fails',
        '    else: mark the whole run as the file'],
    linked: ['for each file, in order:', '    take the first free blocks, one per file block', '    if too few are free: allocation fails',
        '    link each block to the next with a pointer'],
    indexed: ['for each file, in order:', '    take one free block as the index block', '    take one free block per file block',
        '    store the data block numbers in the index block; fail if disk is full'],
};

function grid(method, files, total, used, upTo) {
    const owner = new Map();
    const placed = files.slice(0, upTo);
    for (const f of placed) {
        f.blocks.forEach((b, pos) => owner.set(b, { name: f.name, role: 'data', next: method === 'linked' ? f.blocks[pos + 1] : null, pos }));
        if (f.indexBlock != null) owner.set(f.indexBlock, { name: f.name, role: 'index' });
    }
    const cols = total <= 32 ? 8 : 16;
    return h('div', { class: 'disk-grid', style: { '--cols': cols } }, Array.from({ length: total }, (_, i) => {
        const o = owner.get(i);
        const reserved = used.includes(i);
        const cls = o ? `blk proc ${o.role}` : reserved ? 'blk reserved' : 'blk free';
        return h('div', { class: cls, style: o ? procStyle(o.name) : {}, title: o ? `Block ${i}: ${o.name} ${o.role}${o.next != null ? `, next ${o.next}` : ''}` : `Block ${i}: ${reserved ? 'reserved' : 'free'}` },
            h('span', { class: 'blk-n' }, i), o ? h('span', { class: 'blk-f' }, o.role === 'index' ? `${o.name}*` : o.name) : null,
            o && o.next != null ? h('span', { class: 'blk-next' }, `to ${o.next}`) : null);
    }));
}

export { grid as diskGrid };

export default {
    id: 'files',
    title: 'File Allocation',
    group: 'Storage',
    blurb: 'Contiguous, linked and indexed allocation on the same disk.',
    mount(root) {
        let method = 'contiguous';
        let total = 32;
        let reserved = [2, 3, 7, 8, 12, 13, 20, 26];
        let files = [{ name: 'A', size: 4 }, { name: 'B', size: 5 }, { name: 'C', size: 3 }, { name: 'D', size: 6 }];
        const errors = notice();
        const results = h('div', { class: 'results' });
        const note = h('p', { class: 'note' }, NOTES[method]);
        const totalInput = numberInput({ value: total, min: 4, max: 256, label: 'Disk blocks', onInput: (v) => { total = v; run(); } });
        const reservedInput = h('input', { type: 'text', value: reserved.join(' '), spellcheck: 'false', 'aria-label': 'Reserved blocks',
            onInput: (e) => { const v = parseInts(e.target.value); if (v) { reserved = v; run(); } else errors.show('Reserved blocks must be whole numbers.'); } });
        const filesInput = h('textarea', { class: 'code-input', rows: 5, spellcheck: 'false', 'aria-label': 'Files', onInput: () => run() });
        filesInput.value = files.map((f) => `${f.name} ${f.size}`).join('\n');

        const run = debounce(async () => {
            try {
                const parsed = filesInput.value.split('\n').map((l) => l.trim()).filter(Boolean).map((l, i) => {
                    const [name, size] = l.split(/\s+/);
                    if (!name || !Number.isInteger(Number(size))) throw new Error(`File ${i + 1}: write "NAME BLOCKS".`);
                    return { name, size: Number(size) };
                });
                const data = await post('/api/file-allocation', { total_blocks: total, files: parsed, used_blocks: reserved });
                errors.hide();
                draw(data);
            } catch (e) { errors.show(e.message); }
        }, 250);

        function draw(data) {
            results.result = data;
            const m = data.methods[method];
            const code = pseudocode(LINES[method]);
            const host = h('div', { class: 'disk-host' });
            const status = h('div', { class: 'now' });
            const allFiles = filesInput.value.split('\n').map((l) => l.trim().split(/\s+/)[0]).filter(Boolean);
            const onFrame = (i) => {
                const upTo = allFiles.slice(0, i);
                const shown = m.files.filter((f) => upTo.includes(f.name));
                clear(host).append(grid(method, shown, data.totalBlocks, data.usedBlocks, shown.length));
                const name = allFiles[i - 1];
                const ok = m.files.find((f) => f.name === name);
                clear(status).append(h('span', null, i === 0 ? 'Empty disk with reserved blocks' : `File ${name}: ${ok ? 'allocated' : 'FAILED'}`),
                    ok ? h('span', null, ok.blocks.length ? `blocks ${ok.blocks.join(', ')}${ok.indexBlock != null ? `, index ${ok.indexBlock}` : ''}` : '') : null);
                code.set(!name ? [] : ok ? [0, 1, 3] : [0, 1, 2]);
            };
            const controls = player({ count: allFiles.length, onFrame, interval: 900 });
            clear(results).append(
                metricTiles([
                    { label: 'Files placed', value: `${m.files.length}/${allFiles.length}`, tone: m.failed.length ? 'bad' : 'good' },
                    { label: 'Free blocks', value: m.freeBlocks },
                    { label: 'Largest free run', value: m.largestFreeRun, hint: 'contiguous blocks' },
                    { label: 'Free fragments', value: m.freeRuns },
                ]),
                h('div', { class: 'playback' },
                    card('Disk', [h('p', { class: 'legend' }, h('span', { class: 'lg lg-req' }, 'file block'), h('span', { class: 'lg lg-idx' }, 'index block'),
                        h('span', { class: 'lg lg-free' }, 'free'), h('span', { class: 'lg lg-res' }, 'reserved')), host, status, controls,
                    m.failed.length ? h('p', { class: 'note warn' }, `Could not place ${m.failed.join(', ')}. ${method === 'contiguous' ? `Free blocks exist (${m.freeBlocks}) but no single run is long enough.` : 'Not enough free blocks.'}`) : null]),
                    card('Pseudocode', code)),
                card('Cost of reading each file’s last block', table(['File', 'Blocks', 'Contiguous', 'Linked', 'Indexed'],
                    filesInput.value.split('\n').map((l) => l.trim().split(/\s+/)).filter((p) => p[0]).map(([name, size]) => {
                        const cell = (k) => { const f = data.methods[k].files.find((x) => x.name === name); return f ? `${f.lastBlockReads} ${f.lastBlockReads === 1 ? 'read' : 'reads'}` : 'fails'; };
                        return [chip(name), size, cell('contiguous'), cell('linked'), cell('indexed')];
                    }))));
        }

        function random() {
            total = [32, 48, 64][int(0, 2)];
            totalInput.value = total;
            reserved = Array.from(new Set(Array.from({ length: int(4, Math.floor(total / 3)) }, () => int(0, total - 1)))).sort((a, b) => a - b);
            reservedInput.value = reserved.join(' ');
            filesInput.value = Array.from({ length: int(3, 6) }, (_, i) => `${String.fromCharCode(65 + i)} ${int(2, 8)}`).join('\n');
            run();
        }

        root.append(h('div', { class: 'split' },
            h('div', { class: 'controls' },
                card('Method', [segmented(METHODS, method, (v) => { method = v; note.textContent = NOTES[v]; run(); }, 'Allocation method'), note]),
                card('Disk', [field('Blocks', totalInput), field('Reserved blocks', reservedInput, 'Already in use, so free space is fragmented'),
                    field('Files, allocated in order', filesInput, 'NAME BLOCKS, one per line'),
                    h('div', { class: 'btn-row' }, button('Randomise', random, 'secondary'))]),
                errors),
            results));
        root.random = random;
        root.sync = () => {};
        run();
    },
};
