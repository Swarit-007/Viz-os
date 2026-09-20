// Inputs shared between views so the Compare view can reuse what you configured elsewhere.
export const store = {
    processes: [
        { id: 'P1', arrival: 0, burst: 8, priority: 3 },
        { id: 'P2', arrival: 1, burst: 4, priority: 1 },
        { id: 'P3', arrival: 2, burst: 9, priority: 4 },
        { id: 'P4', arrival: 3, burst: 5, priority: 2 },
    ],
    quantum: 3,
    frames: 3,
    pages: [7, 0, 1, 2, 0, 3, 0, 4, 2, 3, 0, 3, 2, 1, 2, 0, 1, 7, 0, 1],
    disk: { requests: [98, 183, 37, 122, 14, 124, 65, 67], head: 53, size: 200, direction: 'up' },
};

// Parse "1 2, 3" style input into integers; returns null when any token is not a whole number.
export function parseInts(text) {
    const tokens = text.split(/[\s,]+/).filter(Boolean);
    const numbers = tokens.map(Number);
    return numbers.every(Number.isInteger) ? numbers : null;
}
