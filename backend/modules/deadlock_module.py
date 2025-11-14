"""
Deadlock Detection Algorithm Module
"""

import random

class DeadlockModule:
    def __init__(self):
        self.name = "Deadlock Detection"
        self.description = "Detect deadlocks in resource allocation"
    
    def simulate(self, num_processes, num_resources, allocation=None, request=None, available=None):
        """
        Simulate deadlock detection algorithm
        
        Args:
            num_processes: Number of processes
            num_resources: Number of resource types
            
        Returns:
            Dictionary containing simulation results
        """
        # Generate or use provided allocation, request and available
        allocation = allocation if allocation else self._generate_random_matrix(num_processes, num_resources)
        request = request if request else self._generate_random_matrix(num_processes, num_resources)
        available = available if available else self._generate_random_vector(num_resources)

        # Basic validation
        if len(allocation) != num_processes or len(request) != num_processes:
            return { 'success': False, 'error': 'Invalid matrix dimensions for processes' }
        if any(len(row) != num_resources for row in allocation) or any(len(row) != num_resources for row in request):
            return { 'success': False, 'error': 'Invalid matrix dimensions for resources' }
        if len(available) != num_resources:
            return { 'success': False, 'error': 'Invalid available vector length' }
        
        # Detect deadlock with step-by-step trace
        deadlock_result, steps = self._detect_deadlock(allocation, request, available, num_processes, num_resources)
        
        # Generate wait-for graph data
        wait_for_graph = self._generate_wait_for_graph(num_processes, allocation, request)
        
        return {
            'success': True,
            'algorithm': 'Deadlock Detection',
            'allocation': allocation,
            'request': request,
            'available': available,
            'hasDeadlock': deadlock_result['hasDeadlock'],
            'deadlockedProcesses': deadlock_result['deadlockedProcesses'],
            'waitForGraph': wait_for_graph,
            'steps': steps
        }
    
    def _generate_random_matrix(self, rows, cols):
        """Generate a random matrix with values 0-2"""
        matrix = []
        for i in range(rows):
            row = []
            for j in range(cols):
                row.append(random.randint(0, 2))
            matrix.append(row)
        return matrix
    
    def _generate_random_vector(self, size):
        """Generate a random vector with values 1-5"""
        vector = []
        for i in range(size):
            vector.append(random.randint(1, 5))
        return vector
    
    def _detect_deadlock(self, allocation, request, available, num_processes, num_resources):
        """Detect deadlock using the deadlock detection algorithm with step trace"""
        work = available.copy()
        finish = [False] * num_processes
        deadlocked_processes = []
        steps = []

        # Initialize finish array - mark processes with no allocation as finished
        init_info = {'initializedFinished': []}
        for i in range(num_processes):
            has_allocation = any(allocation[i][j] > 0 for j in range(num_resources))
            if not has_allocation:
                finish[i] = True
                init_info['initializedFinished'].append(f"P{i + 1}")
        steps.append(init_info)

        # Find processes that can be allocated resources
        progress_made = True
        while progress_made:
            progress_made = False
            iteration_info = {'work': work.copy(), 'allocated': []}
            for i in range(num_processes):
                if not finish[i] and self._can_allocate(request[i], work, num_resources):
                    for j in range(num_resources):
                        work[j] += allocation[i][j]
                    finish[i] = True
                    iteration_info['allocated'].append(f"P{i + 1}")
                    progress_made = True
            steps.append(iteration_info)

        # Check for deadlocked processes
        for i in range(num_processes):
            if not finish[i]:
                deadlocked_processes.append(f"P{i + 1}")

        return ({
            'hasDeadlock': len(deadlocked_processes) > 0,
            'deadlockedProcesses': deadlocked_processes
        }, steps)
    
    def _can_allocate(self, request, work, num_resources):
        """Check if resources can be allocated to a process"""
        for i in range(num_resources):
            if request[i] > work[i]:
                return False
        return True
    
    def _generate_wait_for_graph(self, num_processes, allocation, request):
        """Generate wait-for graph data for visualization"""
        processes = []
        edges = []
        
        # Create process nodes
        for i in range(num_processes):
            processes.append({
                'name': f"P{i + 1}",
                'id': i,
                'isDeadlocked': False
            })
        
        # Create wait-for edges based on resource allocation
        for i in range(num_processes):
            for j in range(num_processes):
                if i != j:
                    # Check if process i is waiting for resources held by process j
                    is_waiting = any(
                        request[i][k] > 0 and allocation[j][k] > 0 
                        for k in range(len(allocation[0]))
                    )
                    if is_waiting:
                        edges.append({
                            'from': i,
                            'to': j,
                            'label': f"P{i + 1} waits for P{j + 1}"
                        })
        
        # Mark deadlocked processes
        deadlock_result, _ = self._detect_deadlock(
            allocation,
            request,
            self._generate_random_vector(len(allocation[0])),
            num_processes,
            len(allocation[0])
        )
        
        for process_name in deadlock_result['deadlockedProcesses']:
            process_id = int(process_name[1:]) - 1
            if 0 <= process_id < len(processes):
                processes[process_id]['isDeadlocked'] = True
        
        return {
            'processes': processes,
            'edges': edges
        }
