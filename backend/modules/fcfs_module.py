"""
First Come First Serve (FCFS) CPU Scheduling Algorithm Module
"""

class FCFSModule:
    def __init__(self):
        self.name = "First Come First Serve"
        self.description = "Processes are executed in the order they arrive"
    
    def simulate(self, processes):
        """
        Simulate FCFS CPU scheduling algorithm
        
        Args:
            processes: List of process dictionaries with keys: id, arrival, burst, priority
            
        Returns:
            Dictionary containing simulation results
        """
        # Sort processes by arrival time
        sorted_processes = sorted(processes, key=lambda x: x['arrival'])
        
        current_time = 0
        gantt_chart = []
        process_results = []
        steps = []
        
        # Calculate completion time, turnaround time, waiting time, and response time
        for process in sorted_processes:
            start_time = max(current_time, process['arrival'])
            completion_time = start_time + process['burst']
            turnaround_time = completion_time - process['arrival']
            waiting_time = turnaround_time - process['burst']
            response_time = start_time - process['arrival']
            
            # Add to Gantt chart
            gantt_chart.append({
                'name': process['id'],
                'startTime': start_time,
                'duration': process['burst']
            })
            steps.append({
                'event': 'dispatch',
                'process': process['id'],
                'start': start_time,
                'end': completion_time
            })
            
            # Store process results
            process_results.append({
                'id': process['id'],
                'arrivalTime': process['arrival'],
                'burstTime': process['burst'],
                'startTime': start_time,
                'completionTime': completion_time,
                'turnaroundTime': turnaround_time,
                'waitingTime': waiting_time,
                'responseTime': response_time
            })
            
            current_time = completion_time
        
        # Calculate metrics
        total_waiting_time = sum(p['waitingTime'] for p in process_results)
        total_turnaround_time = sum(p['turnaroundTime'] for p in process_results)
        total_response_time = sum(p['responseTime'] for p in process_results)
        total_burst_time = sum(p['burstTime'] for p in process_results)
        
        avg_waiting_time = total_waiting_time / len(process_results)
        avg_turnaround_time = total_turnaround_time / len(process_results)
        avg_response_time = total_response_time / len(process_results)
        cpu_utilization = total_burst_time / current_time if current_time > 0 else 0
        
        return {
            'algorithm': 'FCFS',
            'ganttChart': {
                'processes': gantt_chart,
                'totalTime': current_time
            },
            'processResults': process_results,
            'metrics': {
                'avgWaitingTime': round(avg_waiting_time, 2),
                'avgTurnaroundTime': round(avg_turnaround_time, 2),
                'avgResponseTime': round(avg_response_time, 2),
                'cpuUtilization': round(cpu_utilization, 4)
            },
            'steps': steps
        }
