"""
Page Replacement Module
Implements FIFO and LRU page replacement algorithms
"""

from typing import List, Dict, Any, Optional
from collections import deque, OrderedDict

class PageReplacementModule:
    def __init__(self):
        pass

    def simulate_fifo(self, frames: int, page_requests: List[int]) -> Dict[str, Any]:
        """
        Simulate FIFO (First-In-First-Out) page replacement algorithm
        
        Args:
            frames: Number of frames available in memory
            page_requests: List of page requests
            
        Returns:
            Dictionary containing simulation results
        """
        memory = []  # Current pages in memory (FIFO queue)
        page_faults = 0
        steps = []
        
        for i, page in enumerate(page_requests):
            step = {
                'step': i + 1,
                'requested_page': page,
                'memory_before': memory.copy(),
                'page_fault': False,
                'replaced_page': None,
                'memory_after': None,
                'description': ''
            }
            
            if page not in memory:
                page_fault = True
                page_faults += 1
                
                if len(memory) < frames:
                    # Memory not full, just add the page
                    memory.append(page)
                    step['description'] = f'Page {page} added to memory (memory not full)'
                else:
                    # Memory full, replace oldest page (FIFO)
                    replaced = memory.pop(0)  # Remove first (oldest) page
                    memory.append(page)  # Add new page at end
                    step['replaced_page'] = replaced
                    step['description'] = f'Page fault: Replaced page {replaced} with page {page} (FIFO)'
                
                step['page_fault'] = True
            else:
                # Page already in memory, no page fault
                step['description'] = f'Page {page} already in memory, no page fault'
            
            step['memory_after'] = memory.copy()
            steps.append(step)
        
        return {
            'success': True,
            'algorithm': 'FIFO',
            'frames': frames,
            'page_requests': page_requests,
            'total_page_faults': page_faults,
            'steps': steps,
            'final_memory': memory
        }

    def simulate_lru(self, frames: int, page_requests: List[int]) -> Dict[str, Any]:
        """
        Simulate LRU (Least Recently Used) page replacement algorithm
        
        Args:
            frames: Number of frames available in memory
            page_requests: List of page requests
            
        Returns:
            Dictionary containing simulation results
        """
        memory = []  # Current pages in memory
        page_access_order = {}  # Track when each page was last accessed
        page_faults = 0
        steps = []
        
        for i, page in enumerate(page_requests):
            step = {
                'step': i + 1,
                'requested_page': page,
                'memory_before': memory.copy(),
                'page_fault': False,
                'replaced_page': None,
                'memory_after': None,
                'description': ''
            }
            
            if page not in memory:
                page_fault = True
                page_faults += 1
                
                if len(memory) < frames:
                    # Memory not full, just add the page
                    memory.append(page)
                    step['description'] = f'Page {page} added to memory (memory not full)'
                else:
                    # Memory full, find LRU page (least recently accessed)
                    lru_page = None
                    lru_time = float('inf')
                    
                    for mem_page in memory:
                        if mem_page in page_access_order:
                            if page_access_order[mem_page] < lru_time:
                                lru_time = page_access_order[mem_page]
                                lru_page = mem_page
                    
                    # If no access order found, use first page as fallback
                    if lru_page is None:
                        lru_page = memory[0]
                    
                    # Replace LRU page
                    memory.remove(lru_page)
                    memory.append(page)
                    step['replaced_page'] = lru_page
                    step['description'] = f'Page fault: Replaced page {lru_page} (LRU) with page {page}'
                
                step['page_fault'] = True
            else:
                # Page already in memory, update access time
                step['description'] = f'Page {page} already in memory, updated access time'
            
            # Update access order for current page
            page_access_order[page] = i
            
            step['memory_after'] = memory.copy()
            steps.append(step)
        
        return {
            'success': True,
            'algorithm': 'LRU',
            'frames': frames,
            'page_requests': page_requests,
            'total_page_faults': page_faults,
            'steps': steps,
            'final_memory': memory
        }

    def simulate(self, algorithm: str, frames: int, page_requests: List[int]) -> Dict[str, Any]:
        """
        Simulate page replacement algorithm
        
        Args:
            algorithm: 'fifo' or 'lru'
            frames: Number of frames available in memory
            page_requests: List of page requests
            
        Returns:
            Dictionary containing simulation results
        """
        if algorithm.lower() == 'fifo':
            return self.simulate_fifo(frames, page_requests)
        elif algorithm.lower() == 'lru':
            return self.simulate_lru(frames, page_requests)
        else:
            return {
                'success': False,
                'error': f'Unknown algorithm: {algorithm}'
            }

