// form.js: builds an input form from a parameter schema sent by the server.
// The server describes each input ({type: 'int' | 'bool' | 'choice' | 'intlist' | 'lines' | 'table' | 'matrix' | 'vector', ...});
// this file turns that into DOM controls. Every field builder returns { el, get(), set(v), error() }:
//   el     the DOM node to show          get()    the current value        set(v)  replace the value
//   error  a message if the current text cannot be parsed, otherwise null
// buildForm() then combines the fields and exposes read() (all values or the first error) and set().

import { h, replace } from './dom.js';
import { icon } from './icons.js';
import { chip } from './util.js';

// Empty text becomes NaN (an error) rather than 0, so a blank cell is never silently treated as zero.
const toInt = (text) => (text.trim() === '' ? NaN : Number(text));

function numberInput(value, spec, onInput, label) {
    return h('input', { type: 'number', value, min: spec.min, max: spec.max, step: 1, inputmode: 'numeric', 'aria-label': label,
        onInput: (e) => onInput(toInt(e.target.value)) });
}

// ---- individual field builders: each returns { el, get(), set(value), error() } -------------------------
// ---- individual field builders ----------------------------------------------------------------------------
function intField(spec, change) {
    const input = numberInput(spec.default, spec, () => change(), spec.label);
    return { el: input, get: () => toInt(input.value), set: (v) => { input.value = v; }, error: () => (Number.isInteger(toInt(input.value)) ? null : `${spec.label} must be a whole number`) };
}

function boolField(spec, change) {
    const input = h('input', { type: 'checkbox', checked: spec.default, onChange: () => change() });
    return { el: h('label', { class: 'check' }, input, h('span', null, spec.label)), get: () => input.checked, set: (v) => { input.checked = !!v; }, error: () => null, bare: true };
}

// Up to four options show as a segmented button row; more become a drop-down.
function choiceField(spec, change) {
    let value = spec.default;
    let el;
    if (spec.options.length <= 4) {
        const buttons = spec.options.map((o) => h('button', { type: 'button', role: 'radio', class: 'seg', 'data-v': o.value, onClick: () => { set(o.value); change(); } }, o.label));
        el = h('div', { class: 'segmented', role: 'radiogroup', 'aria-label': spec.label }, buttons);
        var set = (v) => { value = v; buttons.forEach((b) => b.setAttribute('aria-checked', String(b.dataset.v === String(v)))); };
    } else {
        el = h('select', { 'aria-label': spec.label, onChange: (e) => { value = e.target.value; change(); } }, spec.options.map((o) => h('option', { value: o.value }, o.label)));
        var set = (v) => { value = v; el.value = v; };
    }
    set(value);
    return { el, get: () => value, set, error: () => null };
}

// A list of whole numbers typed as text, e.g. a page reference string '7 0 1 2 0 3'. Commas or spaces both work.
function intListField(spec, change) {
    const input = h('input', { type: 'text', spellcheck: 'false', 'aria-label': spec.label, onInput: () => change() });
    const parse = () => {
        const tokens = input.value.split(/[\s,]+/).filter(Boolean);
        const nums = tokens.map(Number);
        return nums.every(Number.isInteger) ? nums : null;
    };
    return { el: input, get: () => parse(), set: (v) => { input.value = v.join(' '); },
        error: () => { const v = parse(); if (!v) return `${spec.label}: whole numbers separated by spaces`; if (v.length < spec.minLen || v.length > spec.maxLen) return `${spec.label}: ${spec.minLen} to ${spec.maxLen} numbers`; return null; } };
}

// One value per line (for example 'alloc A 100'); blank lines are ignored.
function linesField(spec, change) {
    const area = h('textarea', { class: 'lines', rows: 5, spellcheck: 'false', placeholder: spec.placeholder || '', 'aria-label': spec.label, onInput: () => change() });
    return { el: area, get: () => area.value.split('\n').map((l) => l.trim()).filter(Boolean), set: (v) => { area.value = v.join('\n'); area.rows = Math.min(10, Math.max(4, v.length + 1)); }, error: () => null };
}

