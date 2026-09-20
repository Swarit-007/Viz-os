// viz/index.js: maps a result's `viz` kind to the function that draws it.
//
// Every renderer has the signature  render(result, cursor) -> DOM node  and is a pure function of its inputs:
// the page calls it again for every playback frame instead of mutating the old drawing.
// `cursor` says how far the run has progressed. For 'timeline' it is a TIME value; for every other kind it is a
// zero-based index into result.data.snapshots / steps (-1 = before the first step).

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

// Add a new figure kind by writing a renderer and listing it here (tests check every viz used by the server is listed).
const RENDERERS = { timeline, disk, frames, curve, grid, memory, partitions, banker, graph, philosophers, buffer, race, 'sync-state': syncState, translate, multilevel, inode, tree };

// cursor: timeline uses time; every other figure uses a zero-based index (-1 before the first step).
// Convert the player's frame number into the cursor value described above, then draw.
export function renderFigure(res, frame) {
    const draw = RENDERERS[res.viz];
    const step = frame > 0 ? res.steps[frame - 1] : null;
    const cursor = res.viz === 'timeline' ? (step ? step.at : 0) : (step ? step.at : -1);
    return draw(res, cursor);
}
export const hasPlayback = () => true;
