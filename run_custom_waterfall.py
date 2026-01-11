#!/usr/bin/env python3
"""
Script pour lancer une simulation de scénario Waterfall avec des paramètres personnalisés.
"""

import argparse
import random
from src.core import SimulationEngine
from src.capacity import WaterfallScenario

def run_custom_waterfall(lambda_rate, mu_exec, mu_feed, c, duration=1000.0, seed=42):
    """
    Lance une simulation du scénario Waterfall avec des paramètres spécifiques.

    Args:
        lambda_rate (float): Taux d'arrivée (λ).
        mu_exec (float): Taux de service pour l'exécution (μ_exec).
        mu_feed (float): Taux de service pour le feedback (μ_feed).
        c (int): Nombre de serveurs.
        duration (float, optional): Durée de la simulation. Defaults to 1000.0.
        seed (int, optional): Graine aléatoire. Defaults to 42.
    """
    print(f"--- Simulation Waterfall Personnalisée ---")
    print(f"Paramètres: λ={lambda_rate}, μ_exec={mu_exec}, μ_feed={mu_feed}, c={c}\n")

    # Utiliser des files "infinies" pour ce scénario
    # Les tailles de file ks et kf sont ignorées lorsque finite=False
    ks = -1 
    kf = -1

    engine = SimulationEngine(random_seed=seed)
    
    scenario = WaterfallScenario(
        env=engine.env,
        logger=engine.logger,
        num_servers=c,
        execution_queue_size=ks,
        execution_rate=mu_exec,
        feedback_queue_size=kf,
        feedback_rate=mu_feed,
        arrival_rate=lambda_rate,
        duration=duration,
        finite=False,  # Important pour simuler un système avec files potentiellement illimitées
    )

    engine.env.process(scenario.arrivals())
    engine.run(duration)

    # Récupération et affichage des statistiques
    sojourn_stats = scenario.get_sojourn_stats()
    exec_stats = scenario.execution_queue.get_stats()
    feed_stats = scenario.feedback_queue.get_stats()

    print("Résultats:")
    print(f"  Jobs exécutés: {exec_stats['jobs_completed']}")
    print(f"  Jobs finalisés (feedback): {feed_stats['jobs_completed']}")
    print(f"  Temps de séjour moyen (global): {sojourn_stats['mean_sojourn_time']:.4f}")
    print(f"  Variance du temps de séjour: {sojourn_stats['sojourn_variance']:.4f}")
    print(f"  Taux de rejet (Exec): {exec_stats['rejection_rate']:.2%}")
    print(f"  Taux de rejet (Feed): {feed_stats['rejection_rate']:.2%}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Lancer une simulation Waterfall personnalisée.")
    parser.add_argument("--lambda", type=float, required=True, dest='lambda_rate', help="Taux d'arrivée (λ)")
    parser.add_argument("--mu-exec", type=float, required=True, help="Taux de service pour l'exécution (μ_exec)")
    parser.add_argument("--mu-feed", type=float, required=True, help="Taux de service pour le feedback (μ_feed)")
    parser.add_argument("--c", type=int, required=True, help="Nombre de serveurs")
    
    args = parser.parse_args()

    run_custom_waterfall(
        lambda_rate=args.lambda_rate,
        mu_exec=args.mu_exec,
        mu_feed=args.mu_feed,
        c=args.c
    )
