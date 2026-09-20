// Tiny DOM helpers. All text goes through text nodes, so no HTML is ever parsed from data.

const SVG_NS = 'http://www.w3.org/2000/svg';

function apply(el, attrs) {
    for (const [key, value] of Object.entries(attrs || {})) {
        if (value == null || value === false) continue;
        if (key === 'class') el.setAttribute('class', value);
        else if (key === 'style' && typeof value === 'object') {
            for (const [prop, v] of Object.entries(value)) {
                prop.startsWith('--') ? el.style.setProperty(prop, v) : (el.style[prop] = v);
            }
        } else if (key.startsWith('on') && typeof value === 'function') {
            el.addEventListener(key.slice(2).toLowerCase(), value);
        } else if (key === 'value' && 'value' in el) el.value = value;
        else el.setAttribute(key, value === true ? '' : value);
    }
}

function append(el, children) {
    for (const child of children.flat(Infinity)) {
        if (child == null || child === false) continue;
        el.append(child instanceof Node ? child : document.createTextNode(String(child)));
    }
}

export function h(tag, attrs, ...children) {
    const el = document.createElement(tag);
    apply(el, attrs);
    append(el, children);
    return el;
}

export function svg(tag, attrs, ...children) {
    const el = document.createElementNS(SVG_NS, tag);
    apply(el, attrs);
    append(el, children);
    return el;
}

// Empty an element. Its append() is replaced with a version that skips null, false and nested arrays,
// so views can write `clear(el).append(cond ? node : null)` without printing "null".
export function clear(el) {
    while (el.firstChild) el.removeChild(el.firstChild);
    if (!el._safeAppend) {
        el._safeAppend = true;
        const native = Element.prototype.append;
        el.append = (...children) => native.call(el, ...children.flat(Infinity)
            .filter((c) => c != null && c !== false).map((c) => (c instanceof Node ? c : String(c))));
    }
    return el;
}

export function debounce(fn, ms) {
    let timer;
    return (...args) => {
        clearTimeout(timer);
        timer = setTimeout(() => fn(...args), ms);
    };
}
