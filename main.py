#!/usr/bin/env python3
"""
Script Principal - Simulateur de Moulinette
Projet ERO2 - EPITA

Ce script permet de lancer différents scénarios de simulation
et d'analyser les résultats.
"""

import random
import argparse
from pathlib import Path

# Import des modules
from src.core import SimulationEngine
from src.capacity import WaterfallScenario, LimitedQueue
from src.reliability import (
    SystematicBackup, RandomBackup, ReliableServer, BackupComparison
)
from src.regulation import ChannelsScenario
from src.analysis import (
    WarmupDetector, PerformanceAnalyzer, Visualizer, RealDataComparator
)


def scenario_basic(duration: float = 1000.0, seed: int = 42):
    """
    Scénario basique: file M/M/c simple
    
    Args:
        duration: Durée de la simulation
        seed: Graine aléatoire
    """
    print("=== SCÉNARIO BASIQUE: M/M/c ===\n")
    
    # Paramètres
    arrival_rate = 2.0  # λ = 2 jobs/unité
    service_rate = 3.0  # μ = 3 jobs/unité  
    num_servers = 1
    
    print(f"Paramètres:")
    print(f"  λ (arrivées): {arrival_rate}")
    print(f"  μ (service): {service_rate}")
    print(f"  c (serveurs): {num_servers}")
    print(f"  ρ (utilisation théorique): {arrival_rate/(service_rate*num_servers):.2f}\n")
    
    # Initialisation
    engine = SimulationEngine(random_seed=seed)
    
    from src.core import Server, JobGenerator
    server = Server(
        env=engine.env,
        server_id="basic_server",
        num_servers=num_servers,
        logger=engine.logger
    )
    
    generator = JobGenerator(
        env=engine.env,
        logger=engine.logger,
        arrival_rate=arrival_rate,
        job_type="ING"
    )
    
    # Lancement
    def service_time_gen():
        return random.expovariate(service_rate)
    
    engine.env.process(generator.generate(server, service_time_gen, duration))
    engine.run(duration)
    
    # Analyse
    df = engine.get_results()
    analyzer = PerformanceAnalyzer(df)
    summary = analyzer.get_summary(num_servers)
    
    print("Résultats:")
    print(f"  Débit: {summary['throughput']:.4f} jobs/unité")
    print(f"  Utilisation: {summary['utilization']:.2%}")
    print(f"  Temps d'attente moyen: {summary['waiting_time']['mean']:.4f}")
    print(f"  Temps de réponse moyen: {summary['response_time']['mean']:.4f}")
    print(f"  Taux de rejet: {summary['rejection_rate']:.2%}\n")
    
    return df, summary


def scenario_waterfall(duration: float = 1000.0, seed: int = 42):
    """
    Scénario Waterfall: comparaison files finies vs loss system
    
    Args:
        duration: Durée de la simulation
        seed: Graine aléatoire
    """
    print("=== SCÉNARIO WATERFALL: Files Finies ===\n")
    
    # Paramètres
    arrival_rate = 3.0
    service_rate = 2.5
    num_servers = 2
    max_queue_size = 5
    
    print(f"Paramètres:")
    print(f"  λ: {arrival_rate}")
    print(f"  μ: {service_rate}")
    print(f"  c (serveurs): {num_servers}")
    print(f"  k_f (file max): {max_queue_size}\n")
    
    # Initialisation
    engine = SimulationEngine(random_seed=seed)
    scenario = WaterfallScenario(
        env=engine.env,
        logger=engine.logger,
        num_servers=num_servers,
        max_queue_size=max_queue_size
    )
    
    # Exécution
    results = scenario.run_comparison(arrival_rate, service_rate, duration)
    
    print("Résultats File Limitée:")
    print(f"  Arrivées: {results['limited_queue']['total_arrivals']}")
    print(f"  Complétés: {results['limited_queue']['jobs_completed']}")
    print(f"  Rejets: {results['limited_queue']['total_rejections']}")
    print(f"  Taux de rejet: {results['limited_queue']['rejection_rate']:.2%}\n")
    
    print("Résultats Loss System:")
    print(f"  Arrivées: {results['loss_system']['total_arrivals']}")
    print(f"  Complétés: {results['loss_system']['jobs_completed']}")
    print(f"  Rejets: {results['loss_system']['total_rejections']}")
    print(f"  Prob. blocage: {results['loss_system']['blocking_probability']:.2%}\n")
    
    print("Comparaison:")
    print(f"  Avantage file: +{results['comparison']['queue_advantage']} jobs\n")
    
    return engine.get_results(), results


