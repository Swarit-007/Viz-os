// Tiny DOM helpers. Text always goes through text nodes, so no HTML is ever parsed from data.
const SVG_NS = 'http://www.w3.org/2000/svg';

function apply(el, attrs) {
    for (const [key, value] of Object.entries(attrs || {})) {
        if (value == null || value === false) continue;
        if (key === 'class') el.setAttribute('class', value);
        else if (key === 'style' && typeof value === 'object') {
            for (const [prop, v] of Object.entries(value)) {
                if (prop.startsWith('--')) el.style.setProperty(prop, v); else el.style[prop] = v;
            }
        } else if (key.startsWith('on') && typeof value === 'function') el.addEventListener(key.slice(2).toLowerCase(), value);
        else if (key === 'value' && 'value' in el) el.value = value;
        else if (key === 'checked' && 'checked' in el) el.checked = !!value;
        else el.setAttribute(key, value === true ? '' : value);
    }
}

function append(el, children) {
    for (const child of children.flat(Infinity)) {
        if (child == null || child === false) continue;
        el.append(child instanceof Node ? child : document.createTextNode(String(child)));
    }
}

// h('div', {class: 'x'}, child, child) builds an element. Strings become text nodes, so data can never inject HTML.
export function h(tag, attrs, ...children) {
    const el = document.createElement(tag);
    apply(el, attrs);
    append(el, children);
    return el;
}

// Same as h() but creates SVG elements (they need the SVG namespace to render).
export function svg(tag, attrs, ...children) {
    const el = document.createElementNS(SVG_NS, tag);
    apply(el, attrs);
    append(el, children);
    return el;
}

// Empty an element and fill it with new children.
export function replace(el, ...children) {
    el.replaceChildren();
    append(el, children);
    return el;
}

// Delay fn until `ms` after the last call; wrapped.cancel() drops a pending call.
export function debounce(fn, ms) {
    let timer;
    const wrapped = (...args) => { clearTimeout(timer); timer = setTimeout(() => fn(...args), ms); };
    wrapped.cancel = () => clearTimeout(timer);
    return wrapped;
}

export const clamp = (v, lo, hi) => Math.max(lo, Math.min(hi, v));
