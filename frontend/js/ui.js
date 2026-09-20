import { clear, h, svg } from './dom.js';

// Deterministic per-process hue so P1 keeps its colour across every chart.
export function hueFor(id) {
    const match = /(\d+)$/.exec(String(id));
    const n = match ? Number(match[1]) : [...String(id)].reduce((a, c) => a + c.charCodeAt(0), 0);
    return Math.round((n * 137.508 + 200) % 360);
}

export const procStyle = (id) => ({ '--h': hueFor(id) });

export function badge(text, kind = 'neutral') {
    return h('span', { class: `badge badge-${kind}` }, text);
}

export function chip(id) {
    return h('span', { class: 'chip proc', style: procStyle(id) }, id);
}

export function metricTiles(items) {
    return h('div', { class: 'tiles' }, items.map(({ label, value, hint, tone }) =>
        h('div', { class: `tile ${tone ? `tile-${tone}` : ''}` },
            h('div', { class: 'tile-value' }, value),
            h('div', { class: 'tile-label' }, label),
            hint ? h('div', { class: 'tile-hint' }, hint) : null)));
}

export function table(headers, rows, { compact = true } = {}) {
    return h('div', { class: 'table-wrap' },
        h('table', { class: compact ? 'data compact' : 'data' },
            h('thead', null, h('tr', null, headers.map((t) => h('th', null, t)))),
            h('tbody', null, rows.map((row) =>
                h('tr', { class: row.className }, (row.cells || row).map((c) => h('td', null, c)))))));
}

export function card(title, body, { aside, id } = {}) {
    return h('section', { class: 'card', id },
        title ? h('header', { class: 'card-head' }, h('h3', null, title), aside || null) : null,
        h('div', { class: 'card-body' }, body));
}

export function field(label, control, hint) {
    return h('label', { class: 'field' },
        h('span', { class: 'field-label' }, label), control,
        hint ? h('span', { class: 'field-hint' }, hint) : null);
}

export function numberInput({ value, min, max, step = 1, onInput, width, label }) {
    return h('input', {
        type: 'number', value, min, max, step, inputmode: 'numeric', 'aria-label': label,
        style: width ? { width } : null,
        onInput: (e) => onInput && onInput(e.target.value === '' ? NaN : Number(e.target.value)),
    });
}

export function segmented(options, value, onChange, label) {
    const root = h('div', { class: 'segmented', role: 'radiogroup', 'aria-label': label });
    const buttons = new Map();
    const set = (next) => {
        for (const [key, btn] of buttons) {
            btn.setAttribute('aria-checked', String(key === next));
            btn.tabIndex = key === next ? 0 : -1;
        }
    };
    for (const opt of options) {
        const btn = h('button', {
            type: 'button', role: 'radio', title: opt.title,
            onClick: () => { set(opt.value); onChange(opt.value); },
            onKeydown: (e) => {
                const keys = options.map((o) => o.value);
                const i = keys.indexOf(opt.value);
                const delta = { ArrowRight: 1, ArrowDown: 1, ArrowLeft: -1, ArrowUp: -1 }[e.key];
                if (!delta) return;
                e.preventDefault();
                const next = keys[(i + delta + keys.length) % keys.length];
                set(next); onChange(next); buttons.get(next).focus();
            },
        }, opt.label);
        buttons.set(opt.value, btn);
        root.append(btn);
    }
    set(value);
    root.set = set;
    return root;
}

export function button(text, onClick, kind = 'secondary', attrs = {}) {
    return h('button', { type: 'button', class: `btn btn-${kind}`, onClick, ...attrs }, text);
}

// Inline error/notice area instead of alert() dialogs.
export function notice() {
    const el = h('div', { class: 'notice', role: 'status', 'aria-live': 'polite', hidden: true });
    el.show = (message) => { el.textContent = message; el.hidden = false; };
    el.hide = () => { el.hidden = true; };
    return el;
}

