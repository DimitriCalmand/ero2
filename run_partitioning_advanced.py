
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
        
        self.exec_time_gen = lambda: random.expovariate(params['mu_exec'])
        
        # Total Capacity K distributed among servers
        # If Shared has K=40, Partitioned with 2 servers has 20 each.
        k_per_server = max(1, params['k_exec'] // self.num_servers)
        
        self.servers = []
        for i in range(self.num_servers):
            q = LimitedQueue(
                env=env,
                queue_id=f"partition_{i}",
                max_queue_size=k_per_server,
                num_servers=1,
                logger=logger,
                time_generator=self.exec_time_gen
            )
            self.servers.append(q)
            
    def generate_arrivals(self, duration):
        start_time = self.df_real['receivedAt'].iloc[0]
        
        for _, row in self.df_real.iterrows():
            arrival_time = (row['receivedAt'] - start_time).total_seconds()
            
            assignment = str(row['assignmentUri'])
            first_letter = assignment[0].lower() if assignment else '?'
            
            target_idx = self.partitions.get(first_letter, 0)
            
            delay = arrival_time - self.env.now
            if delay > 0:
                yield self.env.timeout(delay)
            
            if self.env.now > duration:
                break
                
            job = Job(arrival_time=self.env.now, job_type="REAL")
            job.assignment = assignment
            
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


def compute_partitions_balanced(df: pd.DataFrame, num_partitions: int):
    """Greedy balancing"""
    df['first_letter'] = df['assignmentUri'].astype(str).str[0].str.lower()
    counts = df['first_letter'].value_counts()
    sorted_items = counts.items()
    
    sums = [0] * num_partitions
    mapping = {}
    
    for letter, count in sorted_items:
        min_idx = sums.index(min(sums))
        sums[min_idx] += count
        mapping[letter] = min_idx
        
    return mapping, sums

def compute_partitions_alphabetical(df: pd.DataFrame, num_partitions: int):
    """Naive Alphabetical Split"""
    letters = sorted(list(set(df['assignmentUri'].astype(str).str[0].str.lower())))
    chunk_size = len(letters) // num_partitions + 1
    
    mapping = {}
    sums = [0] * num_partitions
    
    # Just to count load
    counts = df['assignmentUri'].astype(str).str[0].str.lower().value_counts()
    
    for i, letter in enumerate(letters):
        p_idx = min(i // chunk_size, num_partitions - 1)
        mapping[letter] = p_idx
        sums[p_idx] += counts.get(letter, 0)
        
    return mapping, sums

def run_simulation():
    print("Loading data...")
    df = pd.read_csv("tags")
    df['receivedAt'] = pd.to_datetime(df['receivedAt'])
    df = df.sort_values('receivedAt')
    duration = (df['receivedAt'].max() - df['receivedAt'].min()).total_seconds()
    
    # Configurations
    server_counts = [2, 3, 4]
    
    # We want to stress the system.
    # To compare C=2,3,4 we need a load that is "too much" for C=2 but "okay" for C=4?
    # Or just "Heavy" for all.
    # 0.022 was good for C=2 saturation.
    # Let's keep mu constant per server. Total capacity grows with C.
    mu_sim = 0.022 
    k_total = 40
    
    results = []
    
    for c in server_counts:
        print(f"\n--- Testing with {c} Servers ---")
        params = {'mu_exec': mu_sim, 'num_servers': c, 'k_exec': k_total}
        
        # 1. Shared
        print(f"  Running Shared c={c}...")
        random.seed(SEED)
        engine = SimulationEngine(random_seed=SEED)
        sim = SharedWaterfallScenario(engine.env, engine.logger, params, df)
        engine.env.process(sim.generate_arrivals(duration))
        engine.run(duration)
        
        res = engine.get_results()
        completed = len(res[res['event_type'] == EventType.END_SERVICE.value])
        rejected = len(res[res['event_type'] == EventType.REJECTION.value])
        
        results.append({
            'Servers': c,
            'Strategy': 'Shared (Optimal)',
            'Completed': completed,
            'Rejected': rejected,
            'Load Imbalance': 0.0
        })
        
        # 2. Balanced Partition
        print(f"  Running Partitioned (Balanced) c={c}...")
        map_bal, sums_bal = compute_partitions_balanced(df, c)
        imbalance_bal = (max(sums_bal) - min(sums_bal)) / sum(sums_bal)
        
        random.seed(SEED)
        engine = SimulationEngine(random_seed=SEED)
        sim = PartitionedWaterfallScenario(engine.env, engine.logger, params, map_bal, df)
        engine.env.process(sim.generate_arrivals(duration))
        engine.run(duration)
        
        res = engine.get_results()
        completed = len(res[res['event_type'] == EventType.END_SERVICE.value])
        rejected = len(res[res['event_type'] == EventType.REJECTION.value])
        
        results.append({
            'Servers': c,
            'Strategy': 'Part. Balanced',
            'Completed': completed,
            'Rejected': rejected,
            'Load Imbalance': imbalance_bal
        })
        
        # 3. Naive Partition (Alphabetical)
        print(f"  Running Partitioned (Naive) c={c}...")
        map_naive, sums_naive = compute_partitions_alphabetical(df, c)
        imbalance_naive = (max(sums_naive) - min(sums_naive)) / sum(sums_naive)
        
        random.seed(SEED)
        engine = SimulationEngine(random_seed=SEED)
        sim = PartitionedWaterfallScenario(engine.env, engine.logger, params, map_naive, df)
        engine.env.process(sim.generate_arrivals(duration))
        engine.run(duration)
        
        res = engine.get_results()
        completed = len(res[res['event_type'] == EventType.END_SERVICE.value])
        rejected = len(res[res['event_type'] == EventType.REJECTION.value])
        
        results.append({
            'Servers': c,
            'Strategy': 'Part. Naive',
            'Completed': completed,
            'Rejected': rejected,
            'Load Imbalance': imbalance_naive
        })

    # Output
    summary_df = pd.DataFrame(results)
    summary_df['Throughput'] = summary_df['Completed'] / duration
    summary_df['Rejection Rate'] = summary_df['Rejected'] / (summary_df['Rejected'] + summary_df['Completed'])
    
    print("\nResults Summary:")
    print(summary_df[['Servers', 'Strategy', 'Completed', 'Rejected', 'Load Imbalance', 'Rejection Rate']])
    summary_df.to_csv(RESULTS_DIR / "partitioning_advanced.csv", index=False)
    
    # Plot Rejection Rate
    plt.figure(figsize=(10, 6))
    sns.barplot(data=summary_df, x='Servers', y='Rejection Rate', hue='Strategy')
    plt.title("Rejection Rate by Strategy and Server Count")
    plt.ylabel("Rejection Rate")
    plt.savefig(RESULTS_DIR / "partitioning_rejection.png")

if __name__ == "__main__":
    run_simulation()
