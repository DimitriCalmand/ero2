
import simpy
import pandas as pd
import random
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from typing import Dict, List, Any

from src.core import SimulationEngine, Job, SimulationLogger, EventType
from src.capacity import LimitedQueue
from src.analysis import RealDataComparator

# --- Configuration ---
RESULTS_DIR = Path("results/partitioning")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
SEED = 42

class PartitionedWaterfallScenario:
    def __init__(self, 
                 env: simpy.Environment, 
                 logger: SimulationLogger,
                 params: dict,
                 partitions: Dict[str, int], # Map 'a' -> 0, 'b' -> 1
                 df_real: pd.DataFrame):
        
        self.env = env
        self.logger = logger
        self.params = params
        self.partitions = partitions
        self.df_real = df_real
        self.num_servers = params['num_servers']
        
        # Service Generators
        self.exec_time_gen = lambda: random.expovariate(params['mu_exec'])
        
        # Create Servers (Partitioned Queues)
        # Each server has its own queue with capacity K/c to be fair?
        # Or same K? Usually partitioning splits resources, so capacity K might be split or kept same.
        # Let's assume each partition gets a dedicated queue of size K_total / c
        k_per_server = params['k_exec'] // self.num_servers
        
        self.servers = []
        for i in range(self.num_servers):
            q = LimitedQueue(
                env=env,
                queue_id=f"partition_{i}",
                max_queue_size=k_per_server,
                num_servers=1, # Dedicated server
                logger=logger,
                time_generator=self.exec_time_gen
            )
            self.servers.append(q)
            
    def generate_arrivals(self, duration):
        start_time = self.df_real['receivedAt'].iloc[0]
        
        for _, row in self.df_real.iterrows():
            arrival_time = (row['receivedAt'] - start_time).total_seconds()
            
            # Assignment/Tag
            assignment = str(row['assignmentUri'])
            first_letter = assignment[0].lower() if assignment else '?'
            
            # Determine target server
            target_idx = self.partitions.get(first_letter, 0) # Default to 0 if unknown
            
            # Wait
            delay = arrival_time - self.env.now
            if delay > 0:
                yield self.env.timeout(delay)
            
            if self.env.now > duration:
                break
                
            job = Job(arrival_time=self.env.now, job_type="REAL")
            job.assignment = assignment # For tracking
            
            # Route to specific server
            self.env.process(self.servers[target_idx].process_job(job))

class SharedWaterfallScenario:
    def __init__(self, 
                 env: simpy.Environment, 
                 logger: SimulationLogger,
                 params: dict,
                 df_real: pd.DataFrame):
        
        self.env = env
        self.logger = logger
        self.df_real = df_real
        
        self.exec_time_gen = lambda: random.expovariate(params['mu_exec'])
        
        # Shared Queue with C servers
        self.queue = LimitedQueue(
            env=env,
            queue_id="shared_pool",
            max_queue_size=params['k_exec'],
            num_servers=params['num_servers'],
            logger=logger,
            time_generator=self.exec_time_gen
        )
            
    def generate_arrivals(self, duration):
        start_time = self.df_real['receivedAt'].iloc[0]
        
        for _, row in self.df_real.iterrows():
            arrival_time = (row['receivedAt'] - start_time).total_seconds()
            
            delay = arrival_time - self.env.now
            if delay > 0:
                yield self.env.timeout(delay)
            
            if self.env.now > duration:
                break
                
            job = Job(arrival_time=self.env.now, job_type="REAL")
            self.env.process(self.queue.process_job(job))


def compute_partitions(df: pd.DataFrame, num_partitions: int):
    # Count frequencies of first letters
    df['first_letter'] = df['assignmentUri'].astype(str).str[0].str.lower()
    counts = df['first_letter'].value_counts()
    
    # Greedy partition
    # Sort counts desc
    sorted_items = counts.items()
    
    partitions = [[] for _ in range(num_partitions)]
    sums = [0] * num_partitions
    
    mapping = {}
    
    for letter, count in sorted_items:
        # Assign to the partition with the lowest current sum
        min_idx = sums.index(min(sums))
        partitions[min_idx].append(letter)
        sums[min_idx] += count
        mapping[letter] = min_idx
        
    print("Partitioning Strategy:")
    for i, p in enumerate(partitions):
        print(f"  Server {i}: {len(p)} letters, {sums[i]} jobs ({sums[i]/sum(sums):.1%})")
        # print(f"    Letters: {p}")
        
    return mapping

