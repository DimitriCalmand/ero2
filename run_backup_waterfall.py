import simpy
import random
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Optional, Callable, Generator
from pathlib import Path

from src.core import SimulationEngine, Job, SimulationLogger, EventType
from src.capacity import LimitedQueue
from src.analysis import RealDataComparator

# --- Configuration ---
RESULTS_DIR = Path("results/backup_waterfall")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

class BackupWaterfallScenario:
    def __init__(self, 
                 env: simpy.Environment, 
                 logger: SimulationLogger,
                 params: dict,
                 backup_strategy: str = "systematic", # systematic, random_50, random_20
                 real_data_df: Optional[pd.DataFrame] = None):
        
        self.env = env
        self.logger = logger
        self.params = params
        self.real_data_df = real_data_df
        
        # Strategy config
        self.backup_prob = 1.0
        if backup_strategy == "random_50":
            self.backup_prob = 0.5
        elif backup_strategy == "random_20":
            self.backup_prob = 0.2
            
        # Generators
        self.exec_time_gen = lambda: random.expovariate(params['mu_exec'])
        self.backup_time_gen = lambda: random.expovariate(params['mu_backup'])
        self.feed_time_gen = lambda: random.expovariate(params['mu_feed'])
        
        # Queues
        # Feedback (Last stage)
        self.feedback_queue = LimitedQueue(
            env=env,
            queue_id="feedback",
            max_queue_size=params['k_feed'],
            num_servers=1,
            logger=logger,
            time_generator=self.feed_time_gen
        )
        
        # Backup (Middle stage)
        # We wrap the backup processing to handle probability
        def _backup_process_wrapper(job):
            # Decide if backup is needed
            if random.random() < self.backup_prob:
                job.assignment = "backup_needed" # Mark for stats
                yield from self.backup_queue.process_job(job)
            else:
                job.assignment = "skipped_backup"
                # Skip backup, go directly to feedback
                yield from self.feedback_queue.process_job(job)

        self.backup_queue = LimitedQueue(
            env=env,
            queue_id="backup",
            max_queue_size=params['k_backup'],
            num_servers=params['c_backup'],
            logger=logger,
            time_generator=self.backup_time_gen,
            on_done=self.feedback_queue.process_job
        )
        
        # Execution (First stage)
        self.execution_queue = LimitedQueue(
            env=env,
            queue_id="execution",
            max_queue_size=params['k_exec'],
            num_servers=params['c_exec'],
            logger=logger,
            time_generator=self.exec_time_gen,
            on_done=_backup_process_wrapper
        )
        
    def generate_arrivals(self, duration):
        if self.real_data_df is not None:
            # Replay real data
            # We assume df has 'interarrival_time' or we calculate relative times
            # Let's use exact timestamps relative to start
            start_time = self.real_data_df['receivedAt'].iloc[0]
            for _, row in self.real_data_df.iterrows():
                arrival_time = (row['receivedAt'] - start_time).total_seconds()
                
                # Wait until arrival time
                delay = arrival_time - self.env.now
                if delay > 0:
                    yield self.env.timeout(delay)
                
                if self.env.now > duration:
                    break
                    
                job = Job(arrival_time=self.env.now, job_type="REAL")
                self.logger.log_event(
                    time=self.env.now,
                    event_type=EventType.ARRIVAL,
                    entity_id=job.id,
                    entity_type=job.job_type,
                    server_id="generator",
                    queue_length=0
                )
                self.env.process(self.execution_queue.process_job(job))
        else:
            # Poisson process
            while self.env.now < duration:
                yield self.env.timeout(random.expovariate(self.params['lambda']))
                job = Job(arrival_time=self.env.now, job_type="RANDOM")
                self.logger.log_event(
                    time=self.env.now,
                    event_type=EventType.ARRIVAL,
                    entity_id=job.id,
                    entity_type=job.job_type,
                    server_id="generator",
                    queue_length=0
                )
                self.env.process(self.execution_queue.process_job(job))