def scenario_backup(duration: float = 1000.0, seed: int = 42):
    """
    Scénario Backup: comparaison des stratégies de sauvegarde
    
    Args:
        duration: Durée de la simulation
        seed: Graine aléatoire
    """
    print("=== SCÉNARIO BACKUP: Stratégies de Sauvegarde ===\n")
    
    # Paramètres
    arrival_rate = 2.0
    service_rate = 3.0
    backup_rate = 10.0  # Backup rapide
    num_servers = 2
    
    print(f"Paramètres:")
    print(f"  λ: {arrival_rate}")
    print(f"  μ (service): {service_rate}")
    print(f"  μ_b (backup): {backup_rate}")
    print(f"  c: {num_servers}\n")
    
    # Initialisation
    engine = SimulationEngine(random_seed=seed)
    comparison = BackupComparison(env=engine.env, logger=engine.logger)
    
    def backup_time_gen():
        return random.expovariate(backup_rate)
    
    # Ajout des stratégies
    comparison.add_server(
        "systematic",
        num_servers,
        SystematicBackup(),
        backup_time_gen
    )
    
    comparison.add_server(
        "random_50%",
        num_servers,
        RandomBackup(0.5),
        backup_time_gen
    )
    
    comparison.add_server(
        "random_20%",
        num_servers,
        RandomBackup(0.2),
        backup_time_gen
    )
    
    # Exécution
    results = comparison.run_comparison(arrival_rate, service_rate, duration)
    
    for strategy, stats in results.items():
        print(f"Stratégie: {strategy}")
        print(f"  Jobs traités: {stats['jobs_processed']}")
        print(f"  Jobs sauvegardés: {stats['jobs_backed_up']}")
        print(f"  Taux backup: {stats['backup_rate']:.2%}")
        print(f"  Temps backup moyen: {stats['avg_backup_time']:.4f}\n")
    
    return engine.get_results(), results


def scenario_channels(duration: float = 1000.0, seed: int = 42):
    """
    Scénario Channels: populations hétérogènes ING/PREPA
    
    Args:
        duration: Durée de la simulation
        seed: Graine aléatoire
    """
    print("=== SCÉNARIO CHANNELS: Populations Hétérogènes ===\n")
    
    # Paramètres
    lambda_ing = 1.5
    lambda_prepa = 0.5
    mu_ing = 2.5
    mu_prepa = 2.0
    num_servers = 2
    
    print(f"Paramètres:")
    print(f"  Population ING: λ={lambda_ing}, μ={mu_ing}")
    print(f"  Population PREPA: λ={lambda_prepa}, μ={mu_prepa}")
    print(f"  Serveurs: {num_servers}\n")
    
    # Test avec différentes politiques
    policies = ["FIFO", "SJF", "PRIORITY"]
    results = {}
    
    for policy in policies:
        print(f"--- Politique: {policy} ---")
        
        engine = SimulationEngine(random_seed=seed)
        scenario = ChannelsScenario(
            env=engine.env,
            logger=engine.logger,
            num_servers=num_servers,
            scheduling_policy=policy
        )
        
        scenario.add_population("ING", lambda_ing, mu_ing)
        scenario.add_population("PREPA", lambda_prepa, mu_prepa)
        
        stats = scenario.run(duration)
        results[policy] = stats
        
        print(f"  ING - Complétés: {stats['by_type']['ING']['completed']}, "
              f"Temps réponse: {stats['by_type']['ING']['avg_response_time']:.4f}")
        print(f"  PREPA - Complétés: {stats['by_type']['PREPA']['completed']}, "
              f"Temps réponse: {stats['by_type']['PREPA']['avg_response_time']:.4f}\n")
    
    return results


