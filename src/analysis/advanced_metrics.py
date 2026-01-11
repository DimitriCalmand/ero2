"""
Module Advanced Metrics - Métriques Avancées et Vérifications Théoriques

Ce module implémente:
- Vérification de la loi de Little (L = λW)
- Comparaison avec la théorie M/M/c
- Métriques avancées de performance
"""

import numpy as np
import pandas as pd
from typing import Dict, Optional
from scipy.special import factorial
from .statistics import PerformanceAnalyzer


class AdvancedMetricsAnalyzer(PerformanceAnalyzer):
    """
    Analyseur de métriques avancées avec vérifications théoriques
    """
    
    def __init__(self, df: pd.DataFrame):
        """
        Args:
            df: DataFrame contenant les événements de simulation
        """
        super().__init__(df)
    
    def calculate_little_law_verification(self) -> Dict:
        """
        Vérifie la loi de Little: L = λW
        
        La loi de Little établit qu'à l'équilibre:
        L (nombre moyen dans le système) = λ (taux d'arrivée) × W (temps moyen dans le système)
        
        Returns:
            Dictionnaire avec les résultats de vérification
        """
        # Calcul de λ (throughput observé)
        lambda_observed = self.calculate_throughput()
        
        # Calcul de W (temps moyen de réponse)
        completed = self.df[self.df['event_type'] == 'end_service']
        if len(completed) == 0:
            return {
                'verified': False,
                'reason': 'No completed jobs'
            }
        
        W = completed['response_time'].mean()
        
        # Calcul de L (nombre moyen dans le système)
        # Approximation: longueur moyenne de file + serveurs occupés
        L_queue = self.df['queue_length'].mean()
        
        # Estimation du nombre moyen de jobs en service
        service_times = completed['service_time'].dropna()
        if len(service_times) > 0:
            avg_service = service_times.mean()
            L_service = lambda_observed * avg_service
        else:
            L_service = 0
        
        L_observed = L_queue + L_service
        
        # Calcul de λW selon Little
        lambda_W = lambda_observed * W
        
        # Calcul de l'erreur relative
        if L_observed > 0:
            error = abs(L_observed - lambda_W) / L_observed
        else:
            error = 0.0
        
        # La loi est vérifiée si l'erreur est < 10%
        verifies = error < 0.1
        
        return {
            'L_observed': L_observed,
            'lambda_observed': lambda_observed,
            'W_observed': W,
            'lambda_W': lambda_W,
            'absolute_error': abs(L_observed - lambda_W),
            'relative_error_percent': error * 100,
            'verifies_little_law': verifies,
            'interpretation': 'Little\'s Law verified' if verifies else 'Little\'s Law NOT verified (may indicate transient period)'
        }
    
    def calculate_theoretical_mmcc_metrics(self, 
                                          lambda_: float, 
                                          mu: float, 
                                          c: int) -> Dict:
        """
        Calcule les métriques théoriques pour un système M/M/c
        
        Args:
            lambda_: Taux d'arrivée
            mu: Taux de service
            c: Nombre de serveurs
            
        Returns:
            Dictionnaire avec les métriques théoriques
        """
        # Utilisation par serveur
        rho = lambda_ / (mu * c)
        
        # Vérification de stabilité
        if rho >= 1:
            return {
                'system_stable': False,
                'rho': rho,
                'message': 'System is unstable (ρ ≥ 1)'
            }
        
        # Calcul de P0 (probabilité que le système soit vide)
        # Formule d'Erlang C
        a = lambda_ / mu  # Traffic intensity
        
        # Somme pour P0
        sum_term = sum((a ** n) / factorial(n) for n in range(c))
        last_term = (a ** c) / (factorial(c) * (1 - rho))
        P0 = 1 / (sum_term + last_term)
        
        # Probabilité d'attente (formule d'Erlang C)
        C = ((a ** c) / factorial(c)) * P0 / (1 - rho)
        
        # Nombre moyen de jobs en attente
        Lq = C * rho / (1 - rho)
        
        # Temps moyen d'attente (formule de Little pour la file)
        Wq = Lq / lambda_
        
        # Nombre moyen de jobs dans le système
        L = Lq + a
        
        # Temps moyen dans le système
        W = L / lambda_
        
        # Temps de service moyen
        service_time = 1 / mu
        
        return {
            'system_stable': True,
            'rho': rho,
            'utilization': rho,
            'P0': P0,
            'erlang_C': C,
            'prob_wait': C,
            'L_queue_theory': Lq,
            'L_system_theory': L,
            'W_queue_theory': Wq,
            'W_system_theory': W,
            'service_time_theory': service_time,
            'traffic_intensity': a
        }
    
    def compare_simulation_to_theory(self, 
                                    lambda_: float, 
                                    mu: float, 
                                    c: int) -> Dict:
        """
        Compare les résultats de simulation avec la théorie M/M/c
        
        Args:
            lambda_: Taux d'arrivée théorique
            mu: Taux de service théorique
            c: Nombre de serveurs
            
        Returns:
            Dictionnaire avec comparaison détaillée
        """
        # Métriques théoriques
        theory = self.calculate_theoretical_mmcc_metrics(lambda_, mu, c)
        
        if not theory.get('system_stable', False):
            return {
                'comparison_valid': False,
                'reason': 'Theoretical system is unstable',
                'theory': theory
            }
        
        # Métriques simulées
        utilization_sim = self.calculate_utilization(c)
        waiting_stats = self.calculate_waiting_time_stats()
        response_stats = self.calculate_response_time_stats()
        
        # Calcul des écarts
        def percent_error(sim, theory):
            if theory == 0:
                return 0.0
            return abs(sim - theory) / theory * 100
        
        comparison = {
            'comparison_valid': True,
            'parameters': {
                'lambda': lambda_,
                'mu': mu,
                'c': c,
                'rho': theory['rho']
            },
            'utilization': {
                'simulated': utilization_sim,
                'theoretical': theory['utilization'],
                'error_percent': percent_error(utilization_sim, theory['utilization'])
            },
            'waiting_time': {
                'simulated': waiting_stats['mean'],
                'theoretical': theory['W_queue_theory'],
                'error_percent': percent_error(waiting_stats['mean'], theory['W_queue_theory'])
            },
            'response_time': {
                'simulated': response_stats['mean'],
                'theoretical': theory['W_system_theory'],
                'error_percent': percent_error(response_stats['mean'], theory['W_system_theory'])
            },
            'full_theory': theory
        }
        
        # Évaluation globale de la précision
        avg_error = (
            comparison['utilization']['error_percent'] +
            comparison['waiting_time']['error_percent'] +
            comparison['response_time']['error_percent']
        ) / 3
        
        comparison['average_error_percent'] = avg_error
        comparison['simulation_accuracy'] = 'Excellent' if avg_error < 5 else 'Good' if avg_error < 10 else 'Fair' if avg_error < 20 else 'Poor'
        
        return comparison
    
    def calculate_variance_to_mean_ratio(self) -> Dict:
        """
        Calcule le ratio variance/moyenne pour détecter les comportements non-Poisson
        
        Pour un processus de Poisson, variance = moyenne
        
        Returns:
            Dictionnaire avec les ratios
        """
        completed = self.df[self.df['event_type'] == 'end_service']
        
        results = {}
        
        # Analyse des temps d'attente
        waiting_times = completed['waiting_time'].dropna()
        if len(waiting_times) > 0:
            mean_wait = waiting_times.mean()
            var_wait = waiting_times.var()
            results['waiting_time'] = {
                'mean': mean_wait,
                'variance': var_wait,
                'ratio': var_wait / mean_wait if mean_wait > 0 else 0,
                'interpretation': 'Exponential-like' if abs(var_wait / mean_wait - 1) < 0.2 else 'Non-exponential'
            }
        
        # Analyse des temps de service
        service_times = completed['service_time'].dropna()
        if len(service_times) > 0:
            mean_service = service_times.mean()
            var_service = service_times.var()
            results['service_time'] = {
                'mean': mean_service,
                'variance': var_service,
                'ratio': var_service / mean_service if mean_service > 0 else 0,
                'interpretation': 'Exponential-like' if abs(var_service / mean_service - 1) < 0.2 else 'Non-exponential'
            }
        
        return results
    
    def calculate_autocorrelation(self, metric: str = 'waiting_time', max_lag: int = 20) -> Dict:
        """
        Calcule l'autocorrélation pour détecter les dépendances temporelles
        
        Args:
            metric: Métrique à analyser
            max_lag: Lag maximum pour l'autocorrélation
            
        Returns:
            Dictionnaire avec les résultats d'autocorrélation
        """
        completed = self.df[self.df['event_type'] == 'end_service']
        
        if metric not in completed.columns:
            return {'error': f'Metric {metric} not found'}
        
        data = completed[metric].dropna().values
        
        if len(data) < max_lag:
            return {'error': 'Not enough data points'}
        
        # Calcul de l'autocorrélation
        autocorr = np.correlate(data - data.mean(), data - data.mean(), mode='full')
        autocorr = autocorr[len(autocorr)//2:]
        autocorr = autocorr[:max_lag+1] / autocorr[0]
        
        # Détection de corrélation significative (seuil: 2/√n)
        threshold = 2 / np.sqrt(len(data))
        significant_lags = [lag for lag, corr in enumerate(autocorr[1:], 1) if abs(corr) > threshold]
        
        return {
            'autocorrelation': autocorr.tolist(),
            'significant_lags': significant_lags,
            'has_autocorrelation': len(significant_lags) > 0,
            'interpretation': 'Independent observations' if len(significant_lags) == 0 else f'Correlation detected at lags: {significant_lags}'
        }
    
    def generate_advanced_report(self, 
                                lambda_: float, 
                                mu: float, 
                                c: int,
                                output_file: Optional[str] = None) -> str:
        """
        Génère un rapport complet avec toutes les métriques avancées
        
        Args:
            lambda_: Taux d'arrivée
            mu: Taux de service
            c: Nombre de serveurs
            output_file: Fichier de sortie (optionnel)
            
        Returns:
            Rapport sous forme de chaîne
        """
        report = []
        report.append("=" * 80)
        report.append("RAPPORT D'ANALYSE AVANCÉE")
        report.append("=" * 80)
        report.append("")
        
        # Paramètres du système
        report.append("PARAMÈTRES DU SYSTÈME:")
        report.append(f"  λ (taux d'arrivée): {lambda_:.4f}")
        report.append(f"  μ (taux de service): {mu:.4f}")
        report.append(f"  c (serveurs): {c}")
        report.append(f"  ρ (charge): {lambda_/(mu*c):.4f}")
        report.append("")
        
        # Vérification de la loi de Little
        report.append("VÉRIFICATION DE LA LOI DE LITTLE (L = λW):")
        little = self.calculate_little_law_verification()
        for key, value in little.items():
            if isinstance(value, float):
                report.append(f"  {key}: {value:.6f}")
            else:
                report.append(f"  {key}: {value}")
        report.append("")
        
        # Comparaison avec la théorie
        report.append("COMPARAISON SIMULATION vs THÉORIE M/M/c:")
        comparison = self.compare_simulation_to_theory(lambda_, mu, c)
        if comparison.get('comparison_valid'):
            report.append(f"  Précision globale: {comparison['simulation_accuracy']}")
            report.append(f"  Erreur moyenne: {comparison['average_error_percent']:.2f}%")
            report.append("")
            report.append("  Utilisation:")
            report.append(f"    Simulée: {comparison['utilization']['simulated']:.4f}")
            report.append(f"    Théorique: {comparison['utilization']['theoretical']:.4f}")
            report.append(f"    Erreur: {comparison['utilization']['error_percent']:.2f}%")
            report.append("")
            report.append("  Temps d'attente:")
            report.append(f"    Simulé: {comparison['waiting_time']['simulated']:.4f}")
            report.append(f"    Théorique: {comparison['waiting_time']['theoretical']:.4f}")
            report.append(f"    Erreur: {comparison['waiting_time']['error_percent']:.2f}%")
            report.append("")
            report.append("  Temps de réponse:")
            report.append(f"    Simulé: {comparison['response_time']['simulated']:.4f}")
            report.append(f"    Théorique: {comparison['response_time']['theoretical']:.4f}")
            report.append(f"    Erreur: {comparison['response_time']['error_percent']:.2f}%")
        else:
            report.append(f"  Comparaison invalide: {comparison.get('reason')}")
        report.append("")
        
        # Analyse variance/moyenne
        report.append("ANALYSE VARIANCE/MOYENNE:")
        var_mean = self.calculate_variance_to_mean_ratio()
        for metric, data in var_mean.items():
            report.append(f"  {metric}:")
            report.append(f"    Ratio variance/moyenne: {data['ratio']:.4f}")
            report.append(f"    Interprétation: {data['interpretation']}")
        report.append("")
        
        # Autocorrélation
        report.append("ANALYSE D'AUTOCORRÉLATION (temps d'attente):")
        autocorr = self.calculate_autocorrelation('waiting_time', max_lag=10)
        if 'error' not in autocorr:
            report.append(f"  {autocorr['interpretation']}")
            if autocorr['has_autocorrelation']:
                report.append(f"  Lags significatifs: {autocorr['significant_lags']}")
        report.append("")
        
        report.append("=" * 80)
        
        report_text = "\n".join(report)
        
        if output_file:
            with open(output_file, 'w') as f:
                f.write(report_text)
        
        return report_text
