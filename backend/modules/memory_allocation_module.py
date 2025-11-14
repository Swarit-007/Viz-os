"""
Memory Allocation Module
Implements Best Fit, First Fit, and Worst Fit memory allocation strategies
"""

from typing import List, Dict, Any, Optional

class MemoryAllocationModule:
    def __init__(self):
        pass

    def allocate_memory(self, blocks: List[int], processes: List[int], strategy: str = "best") -> Dict[str, Any]:
        """
        Allocate memory to processes using the specified strategy
        
        Args:
            blocks: List of memory block sizes
            processes: List of process memory requirements
            strategy: "best", "first", or "worst"
            
        Returns:
            Dictionary containing allocation results
        """
        # Create a copy of blocks to track remaining space
        remaining_blocks = blocks.copy()
        allocation = []
        steps = []
        final_block_status = []
        
        for process_idx, process_size in enumerate(processes):
            step = {
                'process_index': process_idx + 1,
                'process': process_size,
                'status': 'not_allocated',
                'block': None,
                'description': ''
            }
            
            allocated_block = None
            
            if strategy.lower() == "best":
                allocated_block = self._best_fit(remaining_blocks, process_size)
            elif strategy.lower() == "first":
                allocated_block = self._first_fit(remaining_blocks, process_size)
            elif strategy.lower() == "worst":
                allocated_block = self._worst_fit(remaining_blocks, process_size)
            else:
                return {
                    'success': False,
                    'error': f'Unknown strategy: {strategy}'
                }
            
            if allocated_block is not None:
                block_idx = allocated_block['index']
                # Update remaining block size
                remaining_blocks[block_idx] -= process_size
                
                allocation.append({
                    'process': process_size,
                    'block': block_idx + 1  # 1-indexed for display
                })
                
                step['status'] = 'allocated'
                step['block'] = block_idx + 1
                step['description'] = f'Process {process_size} allocated to block {block_idx + 1} (remaining: {remaining_blocks[block_idx]})'
            else:
                allocation.append({
                    'process': process_size,
                    'block': None
                })
                
                step['status'] = 'not_allocated'
                step['description'] = f'Process {process_size} cannot be allocated - no free block available'
            
            steps.append(step)
        
        # Create final block status
        for idx, (original_size, remaining_size) in enumerate(zip(blocks, remaining_blocks)):
            allocated_size = original_size - remaining_size
            final_block_status.append({
                'block_number': idx + 1,
                'size': original_size,
                'allocated': allocated_size,
                'remaining': remaining_size,
                'is_free': remaining_size == original_size
            })
        
        return {
            'success': True,
            'strategy': strategy,
            'blocks': blocks,
            'processes': processes,
            'allocation': allocation,
            'steps': steps,
            'final_block_status': final_block_status
        }

    def _best_fit(self, blocks: List[int], process_size: int) -> Optional[Dict[str, int]]:
        """
        Best Fit: Find the smallest block that can accommodate the process
        
        Args:
            blocks: List of available block sizes
            process_size: Size of the process
            
        Returns:
            Dictionary with 'index' and 'size' of the best fitting block, or None
        """
        best_idx = None
        best_size = float('inf')
        
        for idx, block_size in enumerate(blocks):
            if block_size >= process_size and block_size < best_size:
                best_size = block_size
                best_idx = idx
        
        if best_idx is not None:
            return {'index': best_idx, 'size': best_size}
        return None

    def _first_fit(self, blocks: List[int], process_size: int) -> Optional[Dict[str, int]]:
        """
        First Fit: Find the first block that can accommodate the process
        
        Args:
            blocks: List of available block sizes
            process_size: Size of the process
            
        Returns:
            Dictionary with 'index' and 'size' of the first fitting block, or None
        """
        for idx, block_size in enumerate(blocks):
            if block_size >= process_size:
                return {'index': idx, 'size': block_size}
        return None

    def _worst_fit(self, blocks: List[int], process_size: int) -> Optional[Dict[str, int]]:
        """
        Worst Fit: Find the largest block that can accommodate the process
        
        Args:
            blocks: List of available block sizes
            process_size: Size of the process
            
        Returns:
            Dictionary with 'index' and 'size' of the worst fitting block, or None
        """
        worst_idx = None
        worst_size = -1
        
        for idx, block_size in enumerate(blocks):
            if block_size >= process_size and block_size > worst_size:
                worst_size = block_size
                worst_idx = idx
        
        if worst_idx is not None:
            return {'index': worst_idx, 'size': worst_size}
        return None

