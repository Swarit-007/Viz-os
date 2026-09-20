import { post } from '../api.js';
import { eventLog } from '../components.js';
import { clear, debounce, h, svg } from '../dom.js';
import { pseudocode } from '../pseudo.js';
import { badge, button, card, chip, field, metricTiles, notice, numberInput, player, segmented } from '../ui.js';

const int = (lo, hi) => lo + Math.floor(Math.random() * (hi - lo + 1));

/* ------------------------------------------------------------ dining philosophers */
const FORK_LINES = {
    naive: [['loop forever:', null], ['    think()', 'think'], ['    wait for left fork, pick it up', 'first'],
        ['    wait for right fork, pick it up', 'second'], ['    eat()', 'eat'], ['    put down both forks', 'release']],
    ordered: [['loop forever:', null], ['    think()', 'think'], ['    pick up the lower-numbered fork first', 'first'],
        ['    then pick up the higher-numbered fork', 'second'], ['    eat()', 'eat'], ['    put down both forks', 'release']],
    asymmetric: [['loop forever:', null], ['    think()', 'think'], ['    even philosopher: left fork first; odd: right fork first', 'first'],
        ['    then pick up the other fork', 'second'], ['    eat()', 'eat'], ['    put down both forks', 'release']],
    waiter: [['loop forever:', null], ['    think()', 'think'], ['    ask the waiter for a seat (at most n-1 seated)', 'seat'],
        ['    pick up left fork, then right fork', 'first'], ['    eat()', 'eat'], ['    put down both forks and leave the seat', 'release']],
};
const STRATEGY_NOTE = {
    naive: 'Everyone takes the left fork first. If all become hungry together each holds one fork and waits forever: deadlock.',
    ordered: 'Forks are numbered and always taken lowest first. This breaks the circular wait, so deadlock is impossible.',
    asymmetric: 'Odd philosophers reach right first. Two neighbours can never both hold one fork and wait on each other.',
    waiter: 'A waiter seats at most n-1 philosophers, so at least one can always get both forks.',
};

function tableSvg(snap, n) {
    const size = 360;
    const c = size / 2;
    const R = 132;
    const angle = (i) => -Math.PI / 2 + (i * 2 * Math.PI) / n;
    const at = (a, r) => [c + r * Math.cos(a), c + r * Math.sin(a)];
    const root = svg('svg', { class: 'chart table-svg', viewBox: `0 0 ${size} ${size}`, role: 'img', 'aria-label': 'Dining table' },
        svg('circle', { class: 'table-top', cx: c, cy: c, r: 96 }));
    snap.forks.forEach((f, k) => {
        const a = angle(k) - Math.PI / n;
        const owner = f.owner == null ? null : f.owner - 1;
        let [x, y] = at(a, 96);
        let [x2, y2] = at(a, 66);
        if (owner != null) {
            const [px, py] = at(angle(owner), R - 34);
            [x, y] = [x + (px - x) * 0.55, y + (py - y) * 0.55];
            [x2, y2] = [x2 + (px - x2) * 0.55, y2 + (py - y2) * 0.55];
        }
        root.append(svg('line', { class: `fork ${owner != null ? 'held' : ''}`, x1: x, y1: y, x2: x2, y2: y2 },
            svg('title', null, `Fork ${f.id}${owner != null ? ` held by P${owner + 1}` : ' free'}`)));
    });
    snap.philosophers.forEach((p, i) => {
        const [x, y] = at(angle(i), R);
        root.append(
            svg('circle', { class: `phil phil-${p.state} ${snap.deadlock ? 'phil-dead' : ''}`, cx: x, cy: y, r: 27 }),
            svg('text', { class: 'phil-label', x, y: y - 1, 'text-anchor': 'middle' }, `P${p.id}`),
            svg('text', { class: 'phil-sub', x, y: y + 13, 'text-anchor': 'middle' }, p.state === 'hungry' && p.holding.length ? 'waiting' : p.state));
    });
    return root;
}

