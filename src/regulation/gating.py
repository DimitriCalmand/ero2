"""
Gating Controller (temporal barrier)
Prevents system access during specific periods
"""

import simpy
from typing import Optional, List


class GatingController:
    """
    Gating Controller (temporal barrier)
    Prevents system access during specific periods
    """
    
    def __init__(self,
                 env: simpy.Environment,
                 gating_intervals: List[tuple]):
        """
        Args:
            env: SimPy Environment
            gating_intervals: List of tuples (start_time, end_time) for closed periods
        """
        self.env = env
        self.gating_intervals = gating_intervals
    
    def is_open(self, time: Optional[float] = None) -> bool:
        """
        Check if the system is open
        
        Args:
            time: Time to check (uses env.now if None)
            
        Returns:
            True if the system is open
        """
        check_time = time if time is not None else self.env.now
        
        for start, end in self.gating_intervals:
            if start <= check_time < end:
                return False  # Closed during this interval
        
        return True
    
    def wait_until_open(self):
        """
        Waiting process until system opens
        """
        while not self.is_open():
            # Find the next opening time
            next_open = None
            current_time = self.env.now
            
            for start, end in self.gating_intervals:
                if start <= current_time < end:
                    next_open = end
                    break
            
            if next_open:
                wait_time = next_open - current_time
                yield self.env.timeout(wait_time)
            else:
                break
