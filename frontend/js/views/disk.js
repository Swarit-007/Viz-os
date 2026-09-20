import { post } from '../api.js';
import { diskPath } from '../charts.js';
import { clear, debounce, h } from '../dom.js';
import { randomDisk } from '../random.js';
import { parseInts, store } from '../store.js';
import { button, card, field, metricTiles, notice, numberInput, player, segmented, table } from '../ui.js';

const ALGORITHMS = [
    { value: 'fcfs', label: 'FCFS', title: 'First Come First Serve' },
    { value: 'sstf', label: 'SSTF', title: 'Shortest Seek Time First' },
    { value: 'scan', label: 'SCAN', title: 'Elevator: sweep to the end, then reverse' },
    { value: 'cscan', label: 'C-SCAN', title: 'Circular SCAN' },
    { value: 'look', label: 'LOOK', title: 'SCAN that turns at the last request' },
    { value: 'clook', label: 'C-LOOK', title: 'Circular LOOK' },
];
const NOTES = {
    fcfs: 'Services requests in arrival order. Fair, but the head can swing wildly across the disk.',
    sstf: 'Always moves to the closest pending request. Low movement, but distant requests can starve.',
    scan: 'The head sweeps to the physical end of the disk servicing requests on the way, then reverses.',
    cscan: 'Sweeps in one direction only; at the end it jumps back and sweeps again. Gives more uniform wait times. The return jump is counted as movement.',
    look: 'Like SCAN but reverses at the last request instead of travelling to the disk edge.',
    clook: 'Like C-SCAN but only travels as far as the last request before jumping back. The jump is counted as movement.',
};

export default {
    id: 'disk',
    title: 'Disk Scheduling',
    group: 'Storage',
    blurb: 'Head movement for FCFS, SSTF, SCAN, C-SCAN, LOOK and C-LOOK.',
    mount(root) {
        let algorithm = 'sstf';
        const d = store.disk;
        const errors = notice();
        const results = h('div', { class: 'results' });
        const note = h('p', { class: 'note' }, NOTES[algorithm]);
        const dirPicker = segmented([{ value: 'up', label: 'Up ↑' }, { value: 'down', label: 'Down ↓' }], d.direction,
            (v) => { d.direction = v; run(); }, 'Direction');
        const dirField = field('Sweep direction', dirPicker, 'For SCAN family');
        const headInput = numberInput({ value: d.head, min: 0, label: 'Head', onInput: (v) => { d.head = v; run(); } });
        const sizeInput = numberInput({ value: d.size, min: 2, label: 'Cylinders', onInput: (v) => { d.size = v; run(); } });
        const requests = h('input', {
            type: 'text', value: d.requests.join(' '), spellcheck: 'false', 'aria-label': 'Cylinder requests',
            onInput: (e) => {
                const values = parseInts(e.target.value);
                if (values) { d.requests = values; run(); } else errors.show('Requests must be whole numbers separated by spaces or commas.');
            },
        });

        const syncInputs = () => {
            requests.value = d.requests.join(' '); headInput.value = d.head; sizeInput.value = d.size;
            dirPicker.set(d.direction);
        };
        function random() { Object.assign(d, randomDisk()); syncInputs(); run(); }

        const run = debounce(async () => {
            if (!Number.isInteger(d.head) || !Number.isInteger(d.size)) { errors.show('Head and disk size must be whole numbers.'); return; }
            try {
                const data = await post('/api/disk-scheduling', {
                    algorithm, requests: d.requests, head: d.head, disk_size: d.size, direction: d.direction,
                });
                errors.hide();
                draw(data);
            } catch (e) { errors.show(e.message); }
        }, 200);

        function draw(data) {
            root.result = data;
            const host = h('div', { class: 'chart-scroll' });
            const line = h('div', { class: 'now' });
            const controls = player({
                count: data.steps.length, interval: 600,
                onFrame: (i) => {
                    clear(host).append(diskPath(data, { upTo: i }));
                    const s = data.steps[i - 1];
                    clear(line).append(h('span', null, i === 0 ? `Head starts at ${data.head}`
                        : `Step ${i}: ${s.from} → ${s.to} (${s.distance} cylinders${s.jump ? ', return jump' : ''})`));
                },
            });
            clear(results).append(
                metricTiles([
                    { label: 'Total head movement', value: data.total_movement, hint: 'cylinders' },
                    { label: 'Average seek', value: data.average_seek.toFixed(2), hint: 'per request' },
                    ...(data.jump_movement ? [{ label: 'Of which return jump', value: data.jump_movement }] : []),
                ]),
                card('Head movement', [h('p', { class: 'legend' },
                    h('span', { class: 'lg lg-head' }, 'start'), h('span', { class: 'lg lg-req' }, 'request serviced'),
                    h('span', { class: 'lg lg-edge' }, 'disk edge'), h('span', { class: 'lg lg-jump' }, 'return jump')),
                host, line, controls]),
                card('Service order', table(['#', 'From', 'To', 'Distance', 'Note'],
                    data.steps.map((s, i) => [i + 1, s.from, s.to, s.distance,
                        s.jump ? 'return jump' : s.serviced ? 'serviced' : 'disk edge']))),
            );
        }

        root.append(h('div', { class: 'split' },
            h('div', { class: 'controls' },
                card('Algorithm', [segmented(ALGORITHMS, algorithm, (v) => {
                    algorithm = v; note.textContent = NOTES[v];
                    dirField.hidden = v === 'fcfs' || v === 'sstf'; run();
                }, 'Disk scheduling algorithm'), note]),
                card('Disk', [
                    h('div', { class: 'grid-2' }, field('Head position', headInput), field('Cylinders', sizeInput)),
                    dirField,
                    field('Request queue', requests, 'Cylinder numbers, space or comma separated'),
                    h('div', { class: 'btn-row' },
                        button('Textbook example', () => {
                            Object.assign(d, { requests: [98, 183, 37, 122, 14, 124, 65, 67], head: 53, size: 200, direction: 'up' });
                            requests.value = d.requests.join(' '); headInput.value = d.head; sizeInput.value = d.size; run();
                        }, 'ghost'),
                        button('Randomise', random, 'ghost'))]),
                errors),
            results));
        dirField.hidden = algorithm === 'fcfs' || algorithm === 'sstf';
        root.random = random;
        root.sync = () => { syncInputs(); run(); };
        run();
    },
};
