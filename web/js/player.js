// player.js: the playback bar under every figure (first, previous, play/pause, next, slider, speed).
// A run has `count` steps, so the player has frames 0..count: frame 0 is 'before anything happened' and frame n shows
// the state after step n. Each frame change calls onFrame(frame); the page redraws the figure and pseudocode from it.

import { h } from './dom.js';
import { icon } from './icons.js';

// Playback bar: frames run 0..count. onFrame(frame) redraws the figure.
// `initial` is the starting frame. Pages start at the last frame (a finished picture) or at 0 when they auto-play.
export function player({ count, onFrame, initial = count }) {
    let frame = initial;
    let timer = null;
    let speed = 1;
    const slider = h('input', { type: 'range', min: 0, max: count, value: frame, 'aria-label': 'Step', onInput: (e) => { stop(); go(Number(e.target.value)); } });
    const label = h('output', { class: 'player-count' });
    const playBtn = h('button', { type: 'button', class: 'btn btn-icon', 'aria-label': 'Play', title: 'Play or pause (Space)', onClick: () => toggle() }, icon('play'));
    const rate = h('select', { 'aria-label': 'Speed', onChange: (e) => { speed = Number(e.target.value); if (timer) { stop(); toggle(true); } } },
        [['0.5', '0.5x'], ['1', '1x'], ['2', '2x'], ['4', '4x']].map(([v, t]) => h('option', { value: v, selected: v === '1' }, t)));

    function go(n) {
        frame = Math.max(0, Math.min(count, n));
        slider.value = frame;
        label.textContent = `${frame} / ${count}`;
        onFrame(frame);
    }
    function stop() {
        clearInterval(timer);
        timer = null;
        playBtn.replaceChildren(icon('play'));
        playBtn.setAttribute('aria-label', 'Play');
    }
    // Play or pause. Pressing play on the last frame restarts from the beginning.
    function toggle(resume = false) {
        if (timer) { stop(); return; }
        if (frame >= count && !resume) go(0);
        playBtn.replaceChildren(icon('pause'));
        playBtn.setAttribute('aria-label', 'Pause');
        timer = setInterval(() => { if (frame >= count) { stop(); return; } go(frame + 1); }, 650 / speed);
    }
    const el = h('div', { class: 'player' },
        h('button', { type: 'button', class: 'btn btn-icon', 'aria-label': 'Back to start', onClick: () => { stop(); go(0); } }, icon('first')),
        h('button', { type: 'button', class: 'btn btn-icon', 'aria-label': 'Previous step', title: 'Previous ([)', onClick: () => { stop(); go(frame - 1); } }, icon('prev')),
        playBtn,
        h('button', { type: 'button', class: 'btn btn-icon', 'aria-label': 'Next step', title: 'Next (])', onClick: () => { stop(); go(frame + 1); } }, icon('next')),
        slider, label, rate);
    // Expose controls so keyboard shortcuts in main.js can drive the player.
    Object.assign(el, { toggle: () => toggle(), step: (d) => { stop(); go(frame + d); }, go, stop, play: () => { if (!timer) { go(0); toggle(true); } } });
    go(frame);
    return el;
}
