// home.js: the front page: headline, a live Round Robin demo, index tabs and the table of contents.
// The contents list is generated from the catalog, so new algorithms appear here automatically.

import { getCatalog, runAlgorithm } from './api.js';
import { h, replace, svg } from './dom.js';
import { icon } from './icons.js';
import { renderFigure } from './viz/index.js';

// A real (not faked) figure: it runs Round Robin on the server and loops through the steps as an animation.
// The loop stops itself when the home page is no longer on screen.
function demo() {
    const host = h('div', { class: 'demo-figure' });
    const cap = h('p', { class: 'caption' });
    runAlgorithm('rr', { processes: [{ id: 'P1', arrival: 0, burst: 5 }, { id: 'P2', arrival: 1, burst: 3 }, { id: 'P3', arrival: 2, burst: 4 }, { id: 'P4', arrival: 3, burst: 2 }], quantum: 2 }).then((res) => {
        let f = 0;
        const draw = () => { replace(host, renderFigure(res, f)); cap.textContent = f === 0 ? 'Round Robin, quantum 2: four processes take turns.' : res.steps[f - 1].note; };
        draw();
        if (matchMedia('(prefers-reduced-motion: reduce)').matches) { f = res.steps.length; draw(); return; }
        const timer = setInterval(() => {
            if (!host.isConnected) { clearInterval(timer); return; }
            f = f >= res.steps.length + 2 ? 0 : f + 1;
            draw();
        }, 900);
    }).catch(() => replace(host, h('p', { class: 'hint' }, 'Start the server to see the live demo.')));
    return h('figure', { class: 'figure hero-figure' }, h('div', { class: 'fig-frame' }, host), h('figcaption', null, h('span', { class: 'fig-num' }, 'Fig. 0'), cap));
}

// Group the catalog by chapter and number the entries continuously (01, 02, ...) like the contents of a book.
export async function mountHome(root, controller) {
    const catalog = await getCatalog();
    const total = catalog.algorithms.length;
    let counter = 0;
    const sections = catalog.categories.map((cat) => {
        const algs = catalog.algorithms.filter((a) => a.category === cat.id);
        return h('section', { class: 'toc-section', id: `cat-${cat.id}` },
            h('header', null, h('h2', null, cat.name), h('p', null, cat.blurb)),
            h('ol', { class: 'toc' }, algs.map((a) => { counter += 1; return h('li', null, h('a', { href: `#/a/${a.id}` }, h('span', { class: 'toc-num' }, String(counter).padStart(2, '0')), h('span', { class: 'toc-name' }, a.name),
                h('span', { class: 'toc-dots', 'aria-hidden': 'true' }), h('span', { class: 'toc-sum' }, a.summary))); })));
    });
    const tabs = h('nav', { class: 'index-tabs', 'aria-label': 'Jump to a chapter' }, catalog.categories.map((c, i) => h('a', { href: `#/#cat-${c.id}`, style: { '--tab': i }, onClick: (e) => { e.preventDefault(); document.getElementById(`cat-${c.id}`)?.scrollIntoView({ behavior: 'smooth', block: 'start' }); } }, c.name)));
    replace(root, h('section', { class: 'hero' },
        h('div', { class: 'hero-copy' }, h('h1', null, 'How machines ', h('span', { class: 'scribble' }, 'decide', svg('svg', { viewBox: '0 0 200 14', preserveAspectRatio: 'none', 'aria-hidden': 'true' }, svg('path', { d: 'M2 9 C 30 2, 60 12, 95 6 S 160 3, 198 8', fill: 'none' }))), '.'),
            h('p', { class: 'lede' }, `A laboratory notebook of ${total} operating-system algorithms. Change the numbers, press play, watch each one work.`),
            h('div', { class: 'btn-row' }, h('button', { type: 'button', class: 'btn btn-accent btn-lg', onClick: () => controller.surprise() }, icon('shuffle', 18), 'Open a random experiment'),
                h('button', { type: 'button', class: 'btn btn-lg', onClick: () => controller.search() }, icon('search', 18), 'Search', h('kbd', null, '/')))),
        demo()),
    tabs, h('div', { class: 'contents' }, h('h2', { class: 'contents-title' }, 'Contents'), ...sections));
    document.title = 'VizOS: how machines decide';
}
