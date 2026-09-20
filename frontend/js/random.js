// Random input generators. Every view uses these so "Randomise" behaves the same everywhere.
const int = (lo, hi) => lo + Math.floor(Math.random() * (hi - lo + 1));

export function randomProcesses() {
    const n = int(4, 7);
    return Array.from({ length: n }, (_, i) => ({
        id: `P${i + 1}`, arrival: int(0, 8), burst: int(1, 10), priority: int(1, 5),
    }));
}

export function randomPages() {
    const length = int(14, 22);
    const range = int(4, 8);
    // Bias toward recently used pages so LRU and FIFO actually differ.
    const pages = [];
    for (let i = 0; i < length; i++) {
        pages.push(i > 2 && Math.random() < 0.35 ? pages[i - int(1, 3)] : int(0, range));
    }
    return { pages, frames: int(3, 4) };
}

export function randomDisk() {
    const size = [100, 200, 256][int(0, 2)];
    return {
        size,
        head: int(0, size - 1),
        direction: Math.random() < 0.5 ? 'up' : 'down',
        requests: Array.from({ length: int(6, 10) }, () => int(0, size - 1)),
    };
}

export function randomMemory() {
    return {
        blocks: Array.from({ length: int(4, 6) }, () => int(4, 60) * 10),
        procs: Array.from({ length: int(4, 6) }, () => int(4, 55) * 10),
    };
}

// Banker's: allocation <= max always holds. `available` is drawn small so both safe and unsafe states occur.
export function randomBanker(n = int(3, 5), m = int(2, 4)) {
    const allocation = Array.from({ length: n }, () => Array.from({ length: m }, () => int(0, 3)));
    const max = allocation.map((row) => row.map((a) => a + int(0, 5)));
    return { n, m, allocation, max, available: Array.from({ length: m }, () => int(0, 4)) };
}

export function randomDeadlock(n = int(3, 5), m = int(2, 3)) {
    const allocation = Array.from({ length: n }, () => Array.from({ length: m }, () => int(0, 2)));
    const request = Array.from({ length: n }, () => Array.from({ length: m }, () => (Math.random() < 0.4 ? int(1, 2) : 0)));
    return { n, m, allocation, request, available: Array.from({ length: m }, () => int(0, 1)) };
}