function philosophersPanel() {
    let n = 5;
    let strategy = 'naive';
    let ticks = 40;
    let seed = 1;
    let allHungry = true;
    const errors = notice();
    const results = h('div', { class: 'results' });
    const note = h('p', { class: 'note' }, STRATEGY_NOTE[strategy]);
    const nInput = numberInput({ value: n, min: 2, max: 8, label: 'Philosophers', onInput: (v) => { n = v; run(); } });
    const seedInput = numberInput({ value: seed, min: 0, label: 'Seed', onInput: (v) => { seed = v; run(); } });
    const startBox = h('input', { type: 'checkbox', checked: allHungry, id: 'all-hungry', onChange: (e) => { allHungry = e.target.checked; run(); } });

    const run = debounce(async () => {
        try {
            const data = await post('/api/sync/philosophers', { n, strategy, ticks, seed, synchronized_start: allHungry });
            errors.hide();
            draw(data);
        } catch (e) { errors.show(e.message); }
    }, 200);

    function draw(data) {
        results.result = data;
        const lines = FORK_LINES[strategy];
        const code = pseudocode(lines.map((l) => l[0]));
        const boardHost = h('div', { class: 'board' });
        const log = h('ul', { class: 'tick-events' });
        const status = h('div', { class: 'now' });
        const total = data.steps.length;
        const onFrame = (i) => {
            const snap = data.steps[Math.max(i, 1) - 1];
            clear(boardHost).append(tableSvg(snap, data.n));
            clear(log).append(...(i === 0 ? [] : snap.events).map((e) => h('li', null, e)));
            clear(status).append(h('span', null, `tick ${i} of ${total}`),
                snap.deadlock && i === total ? badge('deadlock', 'bad') : null);
            const tags = new Set();
            if (i > 0) {
                for (const e of snap.events) {
                    if (/is hungry/.test(e)) tags.add('think');
                    if (/gets a seat|waits for a seat/.test(e)) tags.add('seat');
                    if (/and eats/.test(e)) { tags.add('second'); tags.add('eat'); }
                    else if (/holds fork/.test(e)) tags.add('second');
                    else if (/picks up fork|waits for fork/.test(e)) tags.add('first');
                    if (/puts down/.test(e)) tags.add('release');
                }
            }
            code.set(lines.map((l, idx) => (l[1] && tags.has(l[1]) ? idx : -1)).filter((x) => x >= 0));
        };
        const controls = player({ count: total, onFrame, interval: 650, initial: 0 });
        const meals = data.meals;
        const topMeals = Math.max(...meals, 1);
        clear(results).append(
            h('div', { class: `verdict ${data.deadlock ? 'verdict-bad' : 'verdict-good'}` },
                badge(data.deadlock ? 'Deadlock' : 'No deadlock', data.deadlock ? 'bad' : 'good'),
                h('span', null, data.deadlock
                    ? ` At tick ${data.deadlockTick} every philosopher holds one fork and waits for another. Nothing can progress.`
                    : ` ${data.totalMeals} meals eaten in ${total} ticks.`)),
            h('div', { class: 'playback' },
                card('Table', [boardHost, status, controls, log]),
                card('Pseudocode', code)),
            card('Meals per philosopher', h('div', { class: 'core-load' }, meals.map((m, i) => h('div', { class: 'load-row' },
                h('span', null, `P${i + 1}`),
                h('div', { class: 'load-track', role: 'img', 'aria-label': `${m} meals` }, h('div', { class: 'load-fill', style: { width: `${(m / topMeals) * 100}%` } })),
                h('b', null, m))))));
    }

    const picker = segmented(['naive', 'ordered', 'asymmetric', 'waiter'].map((v) => ({ value: v, label: v[0].toUpperCase() + v.slice(1) })),
        strategy, (v) => { strategy = v; note.textContent = STRATEGY_NOTE[v]; run(); }, 'Strategy');
    const controls = [
        card('Strategy', [picker, note]),
        card('Table', [
            field('Philosophers', nInput), field('Random seed', seedInput, 'Same seed, same run'),
            h('label', { class: 'check', for: 'all-hungry' }, startBox, 'Everyone gets hungry at tick 0'),
            h('div', { class: 'btn-row' }, button('New seed', () => { seed = int(1, 999); seedInput.value = seed; run(); }, 'ghost'))]),
        errors];
    return { controls, results, run, random: () => { n = int(3, 7); seed = int(1, 999); allHungry = Math.random() < 0.6; nInput.value = n; seedInput.value = seed; startBox.checked = allHungry; run(); } };
}

