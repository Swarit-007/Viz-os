"""
Round Robin CPU Scheduling Algorithm Module
"""

class RoundRobinModule:
    def __init__(self):
        self.name = "Round Robin"
        self.description = "Processes are executed in time slices (quantum) in circular order"
    
    def simulate(self, processes, time_quantum):
        """
        Simulate Round Robin CPU scheduling algorithm
        
        Args:
            processes: List of process dictionaries with keys: id, arrival, burst, priority
            time_quantum: Time quantum for round robin scheduling
            
        Returns:
            Dictionary containing simulation results
        """
        # Sort processes by arrival time
        sorted_processes = sorted(processes, key=lambda x: x['arrival'])
        
        current_time = 0
        gantt_chart = []
        process_results = []
        ready_queue = []
        process_index = 0
        steps = []
        
        # Initialize process data
        process_data = []
        for process in sorted_processes:
            process_data.append({
                'id': process['id'],
                'arrival': process['arrival'],
                'burst': process['burst'],
                'remaining_time': process['burst'],
                'start_time': -1,
                'completion_time': -1,
                'turnaround_time': -1,
                'waiting_time': -1,
                'response_time': -1
            })
        
        while process_index < len(process_data) or ready_queue:
            # Add processes that have arrived to ready queue
            while (process_index < len(process_data) and 
                   process_data[process_index]['arrival'] <= current_time):
                ready_queue.append(process_data[process_index])
                process_index += 1
            
            if not ready_queue:
                # No processes ready, advance time to next arrival
                if process_index < len(process_data):
                    current_time = process_data[process_index]['arrival']
                    continue
                else:
                    break
            
            # Get next process from ready queue
            process = ready_queue.pop(0)
            
            # Set start time if this is the first time the process runs
            if process['start_time'] == -1:
                process['start_time'] = current_time
                process['response_time'] = process['start_time'] - process['arrival']
            
            # Execute for time quantum or remaining time, whichever is smaller
            execution_time = min(time_quantum, process['remaining_time'])
            start_execution = current_time
            end_execution = start_execution + execution_time
            
            # Add to Gantt chart
            gantt_chart.append({
                'name': process['id'],
                'startTime': start_execution,
                'duration': execution_time
            })
            steps.append({
                'event': 'timeslice',
                'process': process['id'],
                'quantum': time_quantum,
                'ran': execution_time,
                'start': start_execution,
                'end': end_execution
            })
            
            # Update remaining time
            process['remaining_time'] -= execution_time
            current_time = end_execution
            
            # If process is not finished, add it back to ready queue
            if process['remaining_time'] > 0:
                # Add any new processes that arrived during execution
                while (process_index < len(process_data) and 
                       process_data[process_index]['arrival'] <= current_time):
                    ready_queue.append(process_data[process_index])
                    process_index += 1
                ready_queue.append(process)
            else:
                # Process is completed
                process['completion_time'] = current_time
                process['turnaround_time'] = process['completion_time'] - process['arrival']
                process['waiting_time'] = process['turnaround_time'] - process['burst']
                
                process_results.append({
                    'id': process['id'],
                    'arrivalTime': process['arrival'],
                    'burstTime': process['burst'],
                    'startTime': process['start_time'],
                    'completionTime': process['completion_time'],
                    'turnaroundTime': process['turnaround_time'],
                    'waitingTime': process['waiting_time'],
                    'responseTime': process['response_time']
                })
        
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
            'algorithm': 'Round Robin',
            'timeQuantum': time_quantum,
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
