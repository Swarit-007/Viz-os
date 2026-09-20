import { h } from '../dom.js';

export default {
    id: 'home',
    title: 'Overview',
    group: null,
    blurb: '',
    mount(root, { views }) {
        const tools = views.filter((v) => v.group);
        const groups = [...new Set(tools.map((v) => v.group))];
        root.append(
            h('p', { class: 'lede' }, 'Pick an algorithm, change the input, and watch it run. Every simulation is computed by the server and can be stepped through one move at a time.'),
            ...groups.map((g) => h('section', { class: 'home-group' },
                h('h2', null, g),
                h('div', { class: 'home-grid' }, tools.filter((v) => v.group === g).map((v) =>
                    h('a', { class: 'home-card', href: `#/${v.id}` }, h('strong', null, v.title), h('span', null, v.blurb)))))),
            h('section', { class: 'home-group' },
                h('h2', null, 'Keyboard'),
                h('p', { class: 'note' }, 'Use ← → on any algorithm picker to switch, and Tab to the playback slider to scrub through a run.')));
    },
};
