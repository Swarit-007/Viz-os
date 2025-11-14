// Priority CPU Scheduling Algorithm
class Priority {
    static simulate(processes) {
        // Sort processes by arrival time first
        const sortedProcesses = [...processes].sort((a, b) => a.arrival - b.arrival);
        
        let currentTime = 0;
        const ganttChart = [];
        const processResults = [];
        const readyQueue = [];
        let processIndex = 0;
        
        while (processIndex < sortedProcesses.length || readyQueue.length > 0) {
            // Add processes that have arrived to ready queue
            while (processIndex < sortedProcesses.length && 
                   sortedProcesses[processIndex].arrival <= currentTime) {
                readyQueue.push(sortedProcesses[processIndex]);
                processIndex++;
            }
            
            if (readyQueue.length === 0) {
                // No processes ready, advance time to next arrival
                if (processIndex < sortedProcesses.length) {
                    currentTime = sortedProcesses[processIndex].arrival;
                    continue;
                } else {
                    break;
                }
            }
            
            // Sort ready queue by priority (lower number = higher priority)
            readyQueue.sort((a, b) => a.priority - b.priority);
            
            // Execute the highest priority job
            const process = readyQueue.shift();
            const startTime = Math.max(currentTime, process.arrival);
            const completionTime = startTime + process.burst;
            const turnaroundTime = completionTime - process.arrival;
            const waitingTime = turnaroundTime - process.burst;
            const responseTime = startTime - process.arrival;
            
            // Add to Gantt chart
            ganttChart.push({
                name: process.id,
                startTime: startTime,
                duration: process.burst
            });
            
            // Store process results
            processResults.push({
                id: process.id,
                arrivalTime: process.arrival,
                burstTime: process.burst,
                priority: process.priority,
                startTime: startTime,
                completionTime: completionTime,
                turnaroundTime: turnaroundTime,
                waitingTime: waitingTime,
                responseTime: responseTime
            });
            
            currentTime = completionTime;
        }
        
        // Calculate metrics
        const totalWaitingTime = processResults.reduce((sum, p) => sum + p.waitingTime, 0);
        const totalTurnaroundTime = processResults.reduce((sum, p) => sum + p.turnaroundTime, 0);
        const totalResponseTime = processResults.reduce((sum, p) => sum + p.responseTime, 0);
        const totalBurstTime = processResults.reduce((sum, p) => sum + p.burstTime, 0);
        
        const avgWaitingTime = totalWaitingTime / processResults.length;
        const avgTurnaroundTime = totalTurnaroundTime / processResults.length;
        const avgResponseTime = totalResponseTime / processResults.length;
        const cpuUtilization = totalBurstTime / currentTime;
        
        return {
            algorithm: 'Priority',
            ganttChart: {
                processes: ganttChart,
                totalTime: currentTime
            },
            processResults: processResults,
            metrics: {
                avgWaitingTime: avgWaitingTime,
                avgTurnaroundTime: avgTurnaroundTime,
                avgResponseTime: avgResponseTime,
                cpuUtilization: cpuUtilization
            }
        };
    }
}
