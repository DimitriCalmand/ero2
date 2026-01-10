"""
Server managing multiple populations with different characteristics
"""

import simpy
from typing import Optional, Callable
from src.core.simulation_engine import SimulationLogger, EventType, Job
from .priority_queue import PriorityQueue
from .gating import GatingController


class HeterogeneousServer:
    """
    Server managing multiple populations with different characteristics
    """
    
    def __init__(self,
                 env: simpy.Environment,
                 server_id: str,
                 num_servers: int,
                 logger: SimulationLogger,
                 scheduling_policy: str = "FIFO",
                 gating_controller: Optional[GatingController] = None):
        """
        Args:
            env: SimPy Environment
            server_id: Server identifier
            num_servers: Number of parallel servers
            logger: Centralized logger
            scheduling_policy: Scheduling policy ("FIFO", "SJF", "PRIORITY")
            gating_controller: Optional gating controller
        """
        self.env = env
        self.server_id = server_id
        self.num_servers = num_servers
        self.resource = simpy.Resource(env, capacity=num_servers)
        self.logger = logger
        self.scheduling_policy = scheduling_policy
        self.gating_controller = gating_controller
        
        # Custom queue
        self.custom_queue = PriorityQueue()
        
        # Statistics by job type
        self.stats_by_type = {}
    
    def _update_stats(self, job: Job, event: str):
        """Update statistics for a job type"""
        if job.job_type not in self.stats_by_type:
            self.stats_by_type[job.job_type] = {
                'arrivals': 0,
                'completed': 0,
                'rejected': 0,
                'total_waiting_time': 0.0,
                'total_service_time': 0.0,
                'total_response_time': 0.0
            }
        
        stats = self.stats_by_type[job.job_type]
        
        if event == 'arrival':
            stats['arrivals'] += 1
        elif event == 'completed':
            stats['completed'] += 1
            if job.get_waiting_time():
                stats['total_waiting_time'] += job.get_waiting_time()
            if job.service_time:
                stats['total_service_time'] += job.service_time
            if job.get_response_time():
                stats['total_response_time'] += job.get_response_time()
        elif event == 'rejected':
            stats['rejected'] += 1
    
    def process_job(self, 
                   job: Job,
                   service_time_generator: Callable[[], float]):
        """
        Process a job with gating and priority management
        
        Args:
            job: The job to process
            service_time_generator: Function generating the service time
        """
        # Gating verification
        if self.gating_controller and not self.gating_controller.is_open():
            # Attente de l'ouverture
            yield self.env.process(self.gating_controller.wait_until_open())
        
        # Enregistrement de l'arrivée
        self._update_stats(job, 'arrival')
        
        self.logger.log_event(
            time=self.env.now,
            event_type=EventType.ARRIVAL,
            entity_id=job.id,
            entity_type=job.job_type,
            server_id=self.server_id,
            queue_length=len(self.custom_queue)
        )
        
        # Generate service time for SJF
        service_time = service_time_generator()
        job.service_time = service_time
        
        # Add to custom queue
        self.custom_queue.add(job)
        
        # Wait for server
        with self.resource.request() as request:
            yield request
            
            # Retrieve job according to policy
            if self.scheduling_policy == "SJF":
                current_job = self.custom_queue.get_next_sjf()
            elif self.scheduling_policy == "PRIORITY":
                current_job = self.custom_queue.get_next_priority(["ING", "PREPA"])
            else:  # FIFO by default
                current_job = self.custom_queue.get_next_fifo()
            
            if current_job is None:
                return
            
            # Start of service
            current_job.start_time = self.env.now
            current_job.server_id = self.server_id
            
            self.logger.log_event(
                time=self.env.now,
                event_type=EventType.START_SERVICE,
                entity_id=current_job.id,
                entity_type=current_job.job_type,
                server_id=self.server_id,
                queue_length=len(self.custom_queue),
                extra_data={
                    'scheduling_policy': self.scheduling_policy,
                    'service_time': current_job.service_time
                }
            )
            
            # Execute service
            yield self.env.timeout(current_job.service_time)
            
            # End of service
            current_job.end_time = self.env.now
            self._update_stats(current_job, 'completed')
            
            self.logger.log_event(
                time=self.env.now,
                event_type=EventType.END_SERVICE,
                entity_id=current_job.id,
                entity_type=current_job.job_type,
                server_id=self.server_id,
                queue_length=len(self.custom_queue),
                extra_data={
                    'service_time': current_job.service_time,
                    'waiting_time': current_job.get_waiting_time(),
                    'response_time': current_job.get_response_time()
                }
            )
    
    def get_stats(self) -> dict:
        """Return statistics by job type"""
        result = {
            'server_id': self.server_id,
            'scheduling_policy': self.scheduling_policy,
            'by_type': {}
        }
        
        for job_type, stats in self.stats_by_type.items():
            completed = stats['completed']
            result['by_type'][job_type] = {
                'arrivals': stats['arrivals'],
                'completed': completed,
                'rejected': stats['rejected'],
                'avg_waiting_time': stats['total_waiting_time'] / completed if completed > 0 else 0.0,
                'avg_service_time': stats['total_service_time'] / completed if completed > 0 else 0.0,
                'avg_response_time': stats['total_response_time'] / completed if completed > 0 else 0.0
            }
        
        return result
