// Deadlock Detection Algorithm
class Deadlock {
    static simulate(numProcesses, numResources) {
        // Generate random allocation and request matrices
        const allocation = this.generateRandomMatrix(numProcesses, numResources);
        const request = this.generateRandomMatrix(numProcesses, numResources);
        const available = this.generateRandomVector(numResources);
        
        // Detect deadlock
        const deadlockResult = this.detectDeadlock(allocation, request, available, numProcesses, numResources);
        
        // Generate wait-for graph data
        const waitForGraph = this.generateWaitForGraph(numProcesses, allocation, request);
        
        return {
            algorithm: 'Deadlock Detection',
            allocation: allocation,
            request: request,
            available: available,
            hasDeadlock: deadlockResult.hasDeadlock,
            deadlockedProcesses: deadlockResult.deadlockedProcesses,
            waitForGraph: waitForGraph
        };
    }
    
    static generateRandomMatrix(rows, cols) {
        const matrix = [];
        for (let i = 0; i < rows; i++) {
            const row = [];
            for (let j = 0; j < cols; j++) {
                row.push(Math.floor(Math.random() * 3)); // Random values 0-2
            }
            matrix.push(row);
        }
        return matrix;
    }
    
    static generateRandomVector(size) {
        const vector = [];
        for (let i = 0; i < size; i++) {
            vector.push(Math.floor(Math.random() * 5) + 1); // Random values 1-5
        }
        return vector;
    }
    
    static detectDeadlock(allocation, request, available, numProcesses, numResources) {
        const work = [...available];
        const finish = new Array(numProcesses).fill(false);
        const deadlockedProcesses = [];
        
        // Initialize finish array - mark processes with no allocation as finished
        for (let i = 0; i < numProcesses; i++) {
            let hasAllocation = false;
            for (let j = 0; j < numResources; j++) {
                if (allocation[i][j] > 0) {
                    hasAllocation = true;
                    break;
                }
            }
            if (!hasAllocation) {
                finish[i] = true;
            }
        }
        
        // Find processes that can be allocated resources
        let found = true;
        while (found) {
            found = false;
            for (let i = 0; i < numProcesses; i++) {
                if (!finish[i] && this.canAllocate(request[i], work, numResources)) {
                    // Process i can be allocated resources
                    for (let j = 0; j < numResources; j++) {
                        work[j] += allocation[i][j];
                    }
                    finish[i] = true;
                    found = true;
                }
            }
        }
        
        // Check for deadlocked processes
        for (let i = 0; i < numProcesses; i++) {
            if (!finish[i]) {
                deadlockedProcesses.push(`P${i + 1}`);
            }
        }
        
        return {
            hasDeadlock: deadlockedProcesses.length > 0,
            deadlockedProcesses: deadlockedProcesses
        };
    }
    
    static canAllocate(request, work, numResources) {
        for (let i = 0; i < numResources; i++) {
            if (request[i] > work[i]) {
                return false;
            }
        }
        return true;
    }
    
    static generateWaitForGraph(numProcesses, allocation, request) {
        const processes = [];
        const edges = [];
        
        // Create process nodes
        for (let i = 0; i < numProcesses; i++) {
            processes.push({
                name: `P${i + 1}`,
                id: i,
                isDeadlocked: false
            });
        }
        
        // Create wait-for edges based on resource allocation
        for (let i = 0; i < numProcesses; i++) {
            for (let j = 0; j < numProcesses; j++) {
                if (i !== j) {
                    // Check if process i is waiting for resources held by process j
                    let isWaiting = false;
                    for (let k = 0; k < allocation[0].length; k++) {
                        if (request[i][k] > 0 && allocation[j][k] > 0) {
                            isWaiting = true;
                            break;
                        }
                    }
                    if (isWaiting) {
                        edges.push({
                            from: i,
                            to: j,
                            label: `P${i + 1} waits for P${j + 1}`
                        });
                    }
                }
            }
        }
        
        // Mark deadlocked processes
        const deadlockResult = this.detectDeadlock(allocation, request, 
            this.generateRandomVector(allocation[0].length), numProcesses, allocation[0].length);
        
        deadlockResult.deadlockedProcesses.forEach(processName => {
            const processId = parseInt(processName.substring(1)) - 1;
            if (processId >= 0 && processId < processes.length) {
                processes[processId].isDeadlocked = true;
            }
        });
        
        return {
            processes: processes,
            edges: edges
        };
    }
}
