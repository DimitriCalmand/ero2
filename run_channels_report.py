import simpy
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from src.core import SimulationEngine
from src.regulation import ChannelsScenario, GatingAnalyzer

# Setup
RESULTS_DIR = Path("results/channels_report")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
DURATION = 2000
SEED = 42

def run_channels_policies():
    print("--- Running Channels Policies Comparison ---")
    
    lambda_ing = 1.5
    lambda_prepa = 0.5
    mu_ing = 2.5
    mu_prepa = 2.0
    num_servers = 2
    
    policies = ["FIFO", "SJF", "PRIORITY"]
    results = []
    
    for policy in policies:
        print(f"Testing {policy}...")
        engine = SimulationEngine(random_seed=SEED)
        scenario = ChannelsScenario(
            env=engine.env,
            logger=engine.logger,
            num_servers=num_servers,
            scheduling_policy=policy
        )
        
        scenario.add_population("ING", lambda_ing, mu_ing)
        scenario.add_population("PREPA", lambda_prepa, mu_prepa)
        
        scenario.run(DURATION)
        
        # Extract stats
        stats = scenario.server.get_stats()
        for pop, data in stats['by_type'].items():
            results.append({
                'Policy': policy,
                'Population': pop,
                'Avg Response Time': data['avg_response_time'],
                'Avg Waiting Time': data['avg_waiting_time'],
                'Completed': data['completed']
            })
            
    df = pd.DataFrame(results)
    df.to_csv(RESULTS_DIR / "policies_comparison.csv", index=False)
    
    # Plot
    plt.figure(figsize=(10, 6))
    sns.barplot(data=df, x='Policy', y='Avg Response Time', hue='Population')
    plt.title("Impact of Scheduling Policy on Response Time")
    plt.ylabel("Avg Response Time (units)")
    plt.savefig(RESULTS_DIR / "policies_impact.png")
    print(f"Policies results saved to {RESULTS_DIR}")
    return df

def run_gating_impact():
    print("\n--- Running Gating Impact Analysis ---")
    
    lambda_ing = 1.5
    lambda_prepa = 0.5
    mu_ing = 2.5
    mu_prepa = 2.0
    num_servers = 2
    
    # Configuration "Standard" from report
    tb = 100
    opening = 50
    # Intervals: (0, 100), (150, 250), (300, 400)...
    # Let's generate them for the duration
    intervals = []
    current = 0
    while current < DURATION:
        intervals.append((current, current + tb))
        current += tb + opening
        
    configurations = [
        {"name": "No Gating", "use_gating": False, "intervals": None},
        {"name": "With Gating", "use_gating": True, "intervals": intervals}
    ]
    
    results = []
    
    for config in configurations:
        print(f"Testing {config['name']}...")
        engine = SimulationEngine(random_seed=SEED)
        scenario = ChannelsScenario(
            env=engine.env,
            logger=engine.logger,
            num_servers=num_servers,
            scheduling_policy="FIFO",
            use_gating=config['use_gating'],
            gating_intervals=config['intervals']
        )
        
        scenario.add_population("ING", lambda_ing, mu_ing)
        scenario.add_population("PREPA", lambda_prepa, mu_prepa)
        
        scenario.run(DURATION)
        
        stats = scenario.server.get_stats()
        for pop, data in stats['by_type'].items():
            results.append({
                'Configuration': config['name'],
                'Population': pop,
                'Avg Response Time': data['avg_response_time']
            })
            
    df = pd.DataFrame(results)
    df.to_csv(RESULTS_DIR / "gating_impact.csv", index=False)
    
    # Plot
    plt.figure(figsize=(8, 6))
    sns.barplot(data=df, x='Configuration', y='Avg Response Time', hue='Population')
    plt.title("Impact of Gating on Response Time")
    plt.ylabel("Avg Response Time (units)")
    plt.savefig(RESULTS_DIR / "gating_impact.png")
    print(f"Gating results saved to {RESULTS_DIR}")
    return df

def run_optimization_proposal():
    print("\n--- Running Optimization Proposal (Reduced Gating) ---")
    
    # Use the GatingAnalyzer to find a better config
    lambda_ing = 1.5
    lambda_prepa = 0.5
    mu_ing = 2.5
    mu_prepa = 2.0
    num_servers = 2
    
    analyzer = GatingAnalyzer(lambda_ing, mu_ing, lambda_prepa, mu_prepa, num_servers)
    
    # We test shorter blocking times to allow more frequent flushing
    tb_values = [20, 40, 60, 80, 100]
    # We test higher opening ratios (more time open vs closed)
    # Ratio = Opening Duration / Blocking Duration
    # Current was 50/100 = 0.5
    ratio_values = [0.5, 0.75, 1.0, 1.5]
    
    results_df = analyzer.analyze_gating_variations(
        tb_values=tb_values,
        ratio_values=ratio_values,
        duration=DURATION,
        seed=SEED
    )
    
    # Save Heatmaps
    analyzer.plot_gating_impact(results_df, output_dir=str(RESULTS_DIR))
    
    # Find best compromise
    # We want minimal increase compared to baseline, but we assume Gating is mandatory for some reason (maintenance? batching?)
    # If Gating is for "maintenance", we need a certain total closed time.
    # If Gating is for "grouping", we might want specific tb.
    # Let's assume we want to minimize Response Time while keeping 'tb' (blocking chunk) reasonable if required,
    # OR just find the configuration that minimizes impact.
    
    rec = analyzer.recommend_gating_config(results_df)
    
    with open(RESULTS_DIR / "recommendation.txt", "w") as f:
        f.write(str(rec))
        
    print("Optimization done.")
    return rec

if __name__ == "__main__":
    run_channels_policies()
    run_gating_impact()
    run_optimization_proposal()
