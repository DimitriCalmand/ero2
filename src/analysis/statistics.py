"""
Module Analysis - Analyse Statistique et Visualisation
Étudiant 5: Analyse Statistique & Benchmarking

Ce module implémente:
- Calcul des intervalles de confiance (t-test)
- Détection de la période de chauffe (Warm-up)
- Comparaison avec les métriques réelles
- Visualisation des résultats
"""

import pandas as pd
import numpy as np
from scipy import stats
from typing import Dict, List, Tuple, Optional
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime


class WarmupDetector:
    """
    Détection de la période de chauffe dans les simulations
    """
    
    @staticmethod
    def detect_warmup(data: pd.Series, 
                     window_size: int = 50,
                     threshold: float = 0.05) -> int:
        """
        Détecte la période de chauffe en analysant la stabilité de la moyenne mobile
        
        Args:
            data: Série temporelle à analyser
            window_size: Taille de la fenêtre pour la moyenne mobile
            threshold: Seuil de variation pour considérer la série stable
            
        Returns:
            Index de fin de la période de chauffe
        """
        if len(data) < window_size * 2:
            return 0
        
        # Calcul de la moyenne mobile
        rolling_mean = data.rolling(window=window_size).mean()
        
        # Calcul du coefficient de variation
        rolling_std = data.rolling(window=window_size).std()
        cv = rolling_std / rolling_mean
        
        # Trouve le premier point où le CV devient stable
        for i in range(window_size, len(cv)):
            if cv[i] < threshold:
                return max(0, i - window_size)
        
        return window_size
    
    @staticmethod
    def remove_warmup(df: pd.DataFrame, warmup_time: float) -> pd.DataFrame:
        """
        Supprime la période de chauffe d'un DataFrame
        
        Args:
            df: DataFrame avec une colonne 'time'
            warmup_time: Temps de chauffe à supprimer
            
        Returns:
            DataFrame filtré
        """
        return df[df['time'] >= warmup_time].copy()


class ConfidenceInterval:
    """
    Calcul des intervalles de confiance
    """
    
    @staticmethod
    def calculate_ci(data: np.ndarray,
                    confidence: float = 0.95) -> Tuple[float, float, float]:
        """
        Calcule l'intervalle de confiance pour une série de données
        
        Args:
            data: Données à analyser
            confidence: Niveau de confiance (0.95 = 95%)
            
        Returns:
            Tuple (moyenne, borne_inf, borne_sup)
        """
        if len(data) == 0:
            return 0.0, 0.0, 0.0
        
        mean = np.mean(data)
        std_error = stats.sem(data)
        
        # T-test pour petit échantillon
        if len(data) < 30:
            df = len(data) - 1
            t_value = stats.t.ppf((1 + confidence) / 2, df)
        else:
            # Z-test pour grand échantillon
            t_value = stats.norm.ppf((1 + confidence) / 2)
        
        margin = t_value * std_error
        
        return mean, mean - margin, mean + margin
    
    @staticmethod
    def calculate_multiple_runs_ci(results: List[Dict],
                                   metric: str,
                                   confidence: float = 0.95) -> Tuple[float, float, float]:
        """
        Calcule l'intervalle de confiance sur plusieurs exécutions
        
        Args:
            results: Liste des résultats de plusieurs runs
            metric: Nom de la métrique à analyser
            confidence: Niveau de confiance
            
        Returns:
            Tuple (moyenne, borne_inf, borne_sup)
        """
        values = [r[metric] for r in results if metric in r]
        return ConfidenceInterval.calculate_ci(np.array(values), confidence)


