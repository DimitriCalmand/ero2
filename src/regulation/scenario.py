"""
Complete scenario with multiple populations and regulation strategies
"""

import simpy
from typing import Optional, List
from src.core.simulation_engine import SimulationLogger
from .gating import GatingController
from .server import HeterogeneousServer
from .population import PopulationGenerator


class ChannelsScenario:
    """
    Complete scenario with multiple populations and regulation strategies
    """
    
    def __init__(self,
                 env: simpy.Environment,
                 logger: SimulationLogger,
                 num_servers: int,
                 scheduling_policy: str = "FIFO",
                 use_gating: bool = False,
                 gating_intervals: Optional[List[tuple]] = None):
        """
        Args:
            env: SimPy Environment
            logger: Centralized logger
            num_servers: Number of servers
            scheduling_policy: Scheduling policy
            use_gating: Enable gating
            gating_intervals: Closure intervals
        """
        self.env = env
        self.logger = logger
        
        # Gating controller
        gating_controller = None
        if use_gating and gating_intervals:
            gating_controller = GatingController(env, gating_intervals)
        
        # Heterogeneous server
        self.server = HeterogeneousServer(
            env=env,
            server_id="channels_server",
            num_servers=num_servers,
            logger=logger,
            scheduling_policy=scheduling_policy,
            gating_controller=gating_controller
        )
        
        self.populations = {}
    
    def add_population(self,
                      population_type: str,
                      arrival_rate: float,
                      service_rate: float):
        """
        Add a population
        
        Args:
            population_type: Population type
            arrival_rate: Arrival rate
            service_rate: Service rate
        """
        gen = PopulationGenerator(
            env=self.env,
            logger=self.logger,
            population_type=population_type,
            arrival_rate=arrival_rate,
            service_rate=service_rate
        )
        self.populations[population_type] = gen
    
    def run(self, duration: float) -> dict:
        """
        Execute the scenario
        
        Args:
            duration: Simulation duration
            
        Returns:
            Statistics by population
        """
        # Launch generators
        for pop_type, generator in self.populations.items():
            self.env.process(generator.generate(self.server, duration))
        
        # Execution
        self.env.run(until=duration)
        
        # Results
        return self.server.get_stats()