// Playback controller: play / pause / step / scrub across `count` frames (0..count).
export function player({ count, onFrame, initial = count, interval = 700 }) {
    let frame = initial;
    let timer = null;
    const slider = h('input', {
        type: 'range', min: 0, max: count, value: frame, 'aria-label': 'Playback position',
        onInput: (e) => { stop(); go(Number(e.target.value)); },
    });
    const label = h('span', { class: 'player-label' });
    const playBtn = h('button', { type: 'button', class: 'btn btn-secondary btn-sm', onClick: toggle }, 'Play');

    function go(next) {
        frame = Math.max(0, Math.min(count, next));
        slider.value = frame;
        label.textContent = `${frame} / ${count}`;
        onFrame(frame);
    }
    function stop() {
        clearInterval(timer);
        timer = null;
        playBtn.textContent = 'Play';
    }
    function toggle() {
        if (timer) return stop();
        if (frame >= count) go(0);
        playBtn.textContent = 'Pause';
        timer = setInterval(() => {
            if (frame >= count) return stop();
            go(frame + 1);
        }, interval);
    }
    const el = h('div', { class: 'player' },
        playBtn,
        h('button', { type: 'button', class: 'btn btn-secondary btn-sm', 'aria-label': 'Previous step',
            onClick: () => { stop(); go(frame - 1); } }, '‹'),
        h('button', { type: 'button', class: 'btn btn-secondary btn-sm', 'aria-label': 'Next step',
            onClick: () => { stop(); go(frame + 1); } }, '›'),
        slider, label);
    el.stop = stop;
    el.toggle = toggle;
    el.step = (d) => { stop(); go(frame + d); };
    go(frame);
    return el;
}

// Editable numeric matrix. `get()` returns rows of numbers; `set(values)` fills it.
export function matrixEditor({ title, rowLabel, colLabel, onChange }) {
    const grid = h('div', { class: 'matrix' });
    const root = h('div', { class: 'matrix-block' }, h('div', { class: 'matrix-title' }, title), grid);
    let rows = 0;
    let cols = 0;

    function build(r, c, values) {
        rows = r; cols = c;
        clear(grid);
        grid.style.setProperty('--cols', c + 1);
        grid.append(h('span'));
        for (let j = 0; j < c; j++) grid.append(h('span', { class: 'matrix-head' }, `${colLabel}${j + 1}`));
        for (let i = 0; i < r; i++) {
            grid.append(h('span', { class: 'matrix-head' }, `${rowLabel}${i + 1}`));
            for (let j = 0; j < c; j++) {
                grid.append(h('input', {
                    type: 'number', min: 0, value: values?.[i]?.[j] ?? 0, inputmode: 'numeric',
                    'aria-label': `${title} ${rowLabel}${i + 1} ${colLabel}${j + 1}`,
                    onInput: () => onChange && onChange(),
                }));
            }
        }
    }
    root.build = build;
    root.get = () => {
        const inputs = [...grid.querySelectorAll('input')].map((i) => (i.value === '' ? NaN : Number(i.value)));
        return Array.from({ length: rows }, (_, i) => inputs.slice(i * cols, (i + 1) * cols));
    };
    return root;
}

// Editable numeric vector (single row).
export function vectorEditor({ title, colLabel, onChange }) {
    const grid = h('div', { class: 'matrix' });
    const root = h('div', { class: 'matrix-block' }, h('div', { class: 'matrix-title' }, title), grid);
    let cols = 0;
    root.build = (c, values) => {
        cols = c;
        clear(grid);
        grid.style.setProperty('--cols', c);
        for (let j = 0; j < c; j++) grid.append(h('span', { class: 'matrix-head' }, `${colLabel}${j + 1}`));
        for (let j = 0; j < c; j++) {
            grid.append(h('input', {
                type: 'number', min: 0, value: values?.[j] ?? 0, inputmode: 'numeric',
                'aria-label': `${title} ${colLabel}${j + 1}`, onInput: () => onChange && onChange(),
            }));
        }
    };
    root.get = () => [...grid.querySelectorAll('input')].slice(0, cols)
        .map((i) => (i.value === '' ? NaN : Number(i.value)));
    return root;
}

export { svg };

// Replay the entrance animation on a results container (first render, or after Randomise).
export function replayEnter(el) {
    if (!el) return;
    el.classList.add('enter');
    clearTimeout(el._enterTimer);
    el._enterTimer = setTimeout(() => el.classList.remove('enter'), 1100);
}

// Download JSON as a file.
export function downloadJSON(name, data) {
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const a = h('a', { href: URL.createObjectURL(blob), download: name });
    document.body.append(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(a.href), 1000);
}
