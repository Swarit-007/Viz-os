// Banker's Algorithm for Deadlock Avoidance
class Bankers {
    static simulate(numProcesses, numResources) {
        // Generate random allocation and maximum matrices
        const allocation = this.generateRandomMatrix(numProcesses, numResources);
        const max = this.generateRandomMatrix(numProcesses, numResources);
        const available = this.generateRandomVector(numResources);
        
        // Calculate need matrix
        const need = this.calculateNeedMatrix(allocation, max, numProcesses, numResources);
        
        // Find safe sequence
        const safeSequence = this.findSafeSequence(allocation, need, available, numProcesses, numResources);
        
        // Generate RAG data for visualization
        const rag = this.generateRAGData(numProcesses, numResources, allocation, max);
        
        return {
            algorithm: 'Banker\'s Algorithm',
            allocation: allocation,
            max: max,
            need: need,
            available: available,
            safeSequence: safeSequence,
            rag: rag,
            isSafe: safeSequence.length === numProcesses
        };
    }
    
    static generateRandomMatrix(rows, cols) {
        const matrix = [];
        for (let i = 0; i < rows; i++) {
            const row = [];
            for (let j = 0; j < cols; j++) {
                row.push(Math.floor(Math.random() * 5) + 1); // Random values 1-5
            }
            matrix.push(row);
        }
        return matrix;
    }
    
    static generateRandomVector(size) {
        const vector = [];
        for (let i = 0; i < size; i++) {
            vector.push(Math.floor(Math.random() * 8) + 2); // Random values 2-9
        }
        return vector;
    }
    
    static calculateNeedMatrix(allocation, max, numProcesses, numResources) {
        const need = [];
        for (let i = 0; i < numProcesses; i++) {
            const row = [];
            for (let j = 0; j < numResources; j++) {
                row.push(max[i][j] - allocation[i][j]);
            }
            need.push(row);
        }
        return need;
    }
    
    static findSafeSequence(allocation, need, available, numProcesses, numResources) {
        const work = [...available];
        const finish = new Array(numProcesses).fill(false);
        const safeSequence = [];
        
        let found = true;
        while (found) {
            found = false;
            for (let i = 0; i < numProcesses; i++) {
                if (!finish[i] && this.canAllocate(need[i], work, numResources)) {
                    // Process i can be allocated resources
                    for (let j = 0; j < numResources; j++) {
                        work[j] += allocation[i][j];
                    }
                    finish[i] = true;
                    safeSequence.push(`P${i + 1}`);
                    found = true;
                    break;
                }
            }
        }
        
        return safeSequence;
    }
    
    static canAllocate(need, work, numResources) {
        for (let i = 0; i < numResources; i++) {
            if (need[i] > work[i]) {
                return false;
            }
        }
        return true;
    }
    
    static generateRAGData(numProcesses, numResources, allocation, max) {
        const processes = [];
        const resources = [];
        const edges = [];
        
        // Calculate need matrix for request edges
        const need = this.calculateNeedMatrix(allocation, max, numProcesses, numResources);
        
        // Create process nodes
        for (let i = 0; i < numProcesses; i++) {
            processes.push({
                name: `P${i + 1}`,
                id: i,
                allocation: allocation[i],
                max: max[i]
            });
        }
        
        // Create resource nodes
        for (let i = 0; i < numResources; i++) {
            let totalAllocated = 0;
            for (let j = 0; j < numProcesses; j++) {
                totalAllocated += allocation[j][i];
            }
            resources.push({
                name: `R${i + 1}`,
                id: i,
                total: totalAllocated + Math.floor(Math.random() * 5) + 1,
                allocated: totalAllocated
            });
        }
        
        // Create allocation edges: Resource -> Process (when resource is allocated to process)
        for (let i = 0; i < numProcesses; i++) {
            for (let j = 0; j < numResources; j++) {
                if (allocation[i][j] > 0) {
                    edges.push({
                        from: `R${j + 1}`,
                        to: `P${i + 1}`,
                        type: 'allocation',
                        value: allocation[i][j]
                    });
                }
            }
        }
        
        // Create request edges: Process -> Resource (when process needs resource)
        for (let i = 0; i < numProcesses; i++) {
            for (let j = 0; j < numResources; j++) {
                if (need[i][j] > 0) {
                    edges.push({
                        from: `P${i + 1}`,
                        to: `R${j + 1}`,
                        type: 'request',
                        value: need[i][j]
                    });
                }
            }
        }
        
        return {
            processes: processes,
            resources: resources,
            edges: edges
        };
    }
}
