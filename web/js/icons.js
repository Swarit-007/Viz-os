// icons.js: the icon set. Icons are tiny SVG paths drawn on a 20x20 grid with one stroke width, so no icon library is needed.

import { svg } from './dom.js';

// One icon set: 20px grid, 1.6 stroke, round caps. Drawn here so there is no icon dependency.
const PATHS = {
    play: 'M6.5 4.5v11l9-5.5z', pause: 'M7 4.5v11M13 4.5v11', prev: 'M12.5 4.5L7 10l5.5 5.5', next: 'M7.5 4.5L13 10l-5.5 5.5',
    first: 'M5 4.5v11M15 4.5L8.5 10 15 15.5', x: 'M5 5l10 10M15 5L5 15', plus: 'M10 4v12M4 10h12',
    shuffle: 'M3 6h3.2c1.3 0 2.4.6 3.1 1.6l1.4 2.8c.7 1 1.8 1.6 3.1 1.6H17M3 14h3.2c1.3 0 2.4-.6 3.1-1.6M12 6.2c.4-.1.8-.2 1.3-.2H17M14.5 3.5L17 6l-2.5 2.5M14.5 11.5L17 14l-2.5 2.5',
    download: 'M10 3.5v9M6.5 9.5L10 13l3.5-3.5M4 16.5h12', link: 'M8.5 11.5a3 3 0 004.2 0l2.6-2.6a3 3 0 00-4.2-4.2l-.8.8M11.5 8.5a3 3 0 00-4.2 0l-2.6 2.6a3 3 0 004.2 4.2l.8-.8',
    search: 'M9 3.5a5.5 5.5 0 100 11 5.5 5.5 0 000-11zM13 13l4 4', menu: 'M3.5 5.5h13M3.5 10h13M3.5 14.5h13',
    sun: 'M10 6.5a3.5 3.5 0 100 7 3.5 3.5 0 000-7zM10 2v2M10 16v2M2 10h2M16 10h2M4.3 4.3l1.4 1.4M14.3 14.3l1.4 1.4M4.3 15.7l1.4-1.4M14.3 5.7l1.4-1.4',
    moon: 'M16.5 11.8A6.8 6.8 0 018.2 3.5a6.8 6.8 0 108.3 8.3z', reset: 'M4 10a6 6 0 106-6H7M7 1.5L4.5 4 7 6.5', flask: 'M8 3h4M9 3v5l-4.5 7.5A1.5 1.5 0 005.8 18h8.4a1.5 1.5 0 001.3-2.5L11 8V3',
    arrow: 'M4 10h12M11 5l5 5-5 5', check: 'M4.5 10.5l3.5 3.5 7.5-8', book: 'M4 4.5A1.5 1.5 0 015.5 3H16v12H5.5A1.5 1.5 0 004 16.5zM4 16.5A1.5 1.5 0 005.5 18H16',
};

export function icon(name, size = 16) {
    return svg('svg', { class: 'icon', width: size, height: size, viewBox: '0 0 20 20', fill: 'none', stroke: 'currentColor', 'stroke-width': 1.6,
        'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'aria-hidden': 'true' }, svg('path', { d: PATHS[name] }));
}
