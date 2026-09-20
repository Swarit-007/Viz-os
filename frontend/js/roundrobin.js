// Round Robin CPU Scheduling Algorithm
class RoundRobin {
    static simulate(processes, timeQuantum) {
        // Sort processes by arrival time
        const sortedProcesses = [...processes].sort((a, b) => a.arrival - b.arrival);
        
        let currentTime = 0;
        const ganttChart = [];
        const processResults = [];
        const readyQueue = [];
        let processIndex = 0;
        
        // Initialize process data
        const processData = sortedProcesses.map(p => ({
            ...p,
            remainingTime: p.burst,
            startTime: -1,
            completionTime: -1,
            turnaroundTime: -1,
            waitingTime: -1,
            responseTime: -1
        }));
        
        while (processIndex < processData.length || readyQueue.length > 0) {
            // Add processes that have arrived to ready queue
            while (processIndex < processData.length && 
                   processData[processIndex].arrival <= currentTime) {
                readyQueue.push(processData[processIndex]);
                processIndex++;
            }
            
            if (readyQueue.length === 0) {
                // No processes ready, advance time to next arrival
                if (processIndex < processData.length) {
                    currentTime = processData[processIndex].arrival;
                    continue;
                } else {
                    break;
                }
            }
            
            // Get next process from ready queue
            const process = readyQueue.shift();
            
            // Set start time if this is the first time the process runs
            if (process.startTime === -1) {
                process.startTime = currentTime;
                process.responseTime = process.startTime - process.arrival;
            }
            
            // Execute for time quantum or remaining time, whichever is smaller
            const executionTime = Math.min(timeQuantum, process.remainingTime);
            const startExecution = currentTime;
            const endExecution = startExecution + executionTime;
            
            // Add to Gantt chart
            ganttChart.push({
                name: process.id,
                startTime: startExecution,
                duration: executionTime
            });
            
            // Update remaining time
            process.remainingTime -= executionTime;
            currentTime = endExecution;
            
            // If process is not finished, add it back to ready queue
            if (process.remainingTime > 0) {
                // Add any new processes that arrived during execution
                while (processIndex < processData.length && 
                       processData[processIndex].arrival <= currentTime) {
                    readyQueue.push(processData[processIndex]);
                    processIndex++;
                }
                readyQueue.push(process);
            } else {
                // Process is completed
                process.completionTime = currentTime;
                process.turnaroundTime = process.completionTime - process.arrival;
                process.waitingTime = process.turnaroundTime - process.burst;
                
                processResults.push({
                    id: process.id,
                    arrivalTime: process.arrival,
                    burstTime: process.burst,
                    startTime: process.startTime,
                    completionTime: process.completionTime,
                    turnaroundTime: process.turnaroundTime,
                    waitingTime: process.waitingTime,
                    responseTime: process.responseTime
                });
            }
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
            algorithm: 'Round Robin',
            timeQuantum: timeQuantum,
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
