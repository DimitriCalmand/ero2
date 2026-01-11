#!/usr/bin/env python3
"""
Script pour lancer une simulation de scénario Waterfall en utilisant les données réelles
d'arrivée (Fichier 'tags').
"""

import argparse
import random
import pandas as pd
from typing import List

from src.core import SimulationEngine, Job
from src.capacity.limited_queue import WaterfallScenario
from src.analysis.statistics import RealDataComparator
from src.analysis.time_series import TimeSeriesAnalyzer

def real_arrivals_generator(env, interarrival_times: List[float], execution_queue):
    """
    Générateur d'arrivées basé sur une liste de temps inter-arrivées réels.
    """
    for i, interarrival_time in enumerate(interarrival_times):
        # Attend le temps inter-arrivée
        yield env.timeout(interarrival_time)
        
        # Crée un nouveau job
        job = Job(
            arrival_time=env.now,
            job_type="ING-REAL",
            assignment=f"real_submission_{i}"
        )
        # Lance le processus de traitement pour ce job
        env.process(execution_queue.process_job(job))

def run_real_data_waterfall(
    interarrival_times: List[float], 
    mu_exec: float, 
    mu_feed: float, 
    c: int, 
    ks: int, 
    kf: int, 
    finite: bool,
    seed: int = 42):
    """
    Lance une simulation du scénario Waterfall avec les arrivées réelles.

    Args:
        interarrival_times: Liste des temps inter-arrivées.
        mu_exec (float): Taux de service pour l'exécution (μ_exec).
        mu_feed (float): Taux de service pour le feedback (μ_feed).
        c (int): Nombre de serveurs pour l'exécution.
        ks (int): Taille de la file d'attente d'exécution.
        kf (int): Taille de la file d'attente de feedback.
        finite (bool): Si les files sont finies ou non.
        seed (int, optional): Graine aléatoire. Defaults to 42.
    """
    print(f"--- Simulation Waterfall avec Données Réelles ---")
    queue_type = "Finies" if finite else "Infinies"
    print(f"Type de files: {queue_type}")
    print(f"Paramètres: μ_exec={mu_exec}, μ_feed={mu_feed}, c={c}, ks={ks}, kf={kf}\n")

    random.seed(seed)
    
    # La durée de la simulation est la somme de tous les temps inter-arrivées
    duration = sum(interarrival_times)

    engine = SimulationEngine(random_seed=seed)
    
    scenario = WaterfallScenario(
        env=engine.env,
        logger=engine.logger,
        num_servers=c,
        execution_queue_size=ks,
        execution_rate=mu_exec,
        feedback_queue_size=kf,
        feedback_rate=mu_feed,
        arrival_rate=0,  # Non utilisé car on a notre propre générateur
        duration=duration,
        finite=finite,
    )

    # Lance le générateur d'arrivées réelles
    engine.env.process(real_arrivals_generator(engine.env, interarrival_times, scenario.execution_queue))
    
    # Lance la simulation
    engine.run(duration)

    # Récupération et affichage des statistiques
    sojourn_stats = scenario.get_sojourn_stats()
    exec_stats = scenario.execution_queue.get_stats()
    feed_stats = scenario.feedback_queue.get_stats()

    print("Résultats Globaux:")
    print(f"  Jobs complétés (total): {sojourn_stats['completed_jobs']}")
    print(f"  Temps de séjour moyen: {sojourn_stats['mean_sojourn_time']:.4f}")
    print(f"  Variance du temps de séjour: {sojourn_stats['sojourn_variance']:.4f}\n")

    print("Statistiques - Execution Queue:")
    print(f"  Jobs arrivés: {exec_stats['total_arrivals']}")
    print(f"  Jobs complétés: {exec_stats['jobs_completed']}")
    print(f"  Jobs rejetés: {exec_stats['total_rejections']}")
    print(f"  Taux de rejet: {exec_stats['rejection_rate']:.2%}\n")

    print("Statistiques - Feedback Queue:")
    print(f"  Jobs arrivés: {feed_stats['total_arrivals']}")
    print(f"  Jobs complétés: {feed_stats['jobs_completed']}")
    print(f"  Jobs rejetés: {feed_stats['total_rejections']}")
    print(f"  Taux de rejet: {feed_stats['rejection_rate']:.2%}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Lancer une simulation Waterfall avec les données d'arrivée réelles.")
    parser.add_argument("--tags-file", type=str, default="tags", help="Chemin vers le fichier de données 'tags'.")
    parser.add_argument("--mu-exec", type=float, required=True, help="Taux de service pour l'exécution (μ_exec).")
    parser.add_argument("--mu-feed", type=float, required=True, help="Taux de service pour le feedback (μ_feed).")
    parser.add_argument("--c", type=int, required=True, help="Nombre de serveurs pour l'exécution.")
    parser.add_argument("--ks", type=int, default=10, help="Taille de la file d'attente d'exécution.")
    parser.add_argument("--kf", type=int, default=10, help="Taille de la file d'attente de feedback.")
    parser.add_argument("--finite", action='store_true', help="Utiliser des files finies. Si non spécifié, les files sont infinies.")
    
    args = parser.parse_args()

    # Charger les données réelles
    print("Chargement et analyse des données d'arrivée réelles...")
    real_df = RealDataComparator.load_real_data(args.tags_file)
    ts_analyzer = TimeSeriesAnalyzer(real_df)
    interarrival_times = ts_analyzer.extract_interarrival_times()
    # On met à l'échelle les temps pour la simulation (par défaut, ils sont en secondes)
    # Ici on ne change pas l'échelle
    
    print(f"  {len(interarrival_times)} arrivées trouvées.")
    print(f"  Durée totale couverte par les données: {sum(interarrival_times):.2f} secondes.\n")

    run_real_data_waterfall(
        interarrival_times=interarrival_times,
        mu_exec=args.mu_exec,
        mu_feed=args.mu_feed,
        c=args.c,
        ks=args.ks,
        kf=args.kf,
        finite=args.finite,
    )