class PerformanceAnalyzer:
    """
    Analyse des performances du système
    """
    
    def __init__(self, df: pd.DataFrame):
        """
        Args:
            df: DataFrame contenant les événements de simulation
        """
        self.df = df
    
    def calculate_throughput(self, time_window: Optional[float] = None) -> float:
        """
        Calcule le débit (jobs/unité de temps)
        
        Args:
            time_window: Fenêtre de temps (utilise toute la simulation si None)
            
        Returns:
            Débit moyen
        """
        completed = self.df[self.df['event_type'] == 'end_service']
        
        if len(completed) == 0:
            return 0.0
        
        total_time = time_window if time_window else completed['time'].max()
        
        if total_time == 0:
            return 0.0
        
        return len(completed) / total_time
    
    def calculate_utilization(self, num_servers: int) -> float:
        """
        Calcule le taux d'utilisation des serveurs
        
        Args:
            num_servers: Nombre de serveurs
            
        Returns:
            Taux d'utilisation (0 à 1)
        """
        completed = self.df[self.df['event_type'] == 'end_service']
        
        if len(completed) == 0:
            return 0.0
        
        total_service_time = completed['service_time'].sum()
        simulation_time = self.df['time'].max()
        
        if simulation_time == 0:
            return 0.0
        
        return total_service_time / (num_servers * simulation_time)
    
    def calculate_waiting_time_stats(self) -> Dict[str, float]:
        """
        Calcule les statistiques sur les temps d'attente
        
        Returns:
            Dictionnaire avec moyenne, médiane, percentiles
        """
        completed = self.df[self.df['event_type'] == 'end_service']
        waiting_times = completed['waiting_time'].dropna()
        
        if len(waiting_times) == 0:
            return {
                'mean': 0.0,
                'median': 0.0,
                'p95': 0.0,
                'p99': 0.0,
                'std': 0.0
            }
        
        return {
            'mean': waiting_times.mean(),
            'median': waiting_times.median(),
            'p95': waiting_times.quantile(0.95),
            'p99': waiting_times.quantile(0.99),
            'std': waiting_times.std()
        }
    
    def calculate_response_time_stats(self) -> Dict[str, float]:
        """
        Calcule les statistiques sur les temps de réponse
        
        Returns:
            Dictionnaire avec moyenne, médiane, percentiles
        """
        completed = self.df[self.df['event_type'] == 'end_service']
        response_times = completed['response_time'].dropna()
        
        if len(response_times) == 0:
            return {
                'mean': 0.0,
                'median': 0.0,
                'p95': 0.0,
                'p99': 0.0,
                'std': 0.0
            }
        
        return {
            'mean': response_times.mean(),
            'median': response_times.median(),
            'p95': response_times.quantile(0.95),
            'p99': response_times.quantile(0.99),
            'std': response_times.std()
        }
    
    def calculate_rejection_rate(self) -> float:
        """
        Calcule le taux de rejet
        
        Returns:
            Taux de rejet (0 à 1)
        """
        arrivals = len(self.df[self.df['event_type'] == 'arrival'])
        rejections = len(self.df[self.df['event_type'] == 'rejection'])
        
        if arrivals == 0:
            return 0.0
        
        return rejections / arrivals
    
    def get_summary(self, num_servers: int) -> Dict:
        """
        Génère un résumé complet des performances
        
        Args:
            num_servers: Nombre de serveurs
            
        Returns:
            Dictionnaire avec toutes les métriques
        """
        return {
            'throughput': self.calculate_throughput(),
            'utilization': self.calculate_utilization(num_servers),
            'rejection_rate': self.calculate_rejection_rate(),
            'waiting_time': self.calculate_waiting_time_stats(),
            'response_time': self.calculate_response_time_stats()
        }


