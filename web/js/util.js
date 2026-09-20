// util.js: small helpers shared by many files (colours for process ids, number formatting, downloads, share links).

import { h } from './dom.js';

// A stable highlighter hue per process id, so P1 is the same colour in every figure.
// Map a process id to a hue (0-360). The same id always gets the same colour in every figure, which lets you follow
// P3 from the timeline to the table. 137.508 degrees is the golden angle, so consecutive ids land far apart on the colour wheel.
export function hueFor(id) {
    const m = /(\d+)$/.exec(String(id));
    const n = m ? Number(m[1]) : [...String(id)].reduce((a, c) => a + c.charCodeAt(0), 0);
    const first = String(id).charCodeAt(0) || 0;
    return Math.round((n * 137.508 + first * 29 + 40) % 360);
}
// CSS custom property carrying the hue. Stylesheets turn it into a highlighter-pen colour: hsl(var(--h) ...).
export const ink = (id) => ({ '--h': hueFor(id) });

// Process id rendered as a highlighter-pen chip.
// A process id drawn as a small highlighter-marked label.
export const chip = (id) => h('span', { class: 'chip', style: ink(id) }, id);

// Show integers as they are and other numbers with two decimals.
export const fmt = (v) => (typeof v === 'number' && !Number.isInteger(v) ? v.toFixed(2) : v);

// Save `data` as a JSON file by clicking a temporary link (no server round trip).
export function download(name, data) {
    const url = URL.createObjectURL(new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' }));
    const a = h('a', { href: url, download: name });
    document.body.append(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
}

// URL-safe base64 of JSON, for shareable links.
// Share links keep your inputs in the URL: JSON -> URL-safe base64 (and back with decodeState). No server storage needed.
export const encodeState = (obj) => btoa(unescape(encodeURIComponent(JSON.stringify(obj)))).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
export function decodeState(text) {
    try {
        const b64 = text.replace(/-/g, '+').replace(/_/g, '/');
        return JSON.parse(decodeURIComponent(escape(atob(b64 + '='.repeat((4 - (b64.length % 4)) % 4)))));
    } catch (e) { return null; }
}
