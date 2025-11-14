"""
Banker's Algorithm Module for Deadlock Avoidance
"""

import random

class BankersModule:
    def __init__(self):
        self.name = "Banker's Algorithm"
        self.description = "Deadlock avoidance algorithm using resource allocation"
    
    def simulate(self, num_processes, num_resources, allocation=None, max_matrix=None, available=None):
        """
        Simulate Banker's algorithm
        
        Args:
            num_processes: Number of processes
            num_resources: Number of resource types
            
        Returns:
            Dictionary containing simulation results
        """
        # Generate or use provided allocation, max and available
        allocation = allocation if allocation else self._generate_random_matrix(num_processes, num_resources)
        max_matrix = max_matrix if max_matrix else self._generate_random_matrix(num_processes, num_resources)
        available = available if available else self._generate_random_vector(num_resources)

        # Basic validation
        if len(allocation) != num_processes or len(max_matrix) != num_processes:
            return { 'success': False, 'error': 'Invalid matrix dimensions for processes' }
        if any(len(row) != num_resources for row in allocation) or any(len(row) != num_resources for row in max_matrix):
            return { 'success': False, 'error': 'Invalid matrix dimensions for resources' }
        if len(available) != num_resources:
            return { 'success': False, 'error': 'Invalid available vector length' }
        
        # Calculate need matrix
        need = self._calculate_need_matrix(allocation, max_matrix, num_processes, num_resources)
        
        # Find safe sequence with step-by-step trace
        safe_sequence, steps = self._find_safe_sequence(allocation, need, available, num_processes, num_resources)
        
        # Generate RAG data for visualization
        rag = self._generate_rag_data(num_processes, num_resources, allocation, max_matrix)
        
        return {
            'success': True,
            'algorithm': "Banker's Algorithm",
            'allocation': allocation,
            'max': max_matrix,
            'need': need,
            'available': available,
            'safeSequence': safe_sequence,
            'rag': rag,
            'isSafe': len(safe_sequence) == num_processes,
            'steps': steps
        }
    
    def _generate_random_matrix(self, rows, cols):
        """Generate a random matrix with values 1-5"""
        matrix = []
        for i in range(rows):
            row = []
            for j in range(cols):
                row.append(random.randint(1, 5))
            matrix.append(row)
        return matrix
    
    def _generate_random_vector(self, size):
        """Generate a random vector with values 2-9"""
        vector = []
        for i in range(size):
            vector.append(random.randint(2, 9))
        return vector
    
    def _calculate_need_matrix(self, allocation, max_matrix, num_processes, num_resources):
        """Calculate need matrix: need[i][j] = max[i][j] - allocation[i][j]"""
        need = []
        for i in range(num_processes):
            row = []
            for j in range(num_resources):
                row.append(max_matrix[i][j] - allocation[i][j])
            need.append(row)
        return need
    
    def _find_safe_sequence(self, allocation, need, available, num_processes, num_resources):
        """Find safe sequence using Banker's algorithm with step trace"""
        work = available.copy()
        finish = [False] * num_processes
        safe_sequence = []
        steps = []

        progress_made = True
        while progress_made:
            progress_made = False
            step_info = {
                'work': work.copy(),
                'allocationsReleased': [],
                'chosenProcess': None,
            }
            for i in range(num_processes):
                if not finish[i] and self._can_allocate(need[i], work, num_resources):
                    for j in range(num_resources):
                        work[j] += allocation[i][j]
                    finish[i] = True
                    safe_sequence.append(f"P{i + 1}")
                    step_info['chosenProcess'] = f"P{i + 1}"
                    step_info['allocationsReleased'] = allocation[i].copy()
                    progress_made = True
                    break
            steps.append(step_info)

        return safe_sequence, steps
    
    def _can_allocate(self, need, work, num_resources):
        """Check if resources can be allocated to a process"""
        for i in range(num_resources):
            if need[i] > work[i]:
                return False
        return True
    
    def _generate_rag_data(self, num_processes, num_resources, allocation, max_matrix):
        """Generate Resource Allocation Graph data for visualization"""
        processes = []
        resources = []
        edges = []
        
        # Calculate need matrix for request edges
        need = self._calculate_need_matrix(allocation, max_matrix, num_processes, num_resources)
        
        # Create process nodes
        for i in range(num_processes):
            processes.append({
                'name': f"P{i + 1}",
                'id': i,
                'allocation': allocation[i],
                'max': max_matrix[i]
            })
        
        # Create resource nodes
        for i in range(num_resources):
            total_allocated = sum(allocation[j][i] for j in range(num_processes))
            resources.append({
                'name': f"R{i + 1}",
                'id': i,
                'total': total_allocated + random.randint(1, 5),
                'allocated': total_allocated
            })
        
        # Create allocation edges: Resource -> Process (when resource is allocated to process)
        for i in range(num_processes):
            for j in range(num_resources):
                if allocation[i][j] > 0:
                    edges.append({
                        'from': f"R{j + 1}",
                        'to': f"P{i + 1}",
                        'type': 'allocation',
                        'value': allocation[i][j]
                    })
        
        # Create request edges: Process -> Resource (when process needs resource)
        for i in range(num_processes):
            for j in range(num_resources):
                if need[i][j] > 0:
                    edges.append({
                        'from': f"P{i + 1}",
                        'to': f"R{j + 1}",
                        'type': 'request',
                        'value': need[i][j]
                    })
        
        return {
            'processes': processes,
            'resources': resources,
            'edges': edges
        }