class Visualizer:
    """
    Visualisation des résultats de simulation
    """
    
    def __init__(self, df: pd.DataFrame):
        """
        Args:
            df: DataFrame contenant les événements
        """
        self.df = df
        sns.set_style("whitegrid")
    
    def plot_arrivals_over_time(self, save_path: Optional[str] = None):
        """
        Graphique des arrivées au cours du temps
        
        Args:
            save_path: Chemin pour sauvegarder la figure
        """
        arrivals = self.df[self.df['event_type'] == 'arrival']
        
        plt.figure(figsize=(12, 6))
        plt.plot(arrivals['time'], range(1, len(arrivals) + 1))
        plt.xlabel('Temps (unités)')
        plt.ylabel('Nombre cumulé d\'arrivées')
        plt.title('Arrivées au cours du temps')
        plt.grid(True, alpha=0.3)
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        else:
            plt.show()
        plt.close()
    
    def plot_queue_length_over_time(self, save_path: Optional[str] = None):
        """
        Graphique de la longueur de file au cours du temps
        
        Args:
            save_path: Chemin pour sauvegarder la figure
        """
        plt.figure(figsize=(12, 6))
        plt.plot(self.df['time'], self.df['queue_length'])
        plt.xlabel('Temps (unités)')
        plt.ylabel('Longueur de la file')
        plt.title('Évolution de la longueur de file')
        plt.grid(True, alpha=0.3)
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        else:
            plt.show()
        plt.close()
    
    def plot_waiting_time_distribution(self, save_path: Optional[str] = None):
        """
        Distribution des temps d'attente
        
        Args:
            save_path: Chemin pour sauvegarder la figure
        """
        completed = self.df[self.df['event_type'] == 'end_service']
        waiting_times = completed['waiting_time'].dropna()
        
        plt.figure(figsize=(12, 6))
        plt.hist(waiting_times, bins=50, edgecolor='black', alpha=0.7)
        plt.xlabel('Temps d\'attente (unités)')
        plt.ylabel('Fréquence')
        plt.title('Distribution des temps d\'attente')
        plt.axvline(waiting_times.mean(), color='red', linestyle='--', 
                   label=f'Moyenne: {waiting_times.mean():.2f}')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        else:
            plt.show()
        plt.close()
    
    def plot_response_time_by_type(self, save_path: Optional[str] = None):
        """
        Temps de réponse par type de job
        
        Args:
            save_path: Chemin pour sauvegarder la figure
        """
        completed = self.df[self.df['event_type'] == 'end_service']
        
        plt.figure(figsize=(12, 6))
        
        for job_type in completed['entity_type'].unique():
            data = completed[completed['entity_type'] == job_type]['response_time']
            plt.hist(data, bins=30, alpha=0.5, label=job_type, edgecolor='black')
        
        plt.xlabel('Temps de réponse (unités)')
        plt.ylabel('Fréquence')
        plt.title('Distribution des temps de réponse par type')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        else:
            plt.show()
        plt.close()
    
    def plot_comparison(self, 
                       results: Dict[str, Dict],
                       metric: str,
                       save_path: Optional[str] = None):
        """
        Compare une métrique entre différentes configurations
        
        Args:
            results: Dictionnaire {nom_config: {métriques}}
            metric: Métrique à comparer
            save_path: Chemin pour sauvegarder la figure
        """
        configs = list(results.keys())
        values = [results[config].get(metric, 0) for config in configs]
        
        plt.figure(figsize=(10, 6))
        plt.bar(configs, values, edgecolor='black', alpha=0.7)
        plt.xlabel('Configuration')
        plt.ylabel(metric)
        plt.title(f'Comparaison: {metric}')
        plt.xticks(rotation=45, ha='right')
        plt.grid(True, alpha=0.3, axis='y')
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        else:
            plt.show()
        plt.close()
    
    def generate_full_report(self, output_dir: str, num_servers: int):
        """
        Génère un rapport complet avec tous les graphiques
        
        Args:
            output_dir: Répertoire de sortie
            num_servers: Nombre de serveurs
        """
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        # Génération de tous les graphiques
        self.plot_arrivals_over_time(f"{output_dir}/arrivals.png")
        self.plot_queue_length_over_time(f"{output_dir}/queue_length.png")
        self.plot_waiting_time_distribution(f"{output_dir}/waiting_time.png")
        self.plot_response_time_by_type(f"{output_dir}/response_time_by_type.png")
        
        # Résumé textuel
        analyzer = PerformanceAnalyzer(self.df)
        summary = analyzer.get_summary(num_servers)
        
        with open(f"{output_dir}/summary.txt", 'w') as f:
            f.write("=== RAPPORT D'ANALYSE ===\n\n")
            f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"Débit: {summary['throughput']:.4f} jobs/unité\n")
            f.write(f"Utilisation: {summary['utilization']:.2%}\n")
            f.write(f"Taux de rejet: {summary['rejection_rate']:.2%}\n\n")
            f.write("Temps d'attente:\n")
            for key, val in summary['waiting_time'].items():
                f.write(f"  {key}: {val:.4f}\n")
            f.write("\nTemps de réponse:\n")
            for key, val in summary['response_time'].items():
                f.write(f"  {key}: {val:.4f}\n")


