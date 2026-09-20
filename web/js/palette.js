import { getCatalog } from './api.js';
import { h, replace } from './dom.js';
import { icon } from './icons.js';

// Search palette (native <dialog>). Opens with "/" or Ctrl/Cmd+K.
export function createPalette(go) {
    const input = h('input', { type: 'search', placeholder: 'Search algorithms: scheduling, LRU, deadlock, RAID...', 'aria-label': 'Search algorithms', autocomplete: 'off' });
    const list = h('ul', { class: 'palette-list', role: 'listbox' });
    const dlg = h('dialog', { class: 'palette', 'aria-label': 'Search' }, h('div', { class: 'palette-input' }, icon('search'), input), list, h('p', { class: 'palette-hint' }, h('kbd', null, 'Up'), h('kbd', null, 'Down'), ' to move, ', h('kbd', null, 'Enter'), ' to open, ', h('kbd', null, 'Esc'), ' to close'));
    document.body.append(dlg);
    let items = [];
    let active = 0;
    let all = [];

    function score(a, q) {
        const hay = `${a.name} ${a.id} ${a.tags.join(' ')} ${a.category} ${a.summary}`.toLowerCase();
        return q.split(/\s+/).every((t) => hay.includes(t)) ? (a.name.toLowerCase().includes(q) ? 0 : 1) : 9;
    }
    function draw() {
        const q = input.value.trim().toLowerCase();
        items = (q ? all.filter((a) => score(a, q) < 9).sort((a, b) => score(a, q) - score(b, q)) : all).slice(0, 12);
        active = Math.min(active, Math.max(items.length - 1, 0));
        replace(list, items.length ? items.map((a, i) => h('li', { role: 'option', 'aria-selected': String(i === active), class: i === active ? 'on' : '', onClick: () => open(a), onMouseenter: () => { active = i; draw(); } },
            h('b', null, a.name), h('span', null, a.summary))) : h('li', { class: 'empty' }, 'Nothing matches. Try a broader word.'));
        list.querySelector('.on')?.scrollIntoView({ block: 'nearest' });
    }
    function open(a) { dlg.close(); go(a.id); }
    input.addEventListener('input', () => { active = 0; draw(); });
    input.addEventListener('keydown', (e) => {
        if (e.key === 'ArrowDown') { e.preventDefault(); active = Math.min(active + 1, items.length - 1); draw(); }
        else if (e.key === 'ArrowUp') { e.preventDefault(); active = Math.max(active - 1, 0); draw(); }
        else if (e.key === 'Enter' && items[active]) { e.preventDefault(); open(items[active]); }
    });
    dlg.addEventListener('click', (e) => { if (e.target === dlg) dlg.close(); });
    return { async show() { all = (await getCatalog()).algorithms; input.value = ''; active = 0; draw(); if (!dlg.open) dlg.showModal(); input.focus(); } };
}
