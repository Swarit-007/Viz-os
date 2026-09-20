// Page Replacement Algorithms - FIFO and LRU
class PageReplacement {
    static simulate(algorithm, frames, pageRequests) {
        if (algorithm === 'fifo') {
            return this.simulateFIFO(frames, pageRequests);
        } else if (algorithm === 'lru') {
            return this.simulateLRU(frames, pageRequests);
        }
        throw new Error('Unknown algorithm: ' + algorithm);
    }

    static simulateFIFO(frames, pageRequests) {
        const memory = [];
        let pageFaults = 0;
        const steps = [];

        for (let i = 0; i < pageRequests.length; i++) {
            const page = pageRequests[i];
            const step = {
                step: i + 1,
                requestedPage: page,
                memoryBefore: [...memory],
                pageFault: false,
                replacedPage: null,
                memoryAfter: null,
                description: ''
            };

            if (!memory.includes(page)) {
                pageFaults++;
                step.pageFault = true;

                if (memory.length < frames) {
                    memory.push(page);
                    step.description = `Page ${page} added to memory (memory not full)`;
                } else {
                    const replaced = memory.shift();
                    memory.push(page);
                    step.replacedPage = replaced;
                    step.description = `Page fault: Replaced page ${replaced} with page ${page} (FIFO)`;
                }
            } else {
                step.description = `Page ${page} already in memory, no page fault`;
            }

            step.memoryAfter = [...memory];
            steps.push(step);
        }

        return {
            success: true,
            algorithm: 'FIFO',
            frames: frames,
            pageRequests: pageRequests,
            totalPageFaults: pageFaults,
            steps: steps,
            finalMemory: memory
        };
    }

    static simulateLRU(frames, pageRequests) {
        const memory = [];
        const pageAccessOrder = {};
        let pageFaults = 0;
        const steps = [];

        for (let i = 0; i < pageRequests.length; i++) {
            const page = pageRequests[i];
            const step = {
                step: i + 1,
                requestedPage: page,
                memoryBefore: [...memory],
                pageFault: false,
                replacedPage: null,
                memoryAfter: null,
                description: ''
            };

            if (!memory.includes(page)) {
                pageFaults++;
                step.pageFault = true;

                if (memory.length < frames) {
                    memory.push(page);
                    step.description = `Page ${page} added to memory (memory not full)`;
                } else {
                    // Find LRU page
                    let lruPage = null;
                    let lruTime = Infinity;

                    for (const memPage of memory) {
                        if (memPage in pageAccessOrder) {
                            if (pageAccessOrder[memPage] < lruTime) {
                                lruTime = pageAccessOrder[memPage];
                                lruPage = memPage;
                            }
                        }
                    }

                    if (lruPage === null) {
                        lruPage = memory[0];
                    }

                    const index = memory.indexOf(lruPage);
                    memory.splice(index, 1);
                    memory.push(page);
                    step.replacedPage = lruPage;
                    step.description = `Page fault: Replaced page ${lruPage} (LRU) with page ${page}`;
                }
            } else {
                step.description = `Page ${page} already in memory, updated access time`;
            }

            pageAccessOrder[page] = i;
            step.memoryAfter = [...memory];
            steps.push(step);
        }

        return {
            success: true,
            algorithm: 'LRU',
            frames: frames,
            pageRequests: pageRequests,
            totalPageFaults: pageFaults,
            steps: steps,
            finalMemory: memory
        };
    }
}

