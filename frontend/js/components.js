import { clear, h } from './dom.js';
import { icon } from './icons.js';
import { store } from './store.js';
import { button, chip, numberInput } from './ui.js';

// Editable process list shared by every CPU scheduling screen. Reads and writes store.processes.
export function processTable({ priority = true, onChange }) {
    const rows = h('div', { class: 'proc-rows' });
    const root = h('div', { class: 'proc-editor' }, rows);
    const renumber = () => store.processes.forEach((p, i) => { p.id = `P${i + 1}`; });

    function render() {
        clear(rows).append(h('div', { class: 'proc-row proc-head' },
            ...['Process', 'Arrival', 'Burst', 'Priority', ''].map((t) => h('span', null, t))));
        store.processes.forEach((p, i) => {
            rows.append(h('div', { class: 'proc-row' },
                chip(p.id),
                numberInput({ value: p.arrival, min: 0, max: 1000, label: `${p.id} arrival`, onInput: (v) => { p.arrival = v; onChange(); } }),
                numberInput({ value: p.burst, min: 1, max: 1000, label: `${p.id} burst`, onInput: (v) => { p.burst = v; onChange(); } }),
                numberInput({ value: p.priority, label: `${p.id} priority`, onInput: (v) => { p.priority = v; onChange(); } }),
                h('button', {
                    type: 'button', class: 'icon-btn', 'aria-label': `Remove ${p.id}`, title: 'Remove',
                    disabled: store.processes.length === 1,
                    onClick: () => { store.processes.splice(i, 1); renumber(); render(); onChange(); },
                }, icon('x'))));
        });
        rows.classList.toggle('no-priority', !priority);
    }
    root.render = render;
    root.setPriority = (on) => { priority = on; rows.classList.toggle('no-priority', !on); };
    root.add = () => {
        store.processes.push({ id: `P${store.processes.length + 1}`, arrival: 0, burst: 4, priority: 1 });
        render(); onChange();
    };
    root.addButton = button('Add process', root.add, 'secondary');
    render();
    return root;
}

// Are the processes valid for the API? Returns an error message or null.
export function processError(uses = {}) {
    const bad = store.processes.some((p) => !Number.isInteger(p.arrival) || p.arrival < 0 || p.arrival > 1000
        || !Number.isInteger(p.burst) || p.burst < 1 || p.burst > 1000 || !Number.isInteger(p.priority));
    return bad ? 'Arrival must be 0 to 1000, burst 1 to 1000, priority a whole number.' : null;
}

// Scrolling list of text events; `upTo(predicate)` highlights the latest visible entry.
export function eventLog(entries) {
    const list = h('ol', { class: 'events' }, entries.map((e) => h('li', { 'data-t': e.time }, e.node)));
    list.upTo = (t) => {
        let last = null;
        for (const li of list.children) {
            const visible = Number(li.dataset.t) <= t;
            li.classList.toggle('future', !visible);
            li.classList.remove('latest');
            if (visible) last = li;
        }
        if (last) { last.classList.add('latest'); list.scrollTop = Math.max(0, last.offsetTop - list.clientHeight + last.offsetHeight + 6); }
    };
    return list;
}
