import { compareFamily, getCatalog, randomParams, runAlgorithm } from './api.js';
import { debounce, h, replace } from './dom.js';
import { buildForm } from './form.js';
import { icon } from './icons.js';
import { player } from './player.js';
import { chip, decodeState, download, encodeState, fmt } from './util.js';
import { renderFigure } from './viz/index.js';

const session = new Map();   // last inputs per algorithm, so switching pages keeps your work
const reduceMotion = matchMedia('(prefers-reduced-motion: reduce)').matches;

function pseudocode(lines) {
    const list = h('ol', { class: 'procedure', 'aria-label': 'Procedure' }, lines.map((t, i) => h('li', { 'data-i': i }, h('code', null, t.replace(/^ +/, (m) => ' '.repeat(m.length))))));
    list.mark = (active = []) => { const on = new Set(active); [...list.children].forEach((li, i) => { li.classList.toggle('on', on.has(i)); if (on.has(i)) li.setAttribute('aria-current', 'step'); else li.removeAttribute('aria-current'); }); };
    return list;
}

function measurements(res) {
    return h('dl', { class: 'measure' }, res.summary.flatMap((t) => [h('dt', null, t.label, t.hint ? h('small', null, ` ${t.hint}`) : null), h('dd', { class: t.tone ? `tone-${t.tone}` : '' }, fmt(t.value))]));
}

function dataTable(t) {
    return h('div', { class: 'table-wrap' }, h('table', { class: 'data' }, h('thead', null, h('tr', null, t.headers.map((c) => h('th', null, c)))),
        h('tbody', null, t.rows.map((row) => h('tr', null, row.map((cell) => h('td', null, cell && typeof cell === 'object' ? chip(cell.proc) : fmt(cell))))))));
}

