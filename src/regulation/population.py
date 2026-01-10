"""
Generator for a specific population (ING or PREPA)
"""

import simpy
import random
from src.core.simulation_engine import SimulationLogger, Job


class PopulationGenerator:
    """
    Generator for a specific population (ING or PREPA)
    """
    
    def __init__(self,
                 env: simpy.Environment,
                 logger: SimulationLogger,
                 population_type: str,
                 arrival_rate: float,
                 service_rate: float):
        """
        Args:
            env: SimPy Environment
            logger: Centralized logger
            population_type: Population type ("ING" or "PREPA")
            arrival_rate: Arrival rate λ
            service_rate: Service rate μ
        """
        self.env = env
        self.logger = logger
        self.population_type = population_type
        self.arrival_rate = arrival_rate
        self.service_rate = service_rate
        self.jobs_generated = 0
    
    def generate(self, server, duration: float):
        """
        Generate jobs for this population
        
        Args:
            server: Server that will process the jobs (HeterogeneousServer)
            duration: Simulation duration
        """
        def service_time_gen():
            return random.expovariate(self.service_rate)
        
        while self.env.now < duration:
            # Inter-arrival time
            interarrival = random.expovariate(self.arrival_rate)
            yield self.env.timeout(interarrival)
            
            if self.env.now >= duration:
                break
            
            # Job creation
            job = Job(
                arrival_time=self.env.now,
                job_type=self.population_type,
                assignment=f"{self.population_type}_{self.jobs_generated}"
            )
            self.jobs_generated += 1
            
            # Processing
            self.env.process(server.process_job(job, service_time_gen))