/* ------------------------------------------------------------ producer / consumer */
function bufferPanel() {
    let size = 4;
    let producers = 1;
    let consumers = 1;
    let pPeriod = 1;
    let cPeriod = 2;
    let synced = true;
    let seed = 1;
    const errors = notice();
    const results = h('div', { class: 'results' });
    const inputs = {
        size: numberInput({ value: size, min: 1, max: 20, label: 'Buffer size', onInput: (v) => { size = v; run(); } }),
        producers: numberInput({ value: producers, min: 1, max: 4, label: 'Producers', onInput: (v) => { producers = v; run(); } }),
        consumers: numberInput({ value: consumers, min: 1, max: 4, label: 'Consumers', onInput: (v) => { consumers = v; run(); } }),
        pPeriod: numberInput({ value: pPeriod, min: 1, max: 20, label: 'Producer period', onInput: (v) => { pPeriod = v; run(); } }),
        cPeriod: numberInput({ value: cPeriod, min: 1, max: 20, label: 'Consumer period', onInput: (v) => { cPeriod = v; run(); } }),
    };
    const syncBox = h('input', { type: 'checkbox', checked: synced, id: 'use-sem', onChange: (e) => { synced = e.target.checked; run(); } });

    const run = debounce(async () => {
        try {
            const data = await post('/api/sync/producer-consumer', {
                buffer_size: size, producers, consumers, producer_period: pPeriod, consumer_period: cPeriod, ticks: 40, seed, synchronized: synced });
            errors.hide();
            draw(data);
        } catch (e) { errors.show(e.message); }
    }, 200);

    function levelChart(data, upTo) {
        const W = 640; const H = 130; const pad = 26;
        const top = Math.max(data.bufferSize, ...data.steps.map((s) => s.buffer));
        const x = (i) => pad + (i / Math.max(data.steps.length - 1, 1)) * (W - pad - 8);
        const y = (v) => H - 20 - (v / top) * (H - 36);
        const root = svg('svg', { class: 'chart level', viewBox: `0 0 ${W} ${H}`, role: 'img', 'aria-label': 'Buffer level over time' });
        root.append(svg('line', { class: 'cap-line', x1: pad, x2: W - 8, y1: y(data.bufferSize), y2: y(data.bufferSize) }),
            svg('text', { class: 'tick-label', x: 2, y: y(data.bufferSize) + 4 }, data.bufferSize),
            svg('text', { class: 'tick-label', x: 8, y: y(0) + 4 }, 0));
        const pts = data.steps.slice(0, Math.max(upTo, 1)).map((s, i) => `${x(i)},${y(s.buffer)}`).join(' ');
        root.append(svg('polyline', { class: 'level-line', points: pts }));
        return root;
    }

    function draw(data) {
        results.result = data;
        const synced_ = data.synchronized;
        const lines = synced_
            ? [['producer: loop', 'p'], ['    item = produce()', 'p'], ['    wait(empty)', 'wait-empty'], ['    insert(item)', 'insert'], ['    signal(full)', 'p'],
                ['consumer: loop', 'c'], ['    wait(full)', 'wait-full'], ['    item = remove()', 'remove'], ['    signal(empty)', 'c']]
            : [['producer: loop', 'p'], ['    item = produce()', 'p'], ['    insert(item)   // no check', 'insert'],
                ['consumer: loop', 'c'], ['    item = remove()   // no check', 'remove']];
        const code = pseudocode(lines.map((l) => l[0]));
        const slots = h('div', { class: 'slots' });
        const chartHost = h('div', { class: 'chart-scroll' });
        const sems = h('div', { class: 'sems' });
        const log = h('ul', { class: 'tick-events' });
        const status = h('div', { class: 'now' });
        const total = data.steps.length;
        const onFrame = (i) => {
            const s = data.steps[Math.max(i, 1) - 1];
            const fill = i === 0 ? 0 : s.buffer;
            clear(slots).append(...Array.from({ length: Math.max(data.bufferSize, fill) }, (_, k) => h('span', {
                class: `slot ${k < fill ? 'full' : ''} ${k >= data.bufferSize ? 'over' : ''}` })));
            clear(sems).append(
                h('span', null, 'empty ', h('b', null, i === 0 ? data.bufferSize : s.empty)),
                h('span', null, 'full ', h('b', null, i === 0 ? 0 : s.full)),
                h('span', null, 'items ', h('b', null, `${fill}/${data.bufferSize}`)));
            clear(chartHost).append(levelChart(data, i));
            clear(log).append(...(i === 0 ? [] : s.events).map((e) => h('li', { class: /OVERFLOW|UNDERFLOW/.test(e) ? 'bad' : /blocks/.test(e) ? 'warn' : '' }, e)));
            clear(status).append(h('span', null, `tick ${i} of ${total}`));
            const tags = new Set();
            if (i > 0) {
                for (const e of s.events) {
                    if (/produces|inserts/.test(e)) { tags.add('insert'); tags.add('p'); }
                    if (/consumes|reads an empty/.test(e)) { tags.add('remove'); tags.add('c'); }
                    if (/wait\(empty\)/.test(e)) tags.add('wait-empty');
                    if (/wait\(full\)/.test(e)) tags.add('wait-full');
                }
            }
            const strong = new Set(['insert', 'remove', 'wait-empty', 'wait-full']);
            code.set(lines.map((l, idx) => (strong.has(l[1]) && tags.has(l[1]) ? idx : -1)).filter((x) => x >= 0));
        };
        const controls = player({ count: total, onFrame, interval: 380, initial: 0 });
        const broken = data.overflows + data.underflows > 0;
        clear(results).append(
            metricTiles([
                { label: 'Produced', value: data.produced }, { label: 'Consumed', value: data.consumed },
                { label: 'Overflows', value: data.overflows, tone: data.overflows ? 'bad' : undefined },
                { label: 'Underflows', value: data.underflows, tone: data.underflows ? 'bad' : undefined },
            ]),
            h('div', { class: `verdict ${broken ? 'verdict-bad' : 'verdict-good'}` },
                badge(broken ? 'Unsafe' : 'Safe', broken ? 'bad' : 'good'),
                h('span', null, broken
                    ? ' Without semaphores, producers overwrite a full buffer and consumers read an empty one.'
                    : ' Semaphores keep the buffer between 0 and its capacity. Blocked threads simply wait.')),
            h('div', { class: 'playback' },
                card('Bounded buffer', [slots, sems, chartHost, status, controls, log]),
                card('Pseudocode', code)));
    }

    const controls = [
        card('Buffer', [
            h('div', { class: 'grid-2' }, field('Buffer size', inputs.size), field('Producers', inputs.producers)),
            h('div', { class: 'grid-2' }, field('Consumers', inputs.consumers), field('Producer period', inputs.pPeriod, 'Ticks between items')),
            field('Consumer period', inputs.cPeriod, 'A slow consumer fills the buffer'),
            h('label', { class: 'check', for: 'use-sem' }, syncBox, 'Use semaphores'),
            h('div', { class: 'btn-row' }, button('New seed', () => { seed = int(1, 999); run(); }, 'ghost'))]),
        errors];
    return { controls, results, run, random: () => {
        size = int(2, 8); producers = int(1, 3); consumers = int(1, 3); pPeriod = int(1, 3); cPeriod = int(1, 4); seed = int(1, 999);
        Object.entries({ size, producers, consumers, pPeriod, cPeriod }).forEach(([k, v]) => { inputs[k].value = v; });
        run();
    } };
}

