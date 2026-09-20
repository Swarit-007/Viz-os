import { clear, h } from './dom.js';
import alloc from './views/alloc.js';
import banker from './views/banker.js';
import compare from './views/compare.js';
import cpu from './views/cpu.js';
import deadlock from './views/deadlock.js';
import disk from './views/disk.js';
import home from './views/home.js';
import paging from './views/paging.js';

const views = [home, cpu, disk, paging, alloc, banker, deadlock, compare];
const byId = new Map(views.map((v) => [v.id, v]));
const panels = new Map();

const nav = document.getElementById('nav');
const main = document.getElementById('view');
const heading = document.getElementById('view-title');
const blurb = document.getElementById('view-blurb');

function buildNav() {
    clear(nav).append(h('a', { href: '#/', class: 'nav-link', 'data-id': 'home' }, 'Overview'));
    for (const group of [...new Set(views.filter((v) => v.group).map((v) => v.group))]) {
        nav.append(h('div', { class: 'nav-group' }, group));
        for (const v of views.filter((x) => x.group === group)) {
            nav.append(h('a', { href: `#/${v.id}`, class: 'nav-link', 'data-id': v.id }, v.title));
        }
    }
}

function show(id) {
    const view = byId.get(id) || home;
    for (const link of nav.querySelectorAll('.nav-link')) {
        link.toggleAttribute('aria-current', link.dataset.id === view.id);
        if (link.dataset.id === view.id) link.setAttribute('aria-current', 'page');
    }
    for (const [key, panel] of panels) panel.hidden = key !== view.id;
    if (!panels.has(view.id)) {
        const panel = h('div', { class: 'panel' });
        main.append(panel);
        panels.set(view.id, panel);
        view.mount(panel, { views });
    } else if (panels.get(view.id).refresh) {
        panels.get(view.id).refresh();
    }
    heading.textContent = view.id === 'home' ? 'VizOS' : view.title;
    blurb.textContent = view.id === 'home' ? 'Operating-system algorithms, visualised.' : view.blurb;
    document.title = view.id === 'home' ? 'VizOS' : `${view.title} · VizOS`;
    document.body.classList.remove('nav-open');
    window.scrollTo(0, 0);
}

function route() {
    show(location.hash.replace(/^#\//, '') || 'home');
}

// Theme: follow the system until the user picks one.
const root = document.documentElement;
const stored = (() => { try { return localStorage.getItem('vizos-theme'); } catch (e) { return null; } })();
if (stored) root.dataset.theme = stored;
document.getElementById('theme-toggle').addEventListener('click', () => {
    const dark = root.dataset.theme
        ? root.dataset.theme === 'dark'
        : matchMedia('(prefers-color-scheme: dark)').matches;
    const next = dark ? 'light' : 'dark';
    root.dataset.theme = next;
    try { localStorage.setItem('vizos-theme', next); } catch (e) { /* storage unavailable */ }
});
document.getElementById('nav-toggle').addEventListener('click', () => document.body.classList.toggle('nav-open'));

buildNav();
addEventListener('hashchange', route);
route();
