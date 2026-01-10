"""
Priority queue with priority management
Supports FIFO, SJF (Shortest Job First), and type-based priorities
"""

from typing import Optional, List
from src.core.simulation_engine import Job


class PriorityQueue:
    """
    Priority queue with priority management
    """
    
    def __init__(self):
        self.queue: List[Job] = []
    
    def add(self, job: Job):
        """Add a job to the queue"""
        self.queue.append(job)
    
    def get_next_fifo(self) -> Optional[Job]:
        """Get the next job in FIFO order"""
        if len(self.queue) == 0:
            return None
        return self.queue.pop(0)
    
    def get_next_sjf(self) -> Optional[Job]:
        """
        Get the next job according to Shortest Job First
        Assumes job.service_time is already defined
        """
        if len(self.queue) == 0:
            return None
        
        # Find the job with minimum service time
        min_idx = 0
        min_time = self.queue[0].service_time if self.queue[0].service_time else float('inf')
        
        for i, job in enumerate(self.queue):
            job_time = job.service_time if job.service_time else float('inf')
            if job_time < min_time:
                min_time = job_time
                min_idx = i
        
        return self.queue.pop(min_idx)
    
    def get_next_priority(self, priority_order: List[str]) -> Optional[Job]:
        """
        Get the next job according to a priority order of types
        
        Args:
            priority_order: List of types in priority order (e.g., ["ING", "PREPA"])
        """
        if len(self.queue) == 0:
            return None
        
        # Search first in priority order
        for job_type in priority_order:
            for i, job in enumerate(self.queue):
                if job.job_type == job_type:
                    return self.queue.pop(i)
        
        # If no job found in priorities, take the first one
        return self.queue.pop(0)
    
    def __len__(self):
        return len(self.queue)
