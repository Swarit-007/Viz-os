#!/usr/bin/env python3
"""
Test script for memory allocation function
Demonstrates the allocateMemory() function usage
"""

import sys
import os

# Add project root to path
proj_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if proj_root not in sys.path:
    sys.path.insert(0, proj_root)

from backend.modules.memory_allocation_module import MemoryAllocationModule

def allocateMemory(blocks, processes, strategy="best"):
    """
    Allocate memory to processes using the specified strategy.
    
    Args:
        blocks: List of memory block sizes
        processes: List of process memory requirements
        strategy: "best", "first", or "worst"
    
    Returns:
        Dictionary with allocation results
    """
    allocator = MemoryAllocationModule()
    result = allocator.allocate_memory(blocks, processes, strategy)
    
    # Print results in the expected format
    if result['success']:
        print(f"\nMemory Allocation Results ({strategy.upper()} FIT):")
        print("-" * 40)
        for alloc in result['allocation']:
            process_size = alloc['process']
            block_num = alloc['block']
            if block_num is not None:
                print(f"{process_size} - {block_num}")
            else:
                print(f"{process_size} - no free block available")
        print("-" * 40)
    else:
        print(f"Error: {result.get('error', 'Unknown error')}")
    
    return result

# Example usage
if __name__ == "__main__":
    # Example 1: Best Fit
    print("=" * 50)
    print("EXAMPLE 1: Best Fit")
    print("=" * 50)
    blocks = [100, 500, 200, 300, 600]
    processes = [212, 417, 112, 426]
    allocateMemory(blocks, processes, "best")
    
    # Example 2: First Fit
    print("\n" + "=" * 50)
    print("EXAMPLE 2: First Fit")
    print("=" * 50)
    blocks = [100, 500, 200, 300, 600]
    processes = [212, 417, 112, 426]
    allocateMemory(blocks, processes, "first")
    
    # Example 3: Worst Fit
    print("\n" + "=" * 50)
    print("EXAMPLE 3: Worst Fit")
    print("=" * 50)
    blocks = [100, 500, 200, 300, 600]
    processes = [212, 417, 112, 426]
    allocateMemory(blocks, processes, "worst")
    
    # Example 4: Process that cannot be allocated
    print("\n" + "=" * 50)
    print("EXAMPLE 4: Process too large")
    print("=" * 50)
    blocks = [100, 200, 300]
    processes = [150, 250, 500]  # Last process is too large
    allocateMemory(blocks, processes, "best")