export async function mountAlgorithm(root, id, hashParams, controller) {
    const catalog = await getCatalog();
    const alg = catalog.byId.get(id);
    if (!alg) { replace(root, h('p', { class: 'lede' }, `There is no algorithm called “${id}”.`), h('a', { href: '#/', class: 'btn' }, 'Back to the contents')); return; }
    const number = catalog.algorithms.indexOf(alg) + 1;
    const category = catalog.categories.find((c) => c.id === alg.category);
    const siblings = catalog.algorithms.filter((a) => a.category === alg.category);
    const at = siblings.indexOf(alg);

    const figure = h('div', { class: 'figure-body' });
    const caption = h('p', { class: 'caption' });
    const playerHost = h('div', { class: 'player-host' });
    const summaryHost = h('div', { class: 'summary-host' });
    const verdictHost = h('div', { class: 'verdict-host' });
    const tableHost = h('div', { class: 'table-host' });
    const compareHost = h('section', { class: 'compare-host' });
    const error = h('div', { class: 'notice', role: 'alert', hidden: true });
    const procedure = pseudocode(alg.pseudocode);
    let res = null;
    let pl = null;
    let seq = 0;
    let animate = true;

    const form = buildForm(alg.params, () => schedule());

    function showFrame(f) {
        replace(figure, renderFigure(res, f));
        const step = f > 0 ? res.steps[f - 1] : null;
        caption.textContent = step ? step.note : 'Press play, or drag the slider, to step through this run.';
        procedure.mark(step ? step.lines : []);
    }

    async function run(restart) {
        const read = form.read();
        if (read.error) { error.textContent = read.error; error.hidden = false; return; }
        const mine = ++seq;
        try {
            const out = await runAlgorithm(id, read.params);
            if (mine !== seq) return;
            error.hidden = true;
            res = out;
            session.set(id, read.params);
            history.replaceState(null, '', `#/a/${id}?p=${encodeState(read.params)}`);
            pl?.stop();
            pl = player({ count: res.steps.length, onFrame: showFrame, initial: restart && !reduceMotion ? 0 : res.steps.length });
            replace(playerHost, pl);
            replace(summaryHost, measurements(res));
            replace(verdictHost, res.verdict ? h('div', { class: `stamp-box ${res.verdict.ok ? 'ok' : 'bad'}` }, h('b', null, res.verdict.label), h('span', null, res.verdict.text)) : null);
            replace(tableHost, res.table ? h('section', { class: 'results' }, h('h3', null, res.table.title), dataTable(res.table)) : null);
            if (restart && !reduceMotion) pl.play();
            controller.result = res;
        } catch (e) {
            if (mine !== seq) return;
            error.textContent = e.message;
            error.hidden = false;
        }
    }
    const schedule = debounce(() => run(false), 220);

    async function useParams(params, restart = true) { form.set(params); await run(restart); }
    const example = () => useParams(alg.example);
    const random = async () => { try { const { params } = await randomParams(id); await useParams(params); } catch (e) { error.textContent = e.message; error.hidden = false; } };
    Object.assign(controller, { random, example, toggle: () => pl?.toggle(), step: (d) => pl?.step(d), result: null });

    // ---- compare ("race the family") ----
    const canCompare = alg.family && catalog.compare.includes(alg.family);
    async function race() {
        const read = form.read();
        if (read.error) return;
        replace(compareHost, h('h2', null, 'The family, side by side'), h('p', { class: 'hint' }, 'Running every algorithm on your input...'));
        try {
            const out = await compareFamily(alg.family, read.params);
            const max = Math.max(...out.results.map((r) => Number(r.value)), 1);
            replace(compareHost, h('h2', null, 'The family, side by side'), h('p', { class: 'hint' }, `Same input for everyone. Ranked by ${out.metric.toLowerCase()} (${out.lowerIsBetter ? 'lower' : 'higher'} is better). The winner is underlined in red pen.`),
                h('ol', { class: 'race' }, [...out.results].sort((a, b) => (out.lowerIsBetter ? a.value - b.value : b.value - a.value)).map((r) => h('li', { class: r.best ? 'best' : '' },
                    h('a', { href: `#/a/${r.id}` }, r.name), h('div', { class: 'race-bar' }, h('div', { class: 'race-fill', style: { width: `${Math.max(2, (Number(r.value) / max) * 100)}%` } })), h('b', null, fmt(r.value))))));
        } catch (e) { replace(compareHost, h('h2', null, 'The family, side by side'), h('div', { class: 'notice' }, e.message)); }
    }

    // ---- layout ----
    replace(root,
        h('article', { class: 'experiment' },
            h('header', { class: 'exp-head' },
                h('nav', { class: 'crumbs', 'aria-label': 'Breadcrumb' }, h('a', { href: '#/' }, 'Contents'), h('span', null, '/'), h('span', null, category.name)),
                h('h1', null, alg.name), h('p', { class: 'deck' }, alg.summary),
                h('div', { class: 'tags' }, alg.tags.map((t) => h('span', { class: 'tag' }, t)))),
            h('div', { class: 'exp-grid' },
                h('div', { class: 'exp-main' },
                    h('figure', { class: 'figure' }, h('div', { class: 'fig-frame' }, figure), h('figcaption', null, h('span', { class: 'fig-num' }, `Fig. ${number}`), caption), playerHost),
                    verdictHost, h('section', { class: 'measurements' }, h('h3', null, 'Measurements'), summaryHost), tableHost,
                    canCompare ? h('div', { class: 'compare-cta' }, h('button', { type: 'button', class: 'btn', onClick: race }, icon('flask'), 'Race the whole family on this input')) : null, compareHost,
                    h('nav', { class: 'pager' }, at > 0 ? h('a', { href: `#/a/${siblings[at - 1].id}` }, h('small', null, 'Previous'), siblings[at - 1].name) : h('span'),
                        at < siblings.length - 1 ? h('a', { class: 'next', href: `#/a/${siblings[at + 1].id}` }, h('small', null, 'Next'), siblings[at + 1].name) : h('span'))),
                h('aside', { class: 'exp-aside' },
                    h('section', { class: 'card setup' }, h('div', { class: 'card-head' }, h('h2', null, 'Setup'),
                        h('div', { class: 'btn-row' }, h('button', { type: 'button', class: 'btn btn-accent', title: 'New random input (R)', onClick: random }, icon('shuffle'), 'Randomise'),
                            h('button', { type: 'button', class: 'btn btn-quiet', title: 'Textbook example (E)', onClick: example }, icon('reset'), 'Example'))),
                        form.el, error,
                        h('div', { class: 'btn-row tools' }, h('button', { type: 'button', class: 'btn btn-quiet', onClick: async () => { try { await navigator.clipboard.writeText(location.href); toast('Link copied'); } catch (e) { toast('Copy the address bar to share'); } } }, icon('link', 14), 'Copy link'),
                            h('button', { type: 'button', class: 'btn btn-quiet', onClick: () => res && download(`vizos-${id}.json`, res) }, icon('download', 14), 'Export JSON'))),
                    h('section', { class: 'card' }, h('div', { class: 'card-head' }, h('h2', null, 'Procedure')), procedure),
                    h('section', { class: 'card notes' }, h('div', { class: 'card-head' }, h('h2', null, 'Field notes')),
                        h('dl', { class: 'complexity' }, h('dt', null, 'Time'), h('dd', null, alg.complexity.time), h('dt', null, 'Space'), h('dd', null, alg.complexity.space)),
                        alg.complexity.note ? h('p', { class: 'hint' }, alg.complexity.note) : null, h('ul', null, alg.notes.map((n) => h('li', null, n))))))));

    const start = hashParams ? decodeState(hashParams) : null;
    await useParams(start || session.get(id) || alg.example, !start);
    document.title = `${alg.name} · VizOS`;
}

let toastTimer;
export function toast(text) {
    let el = document.getElementById('toast');
    if (!el) { el = h('div', { id: 'toast', role: 'status' }); document.body.append(el); }
    el.textContent = text;
    el.classList.add('show');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => el.classList.remove('show'), 1800);
}
