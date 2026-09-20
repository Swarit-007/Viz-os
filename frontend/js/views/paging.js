import { post } from '../api.js';
import { clear, debounce, h } from '../dom.js';
import { PSEUDO, pseudocode } from '../pseudo.js';
import { randomPages } from '../random.js';
import { parseInts, store } from '../store.js';
import { button, card, field, metricTiles, notice, numberInput, player, segmented } from '../ui.js';

const ALGORITHMS = [
    { value: 'fifo', label: 'FIFO', title: 'First In First Out' },
    { value: 'lru', label: 'LRU', title: 'Least Recently Used' },
    { value: 'optimal', label: 'Optimal', title: 'Belady’s optimal (needs the future)' },
    { value: 'clock', label: 'Clock', title: 'Second chance' },
];
const NOTES = {
    fifo: 'Evicts the page that has been in memory longest. Cheap, but can suffer Belady’s anomaly: more frames may cause more faults.',
    lru: 'Evicts the page unused for the longest time, assuming the past predicts the future.',
    optimal: 'Evicts the page whose next use is farthest away. Impossible to implement online, but the lower bound other algorithms are judged against.',
    clock: 'Approximates LRU: a hand sweeps the frames, clearing reference bits, and evicts the first page whose bit is 0.',
};

// Rebuild slot-stable frame contents (textbook layout) from the server's steps.
function slotGrid(data) {
    const slots = Array(data.frames).fill(null);
    return data.steps.map((s) => {
        let changed = -1;
        if (s.page_fault) {
            changed = s.replaced_page == null ? slots.indexOf(null) : slots.indexOf(s.replaced_page);
            slots[changed] = s.requested_page;
        }
        return { slots: [...slots], changed };
    });
}

export default {
    id: 'paging',
    title: 'Page Replacement',
    group: 'Memory',
    blurb: 'FIFO, LRU, Optimal and Clock with a frame-by-frame view.',
    mount(root) {
        let algorithm = 'lru';
        const errors = notice();
        const results = h('div', { class: 'results' });
        const note = h('p', { class: 'note' }, NOTES[algorithm]);
        const refs = h('input', {
            type: 'text', value: store.pages.join(' '), spellcheck: 'false', 'aria-label': 'Reference string',
            onInput: (e) => {
                const values = parseInts(e.target.value);
                if (values) { store.pages = values; run(); } else errors.show('Pages must be whole numbers separated by spaces or commas.');
            },
        });

        const framesInput = numberInput({ value: store.frames, min: 1, max: 100, label: 'Frames', onInput: (v) => { store.frames = v; run(); } });
        function random() {
            const r = randomPages(); store.pages = r.pages; store.frames = r.frames;
            refs.value = store.pages.join(' '); framesInput.value = store.frames; run();
        }

        const run = debounce(async () => {
            if (!(store.frames >= 1)) { errors.show('Frames must be at least 1.'); return; }
            try {
                const data = await post('/api/page-replacement', { algorithm, frames: store.frames, page_requests: store.pages });
                errors.hide();
                draw(data);
            } catch (e) { errors.show(e.message); }
        }, 200);

        function draw(data) {
            root.result = data;
            const grid = slotGrid(data);
            const key = algorithm;
            const lines = [...PSEUDO.paging.common];
            lines[1] += PSEUDO.paging.hit[key] ? PSEUDO.paging.hit[key].replace(' (', ' (') : '';
            lines[4] = `        else: ${PSEUDO.paging.victim[key]}`;
            const code = pseudocode(lines);
            const host = h('div', { class: 'chart-scroll' });
            const line = h('div', { class: 'now' });
            const render = (upTo) => {
                const cols = data.steps.length;
                const t = h('table', { class: 'frames' });
                t.append(h('thead', null, h('tr', null, h('th', null, 'Request'),
                    data.steps.map((s, i) => h('th', { class: i < upTo ? (s.page_fault ? 'fault' : 'hit') : 'future' }, s.requested_page)))));
                const body = h('tbody');
                for (let f = 0; f < data.frames; f++) {
                    body.append(h('tr', null, h('th', null, `Frame ${f + 1}`),
                        Array.from({ length: cols }, (_, i) => {
                            if (i >= upTo) return h('td', { class: 'future' }, '');
                            const value = grid[i].slots[f];
                            return h('td', { class: grid[i].changed === f ? 'loaded' : '' },
                                value == null ? '' : value,
                                data.algorithm === 'Clock' && data.steps[i].hand === f ? h('sup', { class: 'hand', title: 'clock hand' }) : null,
                                data.algorithm === 'Clock' && value != null ? h('sub', { class: 'refbit', title: 'reference bit' }, data.steps[i].reference_bits[f]) : null);
                        })));
                }
                body.append(h('tr', { class: 'result-row' }, h('th', null, 'Result'),
                    data.steps.map((s, i) => h('td', { class: i < upTo ? (s.page_fault ? 'fault' : 'hit') : 'future' },
                        i < upTo ? (s.page_fault ? 'F' : 'H') : ''))));
                t.append(body);
                clear(host).append(t);
                const s = data.steps[upTo - 1];
                code.set(!s ? [] : !s.page_fault ? [0, 1] : s.replaced_page == null ? [0, 2, 3, 5] : [0, 2, 4, 5]);
                clear(line).append(h('span', null, upTo === 0 ? 'Press play to step through the reference string.' : `Step ${upTo}: ${s.description}`));
            };
            const controls = player({ count: data.steps.length, onFrame: render, interval: 650 });
            clear(results).append(
                metricTiles([
                    { label: 'Page faults', value: data.total_page_faults, tone: 'bad' },
                    { label: 'Hits', value: data.total_hits, tone: 'good' },
                    { label: 'Hit ratio', value: `${(data.hit_ratio * 100).toFixed(1)}%` },
                    { label: 'Fault ratio', value: `${(data.fault_ratio * 100).toFixed(1)}%` },
                ]),
                h('div', { class: 'playback' },
                    card('Frames over time', [h('p', { class: 'legend' },
                        h('span', { class: 'lg lg-req' }, 'page loaded'), h('span', { class: 'lg lg-hit' }, 'hit'), h('span', { class: 'lg lg-fault' }, 'fault')),
                    host, line, controls]),
                    card('Pseudocode', code)));
        }

        root.append(h('div', { class: 'split' },
            h('div', { class: 'controls' },
                card('Algorithm', [segmented(ALGORITHMS, algorithm, (v) => { algorithm = v; note.textContent = NOTES[v]; run(); }, 'Page replacement algorithm'), note]),
                card('Reference string', [
                    field('Frames', framesInput),
                    field('Pages', refs, 'Space or comma separated'),
                    h('div', { class: 'btn-row' },
                        button('Textbook example', () => {
                            store.pages = [7, 0, 1, 2, 0, 3, 0, 4, 2, 3, 0, 3, 2, 1, 2, 0, 1, 7, 0, 1]; refs.value = store.pages.join(' ');
                            run();
                        }, 'ghost'),
                        button('Belady’s anomaly', () => {
                            store.pages = [1, 2, 3, 4, 1, 2, 5, 1, 2, 3, 4, 5]; refs.value = store.pages.join(' '); algorithm = 'fifo';
                            root.querySelector('.segmented').set('fifo'); note.textContent = NOTES.fifo; run();
                        }, 'ghost'),
                        button('Randomise', random, 'ghost'))]),
                errors),
            results));
        root.random = random;
        root.sync = () => { refs.value = store.pages.join(' '); framesInput.value = store.frames; run(); };
        run();
    },
};
