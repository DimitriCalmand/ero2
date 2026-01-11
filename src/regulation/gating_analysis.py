"""
Advanced gating analysis with multiple configurations
"""

import simpy
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from typing import List, Dict, Tuple, Optional
from pathlib import Path

from src.core.simulation_engine import SimulationEngine
from .scenario import ChannelsScenario


class GatingAnalyzer:
    """
    Analyzer for gating configurations and their impact
    """
    
    def __init__(self,
                 lambda_ing: float,
                 mu_ing: float,
                 lambda_prepa: float,
                 mu_prepa: float,
                 num_servers: int):
        """
        Args:
            lambda_ing: ING arrival rate
            mu_ing: ING service rate
            lambda_prepa: PREPA arrival rate
            mu_prepa: PREPA service rate
            num_servers: Number of servers
        """
        self.lambda_ing = lambda_ing
        self.mu_ing = mu_ing
        self.lambda_prepa = lambda_prepa
        self.mu_prepa = mu_prepa
        self.num_servers = num_servers
    
    def generate_gating_intervals(self, 
                                  tb: int, 
                                  opening_duration: int,
                                  total_duration: float) -> List[Tuple[float, float]]:
        """
        Generate gating intervals for a simulation
        
        Args:
            tb: Blocking duration
            opening_duration: Opening duration
            total_duration: Total simulation duration
            
        Returns:
            List of (start, end) tuples for closed periods
        """
        intervals = []
        current_time = 0
        
        while current_time < total_duration:
            # Closed period
            start = current_time
            end = current_time + tb
            if end > total_duration:
                end = total_duration
            intervals.append((start, end))
            
            # Skip opening period
            current_time = end + opening_duration
        
        return intervals
    
    def run_single_configuration(self,
                                 tb: int,
                                 ratio: float,
                                 duration: float,
                                 seed: int = 42) -> Dict:
        """
        Run simulation with a single gating configuration
        
        Args:
            tb: Blocking duration
            ratio: Opening duration ratio (0.25 = tb/4, 0.5 = tb/2, etc.)
            duration: Simulation duration
            seed: Random seed
            
        Returns:
            Statistics dictionary
        """
        opening_duration = int(tb * ratio)
        intervals = self.generate_gating_intervals(tb, opening_duration, duration)
        
        # Run with gating
        engine = SimulationEngine(random_seed=seed)
        scenario = ChannelsScenario(
            env=engine.env,
            logger=engine.logger,
            num_servers=self.num_servers,
            scheduling_policy="FIFO",
            use_gating=True,
            gating_intervals=intervals
        )
        
        scenario.add_population("ING", self.lambda_ing, self.mu_ing)
        scenario.add_population("PREPA", self.lambda_prepa, self.mu_prepa)
        
        stats = scenario.run(duration)
        
        # Calculate additional metrics
        df = engine.logger.get_dataframe()
        queue_lengths = df[df['queue_length'].notna()]['queue_length']
        
        return {
            'tb': tb,
            'ratio': ratio,
            'opening_duration': opening_duration,
            'num_intervals': len(intervals),
            'ing_avg_response_time': stats['by_type']['ING']['avg_response_time'],
            'prepa_avg_response_time': stats['by_type']['PREPA']['avg_response_time'],
            'ing_completed': stats['by_type']['ING']['completed'],
            'prepa_completed': stats['by_type']['PREPA']['completed'],
            'max_queue_length': queue_lengths.max() if len(queue_lengths) > 0 else 0,
            'avg_queue_length': queue_lengths.mean() if len(queue_lengths) > 0 else 0
        }
    
    def analyze_gating_variations(self,
                                  tb_values: List[int],
                                  ratio_values: List[float],
                                  duration: float = 1000.0,
                                  seed: int = 42) -> pd.DataFrame:
        """
        Analyze multiple gating configurations
        
        Args:
            tb_values: List of blocking durations to test
            ratio_values: List of opening ratios to test
            duration: Simulation duration
            seed: Random seed
            
        Returns:
            DataFrame with results for all configurations
        """
        # Run reference without gating
        engine_ref = SimulationEngine(random_seed=seed)
        scenario_ref = ChannelsScenario(
            env=engine_ref.env,
            logger=engine_ref.logger,
            num_servers=self.num_servers,
            scheduling_policy="FIFO",
            use_gating=False
        )
        scenario_ref.add_population("ING", self.lambda_ing, self.mu_ing)
        scenario_ref.add_population("PREPA", self.lambda_prepa, self.mu_prepa)
        stats_ref = scenario_ref.run(duration)
        
        ref_ing_time = stats_ref['by_type']['ING']['avg_response_time']
        ref_prepa_time = stats_ref['by_type']['PREPA']['avg_response_time']
        
        results = []
        
        for tb in tb_values:
            for ratio in ratio_values:
                print(f"Testing: tb={tb}, ratio={ratio:.2f}")
                
                stats = self.run_single_configuration(tb, ratio, duration, seed)
                
                # Calculate percentage increase
                stats['ing_time_increase_pct'] = (
                    (stats['ing_avg_response_time'] - ref_ing_time) / ref_ing_time * 100
                )
                stats['prepa_time_increase_pct'] = (
                    (stats['prepa_avg_response_time'] - ref_prepa_time) / ref_prepa_time * 100
                )
                
                # Calculate accumulated jobs during closure
                closure_fraction = tb / (tb + stats['opening_duration'])
                accumulated_rate = self.lambda_ing + self.lambda_prepa
                stats['expected_accumulation'] = accumulated_rate * tb * closure_fraction
                
                results.append(stats)
        
        df = pd.DataFrame(results)
        df['reference_ing_time'] = ref_ing_time
        df['reference_prepa_time'] = ref_prepa_time
        
        return df
    
    def plot_gating_impact(self,
                          results_df: pd.DataFrame,
                          output_dir: str = "gating_analysis") -> None:
        """
        Generate visualization of gating impact
        
        Args:
            results_df: Results from analyze_gating_variations
            output_dir: Output directory for plots
        """
        Path(output_dir).mkdir(exist_ok=True)
        
        # 1. Heatmap: ING response time increase
        fig, axes = plt.subplots(2, 2, figsize=(14, 12))
        
        # Pivot for heatmaps
        pivot_ing_time = results_df.pivot(
            index='ratio', 
            columns='tb', 
            values='ing_time_increase_pct'
        )
        pivot_prepa_time = results_df.pivot(
            index='ratio', 
            columns='tb', 
            values='prepa_time_increase_pct'
        )
        pivot_queue = results_df.pivot(
            index='ratio',
            columns='tb',
            values='max_queue_length'
        )
        pivot_throughput = results_df.pivot(
            index='ratio',
            columns='tb',
            values='ing_completed'
        )
        
        # ING time increase
        sns.heatmap(pivot_ing_time, annot=True, fmt='.0f', cmap='YlOrRd',
                   ax=axes[0, 0], cbar_kws={'label': '% Increase'})
        axes[0, 0].set_title('ING Response Time Increase (%)', fontsize=12, fontweight='bold')
        axes[0, 0].set_xlabel('Blocking Duration (tb)')
        axes[0, 0].set_ylabel('Opening Ratio')
        
        # PREPA time increase
        sns.heatmap(pivot_prepa_time, annot=True, fmt='.0f', cmap='YlOrRd',
                   ax=axes[0, 1], cbar_kws={'label': '% Increase'})
        axes[0, 1].set_title('PREPA Response Time Increase (%)', fontsize=12, fontweight='bold')
        axes[0, 1].set_xlabel('Blocking Duration (tb)')
        axes[0, 1].set_ylabel('Opening Ratio')
        
        # Max queue length
        sns.heatmap(pivot_queue, annot=True, fmt='.1f', cmap='Blues',
                   ax=axes[1, 0], cbar_kws={'label': 'Jobs'})
        axes[1, 0].set_title('Maximum Queue Length', fontsize=12, fontweight='bold')
        axes[1, 0].set_xlabel('Blocking Duration (tb)')
        axes[1, 0].set_ylabel('Opening Ratio')
        
        # Throughput (ING completed)
        sns.heatmap(pivot_throughput, annot=True, fmt='.0f', cmap='Greens',
                   ax=axes[1, 1], cbar_kws={'label': 'Jobs'})
        axes[1, 1].set_title('ING Jobs Completed', fontsize=12, fontweight='bold')
        axes[1, 1].set_xlabel('Blocking Duration (tb)')
        axes[1, 1].set_ylabel('Opening Ratio')
        
        plt.tight_layout()
        plt.savefig(f"{output_dir}/gating_impact_heatmaps.png", dpi=300, bbox_inches='tight')
        plt.close()
        
        # 2. Line plots: Impact of tb for different ratios
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        
        for ratio in results_df['ratio'].unique():
            subset = results_df[results_df['ratio'] == ratio]
            
            axes[0, 0].plot(subset['tb'], subset['ing_avg_response_time'], 
                          marker='o', label=f'Ratio={ratio:.2f}')
            axes[0, 1].plot(subset['tb'], subset['prepa_avg_response_time'], 
                          marker='o', label=f'Ratio={ratio:.2f}')
            axes[1, 0].plot(subset['tb'], subset['max_queue_length'], 
                          marker='o', label=f'Ratio={ratio:.2f}')
            axes[1, 1].plot(subset['tb'], subset['ing_completed'] + subset['prepa_completed'], 
                          marker='o', label=f'Ratio={ratio:.2f}')
        
        axes[0, 0].set_title('ING Response Time vs Blocking Duration', fontweight='bold')
        axes[0, 0].set_xlabel('Blocking Duration (tb)')
        axes[0, 0].set_ylabel('Avg Response Time (s)')
        axes[0, 0].legend()
        axes[0, 0].grid(True, alpha=0.3)
        
        axes[0, 1].set_title('PREPA Response Time vs Blocking Duration', fontweight='bold')
        axes[0, 1].set_xlabel('Blocking Duration (tb)')
        axes[0, 1].set_ylabel('Avg Response Time (s)')
        axes[0, 1].legend()
        axes[0, 1].grid(True, alpha=0.3)
        
        axes[1, 0].set_title('Max Queue Length vs Blocking Duration', fontweight='bold')
        axes[1, 0].set_xlabel('Blocking Duration (tb)')
        axes[1, 0].set_ylabel('Max Queue Length (jobs)')
        axes[1, 0].legend()
        axes[1, 0].grid(True, alpha=0.3)
        
        axes[1, 1].set_title('Total Throughput vs Blocking Duration', fontweight='bold')
        axes[1, 1].set_xlabel('Blocking Duration (tb)')
        axes[1, 1].set_ylabel('Total Jobs Completed')
        axes[1, 1].legend()
        axes[1, 1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(f"{output_dir}/gating_impact_curves.png", dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"\n✓ Visualizations saved in {output_dir}/")
    
    def recommend_gating_config(self,
                               results_df: pd.DataFrame,
                               max_time_increase_pct: float = 50.0) -> Dict:
        """
        Recommend optimal gating configuration based on constraints
        
        Args:
            results_df: Results from analyze_gating_variations
            max_time_increase_pct: Maximum acceptable response time increase (%)
            
        Returns:
            Dictionary with recommendation
        """
        # Filter feasible solutions
        feasible = results_df[
            (results_df['ing_time_increase_pct'] <= max_time_increase_pct) &
            (results_df['prepa_time_increase_pct'] <= max_time_increase_pct)
        ]
        
        if len(feasible) == 0:
            return {
                'status': 'no_feasible_solution',
                'message': f'No configuration meets constraint (<{max_time_increase_pct}% increase)',
                'best_compromise': results_df.loc[
                    results_df['ing_time_increase_pct'].idxmin()
                ].to_dict()
            }
        
        # Find configuration minimizing average time increase
        feasible = feasible.copy()
        feasible['avg_time_increase'] = (
            feasible['ing_time_increase_pct'] + feasible['prepa_time_increase_pct']
        ) / 2
        
        best_idx = feasible['avg_time_increase'].idxmin()
        best_config = feasible.loc[best_idx]
        
        return {
            'status': 'optimal_found',
            'tb': int(best_config['tb']),
            'ratio': float(best_config['ratio']),
            'opening_duration': int(best_config['opening_duration']),
            'ing_time_increase_pct': float(best_config['ing_time_increase_pct']),
            'prepa_time_increase_pct': float(best_config['prepa_time_increase_pct']),
            'avg_time_increase_pct': float(best_config['avg_time_increase']),
            'max_queue_length': float(best_config['max_queue_length']),
            'message': f"Optimal: tb={int(best_config['tb'])}, ratio={best_config['ratio']:.2f}"
        }
    
    def create_analysis_report(self,
                              results_df: pd.DataFrame,
                              recommendation: Dict,
                              output_file: str = "gating_analysis/analysis_report.txt") -> None:
        """
        Create text report of gating analysis
        
        Args:
            results_df: Results DataFrame
            recommendation: Recommendation dictionary
            output_file: Output file path
        """
        Path(output_file).parent.mkdir(exist_ok=True)
        
        with open(output_file, 'w') as f:
            f.write("=" * 70 + "\n")
            f.write("  GATING ANALYSIS REPORT\n")
            f.write("=" * 70 + "\n\n")
            
            # Configuration
            f.write("Configuration:\n")
            f.write(f"  Population ING: λ={self.lambda_ing}, μ={self.mu_ing}\n")
            f.write(f"  Population PREPA: λ={self.lambda_prepa}, μ={self.mu_prepa}\n")
            f.write(f"  Servers: {self.num_servers}\n\n")
            
            # Reference (no gating)
            ref_ing = results_df['reference_ing_time'].iloc[0]
            ref_prepa = results_df['reference_prepa_time'].iloc[0]
            f.write("Reference (No Gating):\n")
            f.write(f"  ING response time: {ref_ing:.4f}s\n")
            f.write(f"  PREPA response time: {ref_prepa:.4f}s\n\n")
            
            # Summary statistics
            f.write("Impact Analysis:\n")
            f.write(f"  Configurations tested: {len(results_df)}\n")
            f.write(f"  Min ING time increase: {results_df['ing_time_increase_pct'].min():.2f}%\n")
            f.write(f"  Max ING time increase: {results_df['ing_time_increase_pct'].max():.2f}%\n")
            f.write(f"  Min PREPA time increase: {results_df['prepa_time_increase_pct'].min():.2f}%\n")
            f.write(f"  Max PREPA time increase: {results_df['prepa_time_increase_pct'].max():.2f}%\n")
            f.write(f"  Max queue observed: {results_df['max_queue_length'].max():.1f} jobs\n\n")
            
            # Recommendation
            f.write("=" * 70 + "\n")
            f.write("RECOMMENDATION\n")
            f.write("=" * 70 + "\n\n")
            
            if recommendation['status'] == 'optimal_found':
                f.write(f"✓ Optimal Configuration Found:\n")
                f.write(f"  Blocking duration (tb): {recommendation['tb']} units\n")
                f.write(f"  Opening ratio: {recommendation['ratio']:.2f}\n")
                f.write(f"  Opening duration: {recommendation['opening_duration']} units\n\n")
                f.write(f"Impact:\n")
                f.write(f"  ING time increase: +{recommendation['ing_time_increase_pct']:.2f}%\n")
                f.write(f"  PREPA time increase: +{recommendation['prepa_time_increase_pct']:.2f}%\n")
                f.write(f"  Average increase: +{recommendation['avg_time_increase_pct']:.2f}%\n")
                f.write(f"  Max queue length: {recommendation['max_queue_length']:.1f} jobs\n")
            else:
                f.write(f"✗ {recommendation['message']}\n")
                if 'best_compromise' in recommendation:
                    bc = recommendation['best_compromise']
                    f.write(f"\nBest compromise found:\n")
                    f.write(f"  tb={bc['tb']}, ratio={bc['ratio']:.2f}\n")
                    f.write(f"  ING increase: +{bc['ing_time_increase_pct']:.2f}%\n")
                    f.write(f"  PREPA increase: +{bc['prepa_time_increase_pct']:.2f}%\n")
            
            f.write("\n" + "=" * 70 + "\n")
            f.write("End of Report\n")
            f.write("=" * 70 + "\n")
        
        print(f"✓ Report saved to {output_file}")
