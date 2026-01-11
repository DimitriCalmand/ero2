"""
Module Optimizer - Optimisation Automatique des Paramètres

Ce module implémente:
- Recherche en grille pour optimiser ks, kf
- Optimisation multi-objectif
- Analyse de sensibilité des paramètres
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Callable
import simpy
from ..core import SimulationEngine
from ..capacity import WaterfallScenario


class ParameterOptimizer:
    """
    Optimiseur de paramètres pour systèmes de files d'attente
    """
    
    def __init__(self, random_seed: int = 42):
        """
        Args:
            random_seed: Graine pour reproductibilité
        """
        self.random_seed = random_seed
        self.results = []
    
    def optimize_waterfall_capacity(self,
                                    arrival_rate: float,
                                    execution_rate: float,
                                    feedback_rate: float,
                                    num_servers: int,
                                    duration: float = 5000.0,
                                    target_rejection_rate: float = 0.05,
                                    ks_range: Tuple[int, int] = (2, 20),
                                    kf_range: Tuple[int, int] = (2, 15),
                                    cost_weights: Optional[Dict[str, float]] = None) -> Dict:
        """
        Optimise les capacités ks et kf pour un système Waterfall
        
        Args:
            arrival_rate: Taux d'arrivée λ
            execution_rate: Taux de traitement exécution μ_exec
            feedback_rate: Taux de traitement feedback μ_feed
            num_servers: Nombre de serveurs d'exécution
            duration: Durée de simulation
            target_rejection_rate: Taux de rejet cible (défaut: 5%)
            ks_range: Plage pour ks (min, max)
            kf_range: Plage pour kf (min, max)
            cost_weights: Poids pour la fonction de coût
            
        Returns:
            Dictionnaire avec configuration optimale et historique
        """
        if cost_weights is None:
            cost_weights = {
                'capacity': 1.0,      # Coût de la capacité
                'rejection': 10.0,    # Pénalité pour rejets
                'throughput': -2.0    # Bonus pour débit (négatif = récompense)
            }
        
        print(f"Optimisation en cours...")
        print(f"  Plage ks: {ks_range[0]}-{ks_range[1]}")
        print(f"  Plage kf: {kf_range[0]}-{kf_range[1]}")
        print(f"  Taux rejet cible: {target_rejection_rate:.1%}")
        print()
        
        results = []
        feasible_solutions = []
        
        # Recherche en grille
        for ks in range(ks_range[0], ks_range[1] + 1):
            for kf in range(kf_range[0], kf_range[1] + 1):
                # Simulation
                engine = SimulationEngine(random_seed=self.random_seed)
                
                scenario = WaterfallScenario(
                    env=engine.env,
                    logger=engine.logger,
                    num_servers=num_servers,
                    execution_queue_size=ks,
                    feedback_queue_size=kf,
                    execution_rate=execution_rate,
                    feedback_rate=feedback_rate,
                    arrival_rate=arrival_rate,
                    duration=duration
                )
                
                engine.env.process(scenario.arrivals())
                engine.run(duration)
                
                # Récupération des statistiques
                exec_stats = scenario.execution_queue.get_stats()
                feed_stats = scenario.feedback_queue.get_stats()
                sojourn_stats = scenario.get_sojourn_stats()
                
                # Taux de rejet global (cascade)
                total_arrivals = exec_stats['total_arrivals']
                total_completed = sojourn_stats['completed_jobs']
                total_rejected = total_arrivals - total_completed
                overall_rejection_rate = total_rejected / total_arrivals if total_arrivals > 0 else 0
                
                # Calcul du coût
                total_capacity = ks + kf
                cost = (cost_weights['capacity'] * total_capacity +
                       cost_weights['rejection'] * overall_rejection_rate * 100 +
                       cost_weights['throughput'] * (total_completed / duration))
                
                result = {
                    'ks': ks,
                    'kf': kf,
                    'total_capacity': total_capacity,
                    'overall_rejection_rate': overall_rejection_rate,
                    'exec_rejection_rate': exec_stats['rejection_rate'],
                    'feed_rejection_rate': feed_stats['rejection_rate'],
                    'completed_jobs': total_completed,
                    'throughput': total_completed / duration,
                    'mean_sojourn_time': sojourn_stats['mean_sojourn_time'],
                    'cost': cost
                }
                
                results.append(result)
                
                # Solutions réalisables (respectent la contrainte de rejet)
                if overall_rejection_rate <= target_rejection_rate:
                    feasible_solutions.append(result)
        
        self.results = results
        
        # Conversion en DataFrame pour analyse
        df_results = pd.DataFrame(results)
        
        # Meilleure solution
        if feasible_solutions:
            # Parmi les solutions réalisables, prendre celle avec le coût minimal
            optimal = min(feasible_solutions, key=lambda x: x['cost'])
            status = 'optimal_found'
        else:
            # Aucune solution réalisable, prendre celle avec le rejet minimal
            optimal = min(results, key=lambda x: x['overall_rejection_rate'])
            status = 'no_feasible_solution'
        
        # Analyse de sensibilité
        sensitivity = self._analyze_sensitivity(df_results)
        
        return {
            'status': status,
            'optimal_configuration': optimal,
            'all_results': results,
            'feasible_count': len(feasible_solutions),
            'total_evaluated': len(results),
            'sensitivity_analysis': sensitivity,
            'summary': {
                'optimal_ks': optimal['ks'],
                'optimal_kf': optimal['kf'],
                'total_capacity': optimal['total_capacity'],
                'rejection_rate': optimal['overall_rejection_rate'],
                'throughput': optimal['throughput'],
                'mean_sojourn_time': optimal['mean_sojourn_time']
            }
        }
    
    def _analyze_sensitivity(self, df: pd.DataFrame) -> Dict:
        """
        Analyse la sensibilité des métriques aux paramètres
        
        Args:
            df: DataFrame avec les résultats
            
        Returns:
            Dictionnaire avec l'analyse de sensibilité
        """
        # Corrélation entre paramètres et métriques
        correlations = {}
        
        for metric in ['overall_rejection_rate', 'throughput', 'mean_sojourn_time']:
            if metric in df.columns:
                corr_ks = df['ks'].corr(df[metric])
                corr_kf = df['kf'].corr(df[metric])
                
                correlations[metric] = {
                    'ks_correlation': corr_ks,
                    'kf_correlation': corr_kf,
                    'most_influential': 'ks' if abs(corr_ks) > abs(corr_kf) else 'kf'
                }
        
        return correlations
    
    def plot_optimization_results(self, 
                                  output_dir: str = 'optimization_results'):
        """
        Génère des graphiques d'analyse d'optimisation
        
        Args:
            output_dir: Répertoire de sortie
        """
        import matplotlib.pyplot as plt
        import seaborn as sns
        import os
        
        os.makedirs(output_dir, exist_ok=True)
        
        df = pd.DataFrame(self.results)
        
        # 1. Heatmap du taux de rejet
        plt.figure(figsize=(12, 8))
        pivot_rejection = df.pivot(index='kf', columns='ks', values='overall_rejection_rate')
        sns.heatmap(pivot_rejection, annot=True, fmt='.2%', cmap='RdYlGn_r', 
                   cbar_kws={'label': 'Taux de rejet'})
        plt.title('Taux de rejet en fonction de ks et kf')
        plt.xlabel('ks (capacité exécution)')
        plt.ylabel('kf (capacité feedback)')
        plt.savefig(f'{output_dir}/rejection_rate_heatmap.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # 2. Heatmap du débit
        plt.figure(figsize=(12, 8))
        pivot_throughput = df.pivot(index='kf', columns='ks', values='throughput')
        sns.heatmap(pivot_throughput, annot=True, fmt='.4f', cmap='YlGnBu', 
                   cbar_kws={'label': 'Débit (jobs/unité)'})
        plt.title('Débit en fonction de ks et kf')
        plt.xlabel('ks (capacité exécution)')
        plt.ylabel('kf (capacité feedback)')
        plt.savefig(f'{output_dir}/throughput_heatmap.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # 3. Heatmap du coût
        plt.figure(figsize=(12, 8))
        pivot_cost = df.pivot(index='kf', columns='ks', values='cost')
        sns.heatmap(pivot_cost, annot=True, fmt='.1f', cmap='coolwarm', 
                   cbar_kws={'label': 'Coût'})
        plt.title('Coût total en fonction de ks et kf')
        plt.xlabel('ks (capacité exécution)')
        plt.ylabel('kf (capacité feedback)')
        plt.savefig(f'{output_dir}/cost_heatmap.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # 4. Pareto front (capacité vs rejet)
        plt.figure(figsize=(10, 6))
        plt.scatter(df['total_capacity'], df['overall_rejection_rate'] * 100, 
                   c=df['cost'], cmap='viridis', s=100, alpha=0.6)
        plt.colorbar(label='Coût')
        plt.xlabel('Capacité totale (ks + kf)')
        plt.ylabel('Taux de rejet (%)')
        plt.title('Front de Pareto: Capacité vs Taux de rejet')
        plt.grid(True, alpha=0.3)
        plt.savefig(f'{output_dir}/pareto_front.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"Graphiques sauvegardés dans {output_dir}/")
    
    def find_pareto_optimal(self, 
                           objectives: List[str] = ['total_capacity', 'overall_rejection_rate'],
                           minimize: List[bool] = [True, True]) -> List[Dict]:
        """
        Trouve les solutions Pareto-optimales
        
        Args:
            objectives: Liste des objectifs à optimiser
            minimize: Pour chaque objectif, True si minimisation, False si maximisation
            
        Returns:
            Liste des solutions Pareto-optimales
        """
        if not self.results:
            return []
        
        pareto_front = []
        
        for i, solution_i in enumerate(self.results):
            is_dominated = False
            
            for j, solution_j in enumerate(self.results):
                if i == j:
                    continue
                
                # Vérifier si solution_i est dominée par solution_j
                dominates = True
                strictly_better = False
                
                for obj, minimize_obj in zip(objectives, minimize):
                    val_i = solution_i[obj]
                    val_j = solution_j[obj]
                    
                    if minimize_obj:
                        if val_i < val_j:
                            dominates = False
                            break
                        if val_i > val_j:
                            strictly_better = True
                    else:  # Maximisation
                        if val_i > val_j:
                            dominates = False
                            break
                        if val_i < val_j:
                            strictly_better = True
                
                if dominates and strictly_better:
                    is_dominated = True
                    break
            
            if not is_dominated:
                pareto_front.append(solution_i)
        
        return pareto_front