def scenario_real_data(tags_file: str, duration: float = 1000.0, seed: int = 42):
    """
    Scénario basé sur les données réelles
    
    Args:
        tags_file: Chemin vers le fichier tags
        duration: Durée de la simulation
        seed: Graine aléatoire
    """
    print("=== SCÉNARIO: Données Réelles ===\n")
    
    # Chargement des données réelles
    real_df = RealDataComparator.load_real_data(tags_file)
    arrival_rate = RealDataComparator.estimate_arrival_rate(real_df)
    
    print(f"Analyse des données réelles:")
    print(f"  Nombre total de soumissions: {len(real_df)}")
    print(f"  Taux d'arrivée estimé: {arrival_rate:.6f} jobs/seconde")
    print(f"  Période couverte: {real_df['receivedAt'].min()} à {real_df['receivedAt'].max()}\n")
    
    # Simulation avec les paramètres estimés
    service_rate = arrival_rate * 1.5  # Estimation conservatrice
    num_servers = 3
    
    print(f"Paramètres de simulation:")
    print(f"  λ: {arrival_rate:.6f}")
    print(f"  μ: {service_rate:.6f}")
    print(f"  c: {num_servers}\n")
    
    engine = SimulationEngine(random_seed=seed)
    
    from src.core import Server, JobGenerator
    server = Server(
        env=engine.env,
        server_id="real_data_server",
        num_servers=num_servers,
        logger=engine.logger
    )
    
    generator = JobGenerator(
        env=engine.env,
        logger=engine.logger,
        arrival_rate=arrival_rate,
        job_type="ING"
    )
    
    def service_time_gen():
        return random.expovariate(service_rate)
    
    engine.env.process(generator.generate(server, service_time_gen, duration))
    engine.run(duration)
    
    # Analyse
    df = engine.get_results()
    analyzer = PerformanceAnalyzer(df)
    summary = analyzer.get_summary(num_servers)
    
    print("Résultats de simulation:")
    print(f"  Débit: {summary['throughput']:.6f} jobs/seconde")
    print(f"  Utilisation: {summary['utilization']:.2%}")
    print(f"  Temps d'attente moyen: {summary['waiting_time']['mean']:.4f}s")
    print(f"  Temps de réponse moyen: {summary['response_time']['mean']:.4f}s\n")
    
    return df, summary


def main():
    """Point d'entrée principal"""
    parser = argparse.ArgumentParser(description="Simulateur de Moulinette ERO2")
    parser.add_argument('--scenario', type=str, 
                       choices=['basic', 'waterfall', 'backup', 'channels', 'real'],
                       default='basic',
                       help='Scénario à exécuter')
    parser.add_argument('--duration', type=float, default=1000.0,
                       help='Durée de la simulation')
    parser.add_argument('--seed', type=int, default=42,
                       help='Graine aléatoire')
    parser.add_argument('--tags-file', type=str, default='tags',
                       help='Chemin vers le fichier tags (pour scénario real)')
    parser.add_argument('--output-dir', type=str, default='results',
                       help='Répertoire de sortie pour les graphiques')
    parser.add_argument('--visualize', action='store_true',
                       help='Générer les visualisations')
    
    args = parser.parse_args()
    
    print(f"\n{'='*60}")
    print(f"  SIMULATEUR DE MOULINETTE - PROJET ERO2")
    print(f"{'='*60}\n")
    
    # Exécution du scénario
    df = None
    results = None
    
    if args.scenario == 'basic':
        df, results = scenario_basic(args.duration, args.seed)
    elif args.scenario == 'waterfall':
        df, results = scenario_waterfall(args.duration, args.seed)
    elif args.scenario == 'backup':
        df, results = scenario_backup(args.duration, args.seed)
    elif args.scenario == 'channels':
        results = scenario_channels(args.duration, args.seed)
    elif args.scenario == 'real':
        df, results = scenario_real_data(args.tags_file, args.duration, args.seed)
    
    # Visualisation
    if args.visualize and df is not None:
        print(f"Génération des visualisations dans {args.output_dir}/...")
        visualizer = Visualizer(df)
        visualizer.generate_full_report(args.output_dir, num_servers=2)
        print("Visualisations générées avec succès!\n")
    
    print(f"{'='*60}\n")


if __name__ == '__main__':
    main()