def run_simulation(strategy, use_real_data=False):
    seed = 42
    random.seed(seed)
    duration = 2000 if not use_real_data else 100000 # Enough for real data
    
    # Parameters
    params = {
        'lambda': 2.0,       # Avg arrival for random
        'mu_exec': 2.5,      # Execution rate
        'mu_backup': 10.0,   # Fast backup
        'mu_feed': 1.5,      # Feedback rate (bottleneck usually)
        'c_exec': 2,
        'c_backup': 1,
        'k_exec': 20,
        'k_backup': 20,      # Buffer for backup
        'k_feed': 20
    }
    
    real_df = None
    if use_real_data:
        real_df = RealDataComparator.load_real_data("tags")
        # Adjust lambda for info, but simulation uses timestamps
        duration = (real_df['receivedAt'].max() - real_df['receivedAt'].min()).total_seconds() + 100
    
    engine = SimulationEngine(random_seed=seed)
    scenario = BackupWaterfallScenario(
        engine.env, 
        engine.logger, 
        params, 
        strategy, 
        real_df
    )
    
    engine.env.process(scenario.generate_arrivals(duration))
    engine.run(duration)
    
    df = engine.get_results()
    
    # Calculate stats
    total_jobs = len(df[df['event_type'] == EventType.ARRIVAL.value])
    
    # Exec stats
    exec_completed = len(df[(df['event_type'] == EventType.END_SERVICE.value) & (df['server_id'] == 'execution')])
    exec_rejected = len(df[(df['event_type'] == EventType.REJECTION.value) & (df['server_id'] == 'execution')])
    
    # Backup stats
    backup_attempts = len(df[(df['event_type'] == EventType.START_SERVICE.value) & (df['server_id'] == 'backup')])
    backup_completed = len(df[(df['event_type'] == EventType.END_SERVICE.value) & (df['server_id'] == 'backup')])
    backup_rejected = len(df[(df['event_type'] == EventType.REJECTION.value) & (df['server_id'] == 'backup')])
    
    # Feedback stats
    feed_completed = len(df[(df['event_type'] == EventType.END_SERVICE.value) & (df['server_id'] == 'feedback')])
    feed_rejected = len(df[(df['event_type'] == EventType.REJECTION.value) & (df['server_id'] == 'feedback')])
    
    # Response Time (End-to-End)
    # Filter for jobs that finished feedback (fully completed)
    finished_jobs = df[(df['event_type'] == EventType.END_SERVICE.value) & (df['server_id'] == 'feedback')]
    # Join with arrival time is complex in pure pandas event log without job grouping, 
    # but Job object tracks end_time.
    # The logger 'extra_data' has 'response_time' but that is per server (local response time).
    # We need global response time.
    # Fortunately, the END_SERVICE event for feedback contains the job_id.
    # We can calculate global response time: Time of Feedback End - Time of Arrival.
    
    # Let's extract per-job data
    jobs_data = {}
    for r in df.to_dict('records'):
        jid = r['entity_id']
        if jid not in jobs_data:
            jobs_data[jid] = {'arrival': None, 'end': None, 'status': 'unknown'}
        
        if r['event_type'] == EventType.ARRIVAL.value:
            jobs_data[jid]['arrival'] = r['time']
        elif r['event_type'] == EventType.END_SERVICE.value and r['server_id'] == 'feedback':
            jobs_data[jid]['end'] = r['time']
            jobs_data[jid]['status'] = 'completed'
        elif r['event_type'] == EventType.REJECTION.value:
             jobs_data[jid]['status'] = 'rejected_' + str(r['server_id'])

    response_times = []
    for jid, data in jobs_data.items():
        if data['status'] == 'completed' and data['arrival'] is not None and data['end'] is not None:
            response_times.append(data['end'] - data['arrival'])
            
    avg_response_time = sum(response_times) / len(response_times) if response_times else 0
    
    return {
        'strategy': strategy,
        'data_type': 'Real' if use_real_data else 'Synthetic',
        'total_arrivals': total_jobs,
        'exec_rejection_rate': exec_rejected / total_jobs if total_jobs else 0,
        'backup_processed': backup_completed,
        'backup_rejection_rate': backup_rejected / (exec_completed) if exec_completed else 0,
        'feed_rejection_rate': feed_rejected / (exec_completed) if exec_completed else 0, # Approximation of flow
        'final_throughput': feed_completed / duration,
        'avg_response_time': avg_response_time,
        'raw_df': df
    }

# Run All
results = []
strategies = ["systematic", "random_50", "random_20"]

print("Running Synthetic Data Simulations...")
for s in strategies:
    print(f"  - {s}")
    res = run_simulation(s, use_real_data=False)
    results.append(res)

print("\nRunning Real Data Simulations...")
for s in strategies:
    print(f"  - {s}")
    res = run_simulation(s, use_real_data=True)
    results.append(res)

# Export Summary
summary_df = pd.DataFrame([{k:v for k,v in r.items() if k != 'raw_df'} for r in results])
print("\nSummary:")
print(summary_df)
summary_df.to_csv(RESULTS_DIR / "backup_summary.csv", index=False)

# Plotting Response Times
plt.figure(figsize=(10, 6))
sns.barplot(data=summary_df, x='strategy', y='avg_response_time', hue='data_type')
plt.title("Impact of Backup Strategy on Average Response Time")
plt.ylabel("Avg Response Time (s)")
plt.savefig(RESULTS_DIR / "backup_impact_time.png")

# Plotting Rejection Rates (Global - approximation)
# Let's sum rejections? Or just look at feedback/backup rejections.
# Usually backup rejection implies data loss, not user rejection (depends on architecture).
# Assuming backup rejection = lost data but user "finished".
# But here LimitedQueue rejects if full.
# Let's plot Execution Rejection (Entry Rejection)
plt.figure(figsize=(10, 6))
sns.barplot(data=summary_df, x='strategy', y='exec_rejection_rate', hue='data_type')
plt.title("Impact of Backup Strategy on Entry Rejection Rate")
plt.ylabel("Rejection Rate")
plt.savefig(RESULTS_DIR / "backup_impact_rejection.png")
