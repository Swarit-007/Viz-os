// Memory Allocation Algorithms - Best Fit, First Fit, Worst Fit
class MemoryAllocation {
    static allocateMemory(blocks, processes, strategy) {
        // This is a client-side implementation for reference
        // The actual allocation is done on the server
        const allocator = new MemoryAllocationSimulator();
        return allocator.allocate(blocks, processes, strategy);
    }
}

class MemoryAllocationSimulator {
    allocate(blocks, processes, strategy) {
        const remainingBlocks = [...blocks];
        const allocation = [];
        const steps = [];
        
        for (let i = 0; i < processes.length; i++) {
            const processSize = processes[i];
            let allocatedBlock = null;
            
            if (strategy === 'best') {
                allocatedBlock = this.bestFit(remainingBlocks, processSize);
            } else if (strategy === 'first') {
                allocatedBlock = this.firstFit(remainingBlocks, processSize);
            } else if (strategy === 'worst') {
                allocatedBlock = this.worstFit(remainingBlocks, processSize);
            }
            
            if (allocatedBlock !== null) {
                remainingBlocks[allocatedBlock] -= processSize;
                allocation.push({
                    process: processSize,
                    block: allocatedBlock + 1
                });
                steps.push({
                    process_index: i + 1,
                    process: processSize,
                    status: 'allocated',
                    block: allocatedBlock + 1,
                    description: `Process ${processSize} allocated to block ${allocatedBlock + 1}`
                });
            } else {
                allocation.push({
                    process: processSize,
                    block: null
                });
                steps.push({
                    process_index: i + 1,
                    process: processSize,
                    status: 'not_allocated',
                    block: null,
                    description: `Process ${processSize} cannot be allocated - no free block available`
                });
            }
        }
        
        return {
            success: true,
            strategy: strategy,
            blocks: blocks,
            processes: processes,
            allocation: allocation,
            steps: steps
        };
    }
    
    bestFit(blocks, processSize) {
        let bestIdx = null;
        let bestSize = Infinity;
        
        for (let i = 0; i < blocks.length; i++) {
            if (blocks[i] >= processSize && blocks[i] < bestSize) {
                bestSize = blocks[i];
                bestIdx = i;
            }
        }
        
        return bestIdx;
    }
    
    firstFit(blocks, processSize) {
        for (let i = 0; i < blocks.length; i++) {
            if (blocks[i] >= processSize) {
                return i;
            }
        }
        return null;
    }
    
    worstFit(blocks, processSize) {
        let worstIdx = null;
        let worstSize = -1;
        
        for (let i = 0; i < blocks.length; i++) {
            if (blocks[i] >= processSize && blocks[i] > worstSize) {
                worstSize = blocks[i];
                worstIdx = i;
            }
        }
        
        return worstIdx;
    }
}