// An editable table (processes, segments, files). Row ids like P1, P2 are renumbered automatically when rows are removed.
function tableField(spec, change) {
    let rows = [];
    const body = h('div', { class: 'grid-table', style: { '--cols': spec.columns.length + 2 } });
    const root = h('div', { class: 'table-field' }, body);
    const add = h('button', { type: 'button', class: 'btn btn-quiet', disabled: false, onClick: () => { const r = {}; spec.columns.forEach((c) => { r[c.key] = c.kind === 'text' ? `seg${rows.length + 1}` : Math.max(c.min, 1); }); rows.push(r); draw(); change(); } }, icon('plus', 14), 'Add row');
    root.append(add);
    function draw() {
        rows.forEach((r, i) => { r.id = `${spec.idPrefix}${i + 1}`; });
        replace(body, h('span', { class: 'gt-head' }, ''), ...spec.columns.map((c) => h('span', { class: 'gt-head' }, c.label)), h('span', { class: 'gt-head' }, ''),
            ...rows.flatMap((r, i) => [
                spec.columns.some((c) => c.kind === 'text') ? h('span', { class: 'gt-id' }, r.id) : chip(r.id),
                ...spec.columns.map((c) => c.kind === 'text'
                    ? h('input', { type: 'text', value: r[c.key], 'aria-label': `${r.id} ${c.label}`, onInput: (e) => { r[c.key] = e.target.value.trim(); change(); } })
                    : numberInput(r[c.key], c, (v) => { r[c.key] = v; change(); }, `${r.id} ${c.label}`)),
                h('button', { type: 'button', class: 'icon-btn', 'aria-label': `Remove ${r.id}`, disabled: rows.length <= spec.minRows,
                    onClick: () => { rows.splice(i, 1); draw(); change(); } }, icon('x', 14))]));
        add.disabled = rows.length >= spec.maxRows;
    }
    return { el: root, get: () => rows.map((r) => ({ ...r })), set: (v) => { rows = v.map((r) => ({ ...r })); draw(); },
        error: () => rows.some((r) => spec.columns.some((c) => c.kind === 'int' && !Number.isInteger(r[c.key]))) ? `${spec.label}: every cell needs a whole number` : null };
}

// Editable matrix or vector of numbers. Its size follows other integer fields (for example 'processes' and 'resources'),
// so changing those resizes the grid and keeps the values that still fit.
function gridField(spec, change, sizes, vector) {
    let values = [];
    let r = 0;
    let c = 0;
    const grid = h('div', { class: 'matrix' });
    function fit() {
        const nr = vector ? 1 : Number(sizes(spec.rows));
        const nc = vector ? (typeof spec.length === 'string' ? Number(sizes(spec.length)) : spec.length) : Number(sizes(spec.cols));
        if (!Number.isInteger(nr) || !Number.isInteger(nc) || nr < 1 || nc < 1 || nr > 12 || nc > 12) return;
        if (nr === r && nc === c) return;
        values = Array.from({ length: nr }, (_, i) => Array.from({ length: nc }, (_, j) => values[i]?.[j] ?? 0));
        r = nr; c = nc;
        draw();
    }
    function draw() {
        grid.style.setProperty('--cols', c + 1);
        replace(grid, h('span'), ...Array.from({ length: c }, (_, j) => h('span', { class: 'mx-head' }, `R${j + 1}`)),
            ...values.flatMap((row, i) => [h('span', { class: 'mx-head' }, vector ? '' : `P${i + 1}`),
                ...row.map((v, j) => numberInput(v, spec, (n) => { values[i][j] = n; change(); }, `${spec.label} ${i + 1},${j + 1}`))]));
    }
    return { el: grid, fit, get: () => (vector ? values[0].slice() : values.map((row) => row.slice())),
        set: (v) => { values = vector ? [v.slice()] : v.map((row) => row.slice()); r = values.length; c = values[0].length; draw(); },
        error: () => values.flat().some((n) => !Number.isInteger(n)) ? `${spec.label}: fill every cell with a whole number` : null };
}

// ---- the form ---------------------------------------------------------------------------------------
// ---- the form ---------------------------------------------------------------------------------------------
// Create one field per schema entry. Any edit calls onChange (the page debounces it and re-runs the algorithm).
export function buildForm(schema, onChange) {
    const fields = new Map();
    const el = h('div', { class: 'form' });
    const sizes = (name) => fields.get(name)?.get();
    const change = (from) => { for (const f of fields.values()) if (f.fit) f.fit(); onChange(from); };
    for (const spec of schema) {
        let field;
        switch (spec.type) {
            case 'int': field = intField(spec, change); break;
            case 'bool': field = boolField(spec, change); break;
            case 'choice': field = choiceField(spec, change); break;
            case 'intlist': field = intListField(spec, change); break;
            case 'lines': field = linesField(spec, change); break;
            case 'table': field = tableField(spec, change); break;
            case 'matrix': field = gridField(spec, change, sizes, false); break;
            case 'vector': field = gridField(spec, change, sizes, true); break;
            default: throw new Error(`unknown field type ${spec.type}`);
        }
        fields.set(spec.name, field);
        el.append(field.bare ? h('div', { class: 'field field-bare' }, field.el, spec.hint ? h('small', null, spec.hint) : null)
            : h('label', { class: 'field' }, h('span', { class: 'field-label' }, spec.label), field.el, spec.hint ? h('small', null, spec.hint) : null));
    }
    return {
        el,
        set(values) {
            for (const spec of schema) if (values[spec.name] !== undefined) fields.get(spec.name).set(values[spec.name]);
            for (const f of fields.values()) if (f.fit) f.fit();
            for (const spec of schema) if (values[spec.name] !== undefined && (spec.type === 'matrix' || spec.type === 'vector')) fields.get(spec.name).set(values[spec.name]);
        },
        // { params } when every field parses, otherwise { error }
        read() {
            const params = {};
            for (const spec of schema) {
                const f = fields.get(spec.name);
                const err = f.error();
                if (err) return { error: err };
                params[spec.name] = f.get();
            }
            return { params };
        },
    };
}
