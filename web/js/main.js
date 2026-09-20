import { getCatalog } from './api.js';
import { h, replace } from './dom.js';
import { icon } from './icons.js';
import { mountHome } from './home.js';
import { mountAlgorithm, toast } from './page.js';
import { createPalette } from './palette.js';

const view = document.getElementById('view');
const controller = {};
let token = 0;

const go = (id) => { location.hash = `#/a/${id}`; };
const palette = createPalette(go);
controller.search = () => palette.show();
controller.surprise = async () => {
    const { algorithms } = await getCatalog();
    go(algorithms[Math.floor(Math.random() * algorithms.length)].id);
};

async function route() {
    const mine = ++token;
    const hash = location.hash.replace(/^#/, '');
    const m = /^\/a\/([\w-]+)(?:\?p=(.+))?$/.exec(hash);
    for (const k of ['random', 'example', 'toggle', 'step', 'result']) delete controller[k];
    document.body.dataset.page = m ? 'algorithm' : 'home';
    replace(view, h('div', { class: 'loading', 'aria-busy': 'true' }, h('div', { class: 'sk sk-title' }), h('div', { class: 'sk sk-fig' })));
    try {
        const holder = h('div', { class: 'page' });
        if (m) await mountAlgorithm(holder, m[1], m[2], controller); else await mountHome(holder, controller);
        if (mine !== token) return;
        replace(view, holder);
        if (!m || !location.hash.includes('#cat-')) window.scrollTo(0, 0);
    } catch (e) {
        if (mine !== token) return;
        replace(view, h('div', { class: 'page' }, h('div', { class: 'notice' }, e.message), h('p', null, h('a', { href: '#/' }, 'Back to the contents'))));
    }
}

// theme: paper (light) or blueprint (dark), following the system until chosen
const root = document.documentElement;
try { const saved = localStorage.getItem('vizos-theme'); if (saved) root.dataset.theme = saved; } catch (e) { /* storage blocked */ }
const themeBtn = document.getElementById('theme-btn');
const isDark = () => (root.dataset.theme ? root.dataset.theme === 'dark' : matchMedia('(prefers-color-scheme: dark)').matches);
const paintTheme = () => { themeBtn.replaceChildren(icon(isDark() ? 'sun' : 'moon'), h('span', null, isDark() ? 'Paper' : 'Blueprint')); themeBtn.setAttribute('aria-label', isDark() ? 'Switch to paper theme' : 'Switch to blueprint theme'); };
themeBtn.addEventListener('click', () => { const next = isDark() ? 'light' : 'dark'; root.dataset.theme = next; try { localStorage.setItem('vizos-theme', next); } catch (e) { /* ignore */ } paintTheme(); });
matchMedia('(prefers-color-scheme: dark)').addEventListener('change', paintTheme);
paintTheme();
document.getElementById('search-btn').prepend(icon('search'));
document.getElementById('search-btn').addEventListener('click', () => controller.search());
document.getElementById('surprise-btn').prepend(icon('shuffle'));
document.getElementById('surprise-btn').addEventListener('click', () => controller.surprise());

addEventListener('keydown', (e) => {
    const t = e.target;
    const typing = ['INPUT', 'TEXTAREA', 'SELECT'].includes(t.tagName) || t.isContentEditable;
    if ((e.key === 'k' && (e.metaKey || e.ctrlKey)) || (e.key === '/' && !typing)) { e.preventDefault(); controller.search(); return; }
    if (typing || e.metaKey || e.ctrlKey || e.altKey || document.querySelector('dialog[open]')) return;
    if (e.key === 'r' && controller.random) { e.preventDefault(); controller.random(); }
    else if (e.key === 'e' && controller.example) { e.preventDefault(); controller.example(); }
    else if (e.key === ' ' && controller.toggle && t.tagName !== 'BUTTON') { e.preventDefault(); controller.toggle(); }
    else if (e.key === ']' && controller.step) controller.step(1);
    else if (e.key === '[' && controller.step) controller.step(-1);
});

addEventListener('hashchange', route);
route();
