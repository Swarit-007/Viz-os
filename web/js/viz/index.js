import { banker } from './banker.js';
import { curve } from './curve.js';
import { disk } from './disk.js';
import { frames } from './frames.js';
import { graph } from './graph.js';
import { grid } from './grid.js';
import { memory, partitions } from './memory.js';
import { inode, tree } from './misc.js';
import { buffer, philosophers, race, syncState } from './sync.js';
import { timeline } from './timeline.js';
import { multilevel, translate } from './translate.js';

const RENDERERS = { timeline, disk, frames, curve, grid, memory, partitions, banker, graph, philosophers, buffer, race, 'sync-state': syncState, translate, multilevel, inode, tree };

// cursor: timeline uses time; every other figure uses a zero-based index (-1 before the first step).
export function renderFigure(res, frame) {
    const draw = RENDERERS[res.viz];
    const step = frame > 0 ? res.steps[frame - 1] : null;
    const cursor = res.viz === 'timeline' ? (step ? step.at : 0) : (step ? step.at : -1);
    return draw(res, cursor);
}
export const hasPlayback = () => true;