def run_simulation():
    # Load Data
    print("Loading data...")
    df = pd.read_csv("tags")
    df['receivedAt'] = pd.to_datetime(df['receivedAt'])
    df = df.sort_values('receivedAt')
    
    # Parameters
    # We need to simulate a load where C=2 is "just enough" or slightly saturated
    # to see the difference.
    # Estimated real lambda is ~0.037.
    # If we run at real speed, 2 servers is overkill (rho ~ 0.01).
    # We need to ACCELERATE the arrival rate or SLOW DOWN the service rate 
    # to highlight the inefficiency of partitioning.
    # Let's slow down service rate significantly.
    # Try to target rho ~ 0.85 with Shared.
    # lambda = 0.037
    # mu * 2 * 0.85 = 0.037 => mu = 0.037 / (2 * 0.85) = 0.021
    
    mu_sim = 0.022  # Slow servers to create contention
    num_servers = 2
    k_total = 40
    
    params = {
        'mu_exec': mu_sim,
        'num_servers': num_servers,
        'k_exec': k_total
    }
    
    duration = (df['receivedAt'].max() - df['receivedAt'].min()).total_seconds()
    
    # 1. Compute Partitions
    partitions_map = compute_partitions(df, num_servers)
    
    results = []
    
    # Run Shared
    print("\nRunning Shared Simulation...")
    random.seed(SEED)
    engine = SimulationEngine(random_seed=SEED)
    sim = SharedWaterfallScenario(engine.env, engine.logger, params, df)
    engine.env.process(sim.generate_arrivals(duration))
    engine.run(duration)
    
    res_df = engine.get_results()
    completed = res_df[res_df['event_type'] == EventType.END_SERVICE.value]
    rejected = res_df[res_df['event_type'] == EventType.REJECTION.value]
    avg_resp_shared = completed['response_time'].mean() if len(completed) > 0 else 0
    
    results.append({
        'Scenario': 'Shared (M/M/2)',
        'Avg Response Time': avg_resp_shared,
        'Jobs Completed': len(completed),
        'Jobs Rejected': len(rejected)
    })
    
    # Run Partitioned
    print("Running Partitioned Simulation...")
    random.seed(SEED)
    engine = SimulationEngine(random_seed=SEED)
    sim = PartitionedWaterfallScenario(engine.env, engine.logger, params, partitions_map, df)
    engine.env.process(sim.generate_arrivals(duration))
    engine.run(duration)
    
    res_df = engine.get_results()
    completed = res_df[res_df['event_type'] == EventType.END_SERVICE.value]
    rejected = res_df[res_df['event_type'] == EventType.REJECTION.value]
    avg_resp_part = completed['response_time'].mean() if len(completed) > 0 else 0
    
    results.append({
        'Scenario': 'Partitioned (2 x M/M/1)',
        'Avg Response Time': avg_resp_part,
        'Jobs Completed': len(completed),
        'Jobs Rejected': len(rejected)
    })
    
    # Output
    summary_df = pd.DataFrame(results)
    print("\nResults:")
    print(summary_df)
    summary_df.to_csv(RESULTS_DIR / "partitioning_results.csv", index=False)
    
    # Plot
    plt.figure(figsize=(8, 6))
    sns.barplot(data=summary_df, x='Scenario', y='Avg Response Time')
    plt.title("Impact of Server Partitioning on Response Time")
    plt.ylabel("Avg Response Time (s)")
    plt.savefig(RESULTS_DIR / "partitioning_impact.png")

if __name__ == "__main__":
    run_simulation()