class RealDataComparator:
    """
    Compare les résultats de simulation avec les données réelles
    """
    
    @staticmethod
    def load_real_data(tags_file: str) -> pd.DataFrame:
        """
        Charge les données réelles depuis le fichier tags
        
        Args:
            tags_file: Chemin vers le fichier tags
            
        Returns:
            DataFrame avec les données réelles
        """
        df = pd.read_csv(tags_file)
        df['receivedAt'] = pd.to_datetime(df['receivedAt'])
        df = df.sort_values('receivedAt')
        df['interarrival_time'] = df['receivedAt'].diff().dt.total_seconds()
        return df
    
    @staticmethod
    def estimate_arrival_rate(real_df: pd.DataFrame) -> float:
        """
        Estime le taux d'arrivée λ à partir des données réelles
        
        Args:
            real_df: DataFrame avec les données réelles
            
        Returns:
            Taux d'arrivée estimé (arrivées par seconde)
        """
        interarrivals = real_df['interarrival_time'].dropna()
        mean_interarrival = interarrivals.mean()
        
        if mean_interarrival == 0:
            return 0.0
        
        return 1.0 / mean_interarrival
    
    @staticmethod
    def compare_distributions(real_df: pd.DataFrame,
                            simulated_df: pd.DataFrame,
                            metric: str) -> Dict:
        """
        Compare les distributions entre données réelles et simulées
        
        Args:
            real_df: Données réelles
            simulated_df: Données simulées
            metric: Métrique à comparer
            
        Returns:
            Statistiques de comparaison
        """
        # Test de Kolmogorov-Smirnov
        if metric in real_df.columns and metric in simulated_df.columns:
            real_data = real_df[metric].dropna()
            sim_data = simulated_df[metric].dropna()
            
            ks_stat, p_value = stats.ks_2samp(real_data, sim_data)
            
            return {
                'ks_statistic': ks_stat,
                'p_value': p_value,
                'distributions_similar': p_value > 0.05
            }
        
        return {}


