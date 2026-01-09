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
