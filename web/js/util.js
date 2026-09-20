import { h } from './dom.js';

// A stable highlighter hue per process id, so P1 is the same colour in every figure.
export function hueFor(id) {
    const m = /(\d+)$/.exec(String(id));
    const n = m ? Number(m[1]) : [...String(id)].reduce((a, c) => a + c.charCodeAt(0), 0);
    const first = String(id).charCodeAt(0) || 0;
    return Math.round((n * 137.508 + first * 29 + 40) % 360);
}
export const ink = (id) => ({ '--h': hueFor(id) });

// Process id rendered as a highlighter-pen chip.
export const chip = (id) => h('span', { class: 'chip', style: ink(id) }, id);

export const fmt = (v) => (typeof v === 'number' && !Number.isInteger(v) ? v.toFixed(2) : v);

export function download(name, data) {
    const url = URL.createObjectURL(new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' }));
    const a = h('a', { href: url, download: name });
    document.body.append(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
}

// URL-safe base64 of JSON, for shareable links.
export const encodeState = (obj) => btoa(unescape(encodeURIComponent(JSON.stringify(obj)))).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
export function decodeState(text) {
    try {
        const b64 = text.replace(/-/g, '+').replace(/_/g, '/');
        return JSON.parse(decodeURIComponent(escape(atob(b64 + '='.repeat((4 - (b64.length % 4)) % 4)))));
    } catch (e) { return null; }
}