class PopulationAnalyzer:
    """
    Advanced analysis for heterogeneous populations
    """
    
    def __init__(self, df: pd.DataFrame):
        """
        Args:
            df: DataFrame from simulation logger
        """
        self.df = df
    
    def calculate_fairness_index(self) -> Dict:
        """
        Calculate Jain's Fairness Index for populations
        
        Jain's Index: J = (sum(x_i))^2 / (n * sum(x_i^2))
        Where x_i is the response time for each population
        
        Returns:
            Dictionary with fairness metrics
        """
        completed = self.df[self.df['event_type'] == 'end_service'].copy()
        
        if len(completed) == 0 or 'entity_type' not in completed.columns:
            return {
                'fairness_index': 0.0,
                'status': 'no_data'
            }
        
        # Group by population type
        response_times = completed.groupby('entity_type')['response_time'].mean()
        
        if len(response_times) < 2:
            return {
                'fairness_index': 1.0,
                'status': 'single_population'
            }
        
        # Calculate Jain's Index
        n = len(response_times)
        sum_x = response_times.sum()
        sum_x2 = (response_times ** 2).sum()
        
        if sum_x2 == 0:
            jain_index = 1.0
        else:
            jain_index = (sum_x ** 2) / (n * sum_x2)
        
        # Calculate response time ratio
        times_sorted = response_times.sort_values()
        ratio = times_sorted.iloc[-1] / times_sorted.iloc[0] if times_sorted.iloc[0] > 0 else float('inf')
        
        return {
            'fairness_index': float(jain_index),
            'response_time_ratio': float(ratio),
            'min_response_time': float(times_sorted.iloc[0]),
            'max_response_time': float(times_sorted.iloc[-1]),
            'populations': list(response_times.index),
            'avg_response_times': response_times.to_dict(),
            'interpretation': self._interpret_fairness(jain_index),
            'status': 'ok'
        }
    
    def _interpret_fairness(self, jain_index: float) -> str:
        """Interpret Jain's Fairness Index"""
        if jain_index >= 0.95:
            return "Excellent fairness (≥0.95)"
        elif jain_index >= 0.85:
            return "Good fairness (0.85-0.95)"
        elif jain_index >= 0.70:
            return "Fair (0.70-0.85)"
        elif jain_index >= 0.50:
            return "Poor fairness (0.50-0.70)"
        else:
            return "Very unfair (<0.50)"
    
    def calculate_percentiles_by_type(self,
                                     percentiles: List[float] = [0.50, 0.95, 0.99]) -> Dict:
        """
        Calculate percentiles for each population type
        
        Args:
            percentiles: List of percentiles to calculate (e.g., [0.50, 0.95, 0.99])
            
        Returns:
            Dictionary with percentiles by population type
        """
        completed = self.df[self.df['event_type'] == 'end_service'].copy()
        
        if len(completed) == 0 or 'entity_type' not in completed.columns:
            return {}
        
        results = {}
        
        for pop_type, group in completed.groupby('entity_type'):
            response_times = group['response_time'].dropna()
            waiting_times = group['waiting_time'].dropna()
            
            pop_results = {
                'count': len(group),
                'response_time': {},
                'waiting_time': {}
            }
            
            # Calculate percentiles for response time
            if len(response_times) > 0:
                for p in percentiles:
                    percentile_name = f"p{int(p*100)}"
                    pop_results['response_time'][percentile_name] = float(
                        response_times.quantile(p)
                    )
                pop_results['response_time']['mean'] = float(response_times.mean())
                pop_results['response_time']['std'] = float(response_times.std())
                pop_results['response_time']['min'] = float(response_times.min())
                pop_results['response_time']['max'] = float(response_times.max())
            
            # Calculate percentiles for waiting time
            if len(waiting_times) > 0:
                for p in percentiles:
                    percentile_name = f"p{int(p*100)}"
                    pop_results['waiting_time'][percentile_name] = float(
                        waiting_times.quantile(p)
                    )
                pop_results['waiting_time']['mean'] = float(waiting_times.mean())
                pop_results['waiting_time']['std'] = float(waiting_times.std())
                pop_results['waiting_time']['min'] = float(waiting_times.min())
                pop_results['waiting_time']['max'] = float(waiting_times.max())
            
            results[pop_type] = pop_results
        
        return results
    
    def calculate_sla_compliance(self,
                                sla_thresholds: Dict[str, float]) -> Dict:
        """
        Calculate SLA compliance for each population
        
        Args:
            sla_thresholds: Dictionary mapping population type to SLA threshold (seconds)
                           Example: {"ING": 1.0, "PREPA": 2.0}
        
        Returns:
            Dictionary with compliance metrics
        """
        completed = self.df[self.df['event_type'] == 'end_service'].copy()
        
        if len(completed) == 0 or 'entity_type' not in completed.columns:
            return {}
        
        results = {}
        
        for pop_type, group in completed.groupby('entity_type'):
            if pop_type not in sla_thresholds:
                continue
            
            threshold = sla_thresholds[pop_type]
            response_times = group['response_time'].dropna()
            
            if len(response_times) == 0:
                continue
            
            # Calculate compliance
            within_sla = (response_times <= threshold).sum()
            total = len(response_times)
            compliance_rate = within_sla / total if total > 0 else 0.0
            
            # Calculate violations
            violations = response_times[response_times > threshold]
            
            results[pop_type] = {
                'threshold': threshold,
                'total_jobs': total,
                'within_sla': int(within_sla),
                'violations': int(len(violations)),
                'compliance_rate': float(compliance_rate),
                'compliance_percentage': float(compliance_rate * 100),
                'avg_violation_time': float(violations.mean()) if len(violations) > 0 else 0.0,
                'max_violation_time': float(violations.max()) if len(violations) > 0 else 0.0,
                'status': 'compliant' if compliance_rate >= 0.95 else 'non_compliant'
            }
        
        return results
    
    def analyze_temporal_patterns_by_type(self,
                                         time_window: float = 50.0) -> Dict:
        """
        Analyze temporal patterns for each population
        
        Args:
            time_window: Time window for aggregation
            
        Returns:
            Dictionary with temporal analysis
        """
        completed = self.df[self.df['event_type'] == 'end_service'].copy()
        
        if len(completed) == 0 or 'entity_type' not in completed.columns:
            return {}
        
        results = {}
        
        for pop_type, group in completed.groupby('entity_type'):
            # Create time bins
            group = group.copy()
            group['time_bin'] = (group['time'] // time_window).astype(int)
            
            # Aggregate by time bin
            temporal_stats = group.groupby('time_bin').agg({
                'response_time': ['mean', 'std', 'count'],
                'waiting_time': ['mean', 'std']
            }).reset_index()
            
            # Calculate coefficient of variation over time
            response_means = temporal_stats['response_time']['mean']
            cv = response_means.std() / response_means.mean() if response_means.mean() > 0 else 0
            
            results[pop_type] = {
                'time_window': time_window,
                'num_windows': len(temporal_stats),
                'coefficient_of_variation': float(cv),
                'min_response_time_period': float(response_means.min()),
                'max_response_time_period': float(response_means.max()),
                'avg_jobs_per_window': float(temporal_stats['response_time']['count'].mean()),
                'stability': 'stable' if cv < 0.2 else 'variable' if cv < 0.5 else 'unstable'
            }
        
        return results
    
    def generate_population_report(self,
                                  sla_thresholds: Optional[Dict[str, float]] = None,
                                  output_file: str = "population_analysis_report.txt") -> None:
        """
        Generate comprehensive report for population analysis
        
        Args:
            sla_thresholds: SLA thresholds for compliance analysis
            output_file: Output file path
        """
        with open(output_file, 'w') as f:
            f.write("=" * 70 + "\n")
            f.write("  POPULATION ANALYSIS REPORT\n")
            f.write("=" * 70 + "\n\n")
            
            # Fairness analysis
            fairness = self.calculate_fairness_index()
            f.write("FAIRNESS ANALYSIS\n")
            f.write("-" * 70 + "\n")
            
            if fairness['status'] == 'ok':
                f.write(f"Jain's Fairness Index: {fairness['fairness_index']:.4f}\n")
                f.write(f"Interpretation: {fairness['interpretation']}\n")
                f.write(f"Response Time Ratio: {fairness['response_time_ratio']:.2f}x\n")
                f.write(f"Min Response Time: {fairness['min_response_time']:.4f}s\n")
                f.write(f"Max Response Time: {fairness['max_response_time']:.4f}s\n\n")
                
                f.write("Average Response Times by Population:\n")
                for pop, time in fairness['avg_response_times'].items():
                    f.write(f"  {pop}: {time:.4f}s\n")
            else:
                f.write(f"Status: {fairness['status']}\n")
            
            f.write("\n")
            
            # Percentiles
            percentiles = self.calculate_percentiles_by_type()
            if percentiles:
                f.write("PERCENTILES BY POPULATION\n")
                f.write("-" * 70 + "\n")
                
                for pop_type, stats in percentiles.items():
                    f.write(f"\n{pop_type} (n={stats['count']}):\n")
                    f.write("  Response Time:\n")
                    for metric, value in stats['response_time'].items():
                        f.write(f"    {metric}: {value:.4f}s\n")
                    
                    if stats['waiting_time']:
                        f.write("  Waiting Time:\n")
                        for metric, value in stats['waiting_time'].items():
                            f.write(f"    {metric}: {value:.4f}s\n")
            
            f.write("\n")
            
            # SLA compliance
            if sla_thresholds:
                compliance = self.calculate_sla_compliance(sla_thresholds)
                if compliance:
                    f.write("SLA COMPLIANCE\n")
                    f.write("-" * 70 + "\n")
                    
                    for pop_type, comp in compliance.items():
                        f.write(f"\n{pop_type}:\n")
                        f.write(f"  SLA Threshold: {comp['threshold']}s\n")
                        f.write(f"  Total Jobs: {comp['total_jobs']}\n")
                        f.write(f"  Within SLA: {comp['within_sla']} ({comp['compliance_percentage']:.2f}%)\n")
                        f.write(f"  Violations: {comp['violations']}\n")
                        f.write(f"  Status: {comp['status'].upper()}\n")
                        
                        if comp['violations'] > 0:
                            f.write(f"  Avg Violation Time: {comp['avg_violation_time']:.4f}s\n")
                            f.write(f"  Max Violation Time: {comp['max_violation_time']:.4f}s\n")
            
            f.write("\n")
            
            # Temporal patterns
            temporal = self.analyze_temporal_patterns_by_type()
            if temporal:
                f.write("TEMPORAL PATTERNS\n")
                f.write("-" * 70 + "\n")
                
                for pop_type, pattern in temporal.items():
                    f.write(f"\n{pop_type}:\n")
                    f.write(f"  Stability: {pattern['stability']}\n")
                    f.write(f"  Coefficient of Variation: {pattern['coefficient_of_variation']:.4f}\n")
                    f.write(f"  Response Time Range: {pattern['min_response_time_period']:.4f}s - {pattern['max_response_time_period']:.4f}s\n")
                    f.write(f"  Avg Jobs per Window: {pattern['avg_jobs_per_window']:.1f}\n")
            
            f.write("\n" + "=" * 70 + "\n")
            f.write("End of Report\n")
            f.write("=" * 70 + "\n")
        
        print(f"✓ Population analysis report saved to {output_file}")