/* ------------------------------------------------------------ race condition */
function racePanel() {
    let threads = 2;
    let increments = 5;
    let useLock = false;
    let seed = 1;
    const errors = notice();
    const results = h('div', { class: 'results' });
    const tInput = numberInput({ value: threads, min: 2, max: 4, label: 'Threads', onInput: (v) => { threads = v; run(); } });
    const iInput = numberInput({ value: increments, min: 1, max: 20, label: 'Increments per thread', onInput: (v) => { increments = v; run(); } });
    const lockBox = h('input', { type: 'checkbox', checked: useLock, id: 'use-lock', onChange: (e) => { useLock = e.target.checked; run(); } });

    const run = debounce(async () => {
        try {
            const data = await post('/api/sync/race', { threads, increments, use_lock: useLock, seed });
            errors.hide();
            draw(data);
        } catch (e) { errors.show(e.message); }
    }, 200);

    function draw(data) {
        results.result = data;
        const lines = data.useLock
            ? ['acquire(lock)', 'load  reg, counter', 'add   reg, 1', 'store counter, reg', 'release(lock)']
            : ['load  reg, counter', 'add   reg, 1', 'store counter, reg'];
        const code = pseudocode(lines);
        const off = data.useLock ? 1 : 0;
        // lost update: a store that does not equal (counter before the store) + 1
        let before = 0;
        const rows = data.steps.map((s) => {
            const isStore = /^(acquire lock, )?store|store counter/.test(s.op);
            const lost = isStore && s.counter !== before + 1;
            before = s.counter;
            return { ...s, lost };
        });
        const table = h('ol', { class: 'events steps-list' }, rows.map((s) => h('li', { 'data-t': s.step },
            h('span', { class: 't' }, `#${s.step}`), chip(`P${s.thread}`), h('span', null, s.op),
            s.lost ? badge('lost update', 'bad') : null)));
        const counter = h('div', { class: 'big-counter' });
        const onFrame = (i) => {
            for (const li of table.children) li.classList.toggle('future', Number(li.dataset.t) > i);
            const cur = table.children[i - 1];
            for (const li of table.children) li.classList.remove('latest');
            if (cur) { cur.classList.add('latest'); table.scrollTop = Math.max(0, cur.offsetTop - table.clientHeight + cur.offsetHeight + 6); }
            const s = rows[i - 1];
            clear(counter).append(h('span', null, 'counter'), h('b', null, s ? s.counter : 0),
                h('small', null, `expected ${data.expected}`),
                s ? h('small', null, `registers ${s.registers.map((r, k) => `T${k + 1}=${r ?? '-'}`).join('  ')}`) : null);
            const op = s ? s.op : '';
            const which = /acquire/.test(op) && /load/.test(op) ? [0, 1] : /load/.test(op) ? [0 + off] : /add/.test(op) ? [1 + off] : /store/.test(op) ? (/release/.test(op) ? [2 + off, 3] : [2 + off]) : [];
            code.set(which.map((x) => x).filter((x) => x < lines.length));
        };
        const controls = player({ count: rows.length, onFrame, interval: 380, initial: 0 });
        clear(results).append(
            h('div', { class: `verdict ${data.lostUpdates ? 'verdict-bad' : 'verdict-good'}` },
                badge(data.lostUpdates ? 'Race condition' : 'Correct', data.lostUpdates ? 'bad' : 'good'),
                h('span', null, ` Final counter ${data.final}, expected ${data.expected}. ${data.lostUpdates ? `${data.lostUpdates} updates were lost.` : 'No update was lost.'}`)),
            h('div', { class: 'playback' },
                card('Interleaving', [counter, controls, table]),
                card('Each thread runs', code)));
    }

    const controls = [
        card('Threads', [
            h('p', { class: 'note' }, 'Every thread runs counter = counter + 1 several times. Without a lock the three instructions can interleave and overwrite each other.'),
            h('div', { class: 'grid-2' }, field('Threads', tInput), field('Increments each', iInput)),
            h('label', { class: 'check', for: 'use-lock' }, lockBox, 'Protect with a lock'),
            h('div', { class: 'btn-row' }, button('New schedule', () => { seed = int(1, 999); run(); }, 'ghost'))]),
        errors];
    return { controls, results, run, random: () => { threads = int(2, 4); increments = int(3, 8); seed = int(1, 999); tInput.value = threads; iInput.value = increments; run(); } };
}

export { tableSvg };

export default {
    id: 'sync',
    title: 'Synchronization',
    group: 'Processes',
    blurb: 'Dining philosophers, producer-consumer and a race condition.',
    mount(root) {
        const panels = { philosophers: philosophersPanel(), buffer: bufferPanel(), race: racePanel() };
        let current = 'philosophers';
        const stage = h('div', { class: 'split' });
        const controlsHost = h('div', { class: 'controls' });
        const resultsHost = h('div', { class: 'stack' });
        const picker = segmented([
            { value: 'philosophers', label: 'Dining philosophers' }, { value: 'buffer', label: 'Producer-consumer' },
            { value: 'race', label: 'Race condition' }], current, (v) => { show(v); }, 'Simulation');
        function show(v) {
            current = v;
            const panel = panels[v];
            clear(controlsHost).append(card('Simulation', picker), ...panel.controls);
            clear(resultsHost).append(panel.results);
            panel.run();
        }
        stage.append(controlsHost, resultsHost);
        root.append(stage);
        root.random = () => panels[current].random();
        root.sync = () => {};
        Object.defineProperty(root, 'result', { get: () => panels[current].results.result, set: () => {}, configurable: true });
        show(current);
    },
};
