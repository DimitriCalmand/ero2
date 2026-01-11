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
from src.capacity import WaterfallScenario
from src.reliability import (
    SystematicBackup,
    RandomBackup,
    ReliableServer,
    BackupComparison,
)
from src.regulation import ChannelsScenario
from src.analysis import (
    WarmupDetector,
    PerformanceAnalyzer,
    Visualizer,
    RealDataComparator,
    AdvancedMetricsAnalyzer,
    ParameterOptimizer,
    TimeSeriesAnalyzer,
    ReplaySimulation,
    PopulationAnalyzer
)
from src.regulation import GatingAnalyzer
from src.analysis.dashboard import Dashboard


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
    print(
        f"  ρ (utilisation théorique): {arrival_rate / (service_rate * num_servers):.2f}\n"
    )

    # Initialisation
    engine = SimulationEngine(random_seed=seed)

    from src.core import Server, JobGenerator

    server = Server(
        env=engine.env,
        server_id="basic_server",
        num_servers=num_servers,
        logger=engine.logger,
    )

    generator = JobGenerator(
        env=engine.env, logger=engine.logger, arrival_rate=arrival_rate, job_type="ING"
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


def scenario_waterfall(
    duration: float = 1000.0,
    seed: int = 42,
    include_infinite: bool = True,
    setup_only: bool = False,
):
    """
    Scénario Waterfall: comparaison files finies vs loss system, incluant simulation infinie

    Args:
        duration: Durée de la simulation
        seed: Graine aléatoire
        include_infinite: Inclure la simulation avec files infinies
        setup_only: Si True, retourne l'engine et les files pour le dashboard
    """
    print("=== SCÉNARIO WATERFALL: Analyses Multiples ===\n")

    if setup_only:
        print("--- Mode Dashboard (Configuration Reference) ---")
        config = {
            "name": "Reference (Standard)",
            "arrival": 6.0,  # High traffic to show queues filling
            "exec": 2.5,
            "feed": 1.5,
            "servers": 2,
            "ks": 10,
            "kf": 10,
        }
        engine = SimulationEngine(random_seed=seed)
        scenario = WaterfallScenario(
            env=engine.env,
            logger=engine.logger,
            num_servers=config["servers"],
            execution_queue_size=config["ks"],
            feedback_queue_size=config["kf"],
            execution_rate=config["exec"],
            feedback_rate=config["feed"],
            arrival_rate=config["arrival"],
            duration=duration,
        )
        engine.env.process(scenario.arrivals())
        return engine, {
            "Processing (Execution)": [scenario.execution_queue],
            "Output (Feedback)": [scenario.feedback_queue],
        }

    if include_infinite:
        print("--- Simulation Infinie (Files Illimitées) ---")
        # Paramètres pour la simulation infinie
        num_servers_inf = 2
        execution_rate_inf = 2.5
        feedback_rate_inf = 1.5
        arrival_rate_inf = 3.0

        print(
            f"Paramètres: λ={arrival_rate_inf}, μ_exec={execution_rate_inf}, μ_feed={feedback_rate_inf}, c={num_servers_inf}"
        )

        engine_infinite = SimulationEngine(random_seed=seed)
        scenario_infinite = WaterfallScenario(
            env=engine_infinite.env,
            logger=engine_infinite.logger,
            num_servers=num_servers_inf,
            execution_queue_size=10,  # Ignored
            execution_rate=execution_rate_inf,
            feedback_queue_size=10,  # Ignored
            feedback_rate=feedback_rate_inf,
            arrival_rate=arrival_rate_inf,
            duration=duration,
            finite=False,
        )

        engine_infinite.env.process(scenario_infinite.arrivals())
        engine_infinite.run(duration)

        sojourn_stats = scenario_infinite.get_sojourn_stats()
        exec_stats = scenario_infinite.execution_queue.get_stats()
        feed_stats = scenario_infinite.feedback_queue.get_stats()

        print("Résultats (Files Infinies):")
        print(f"  Jobs exécutés: {exec_stats['jobs_completed']}")
        print(f"  Jobs finalisés: {feed_stats['jobs_completed']}")
        print(f"  Temps de séjour moyen: {sojourn_stats['mean_sojourn_time']:.4f}")
        print(f"  Variance empirique: {sojourn_stats['sojourn_variance']:.4f}")
        print(
            f"  Rejets (Exec/Feed): {exec_stats['total_rejections']}/{feed_stats['total_rejections']}\n"
        )

    def run_waterfall_config(name, arrival, execution, feedback, servers, ks, kf):
        print(f"--- {name} ---")
        print(
            f"Paramètres: λ={arrival}, μ_exec={execution}, μ_feed={feedback}, c={servers}, ks={ks}, kf={kf}"
        )

        engine = SimulationEngine(random_seed=seed)

        # No Queue (Limit=0)
        scenario_no_queue = WaterfallScenario(
            env=engine.env,
            logger=engine.logger,
            num_servers=servers,
            execution_queue_size=0,
            execution_rate=execution,
            feedback_queue_size=0,
            feedback_rate=feedback,
            arrival_rate=arrival,
            duration=duration,
        )

        # With Queue
        scenario_with_queue = WaterfallScenario(
            env=engine.env,
            logger=engine.logger,
            num_servers=servers,
            execution_queue_size=ks,
            feedback_queue_size=kf,
            execution_rate=execution,
            feedback_rate=feedback,
            arrival_rate=arrival,
            duration=duration,
        )

        engine.env.process(scenario_no_queue.arrivals())
        engine.env.process(scenario_with_queue.arrivals())
        engine.run(duration)

        # Stats
        sojourn_stats = scenario_with_queue.get_sojourn_stats()
        stats_no_queue_exec = scenario_no_queue.execution_queue.get_stats()
        stats_no_queue_feed = scenario_no_queue.feedback_queue.get_stats()
        stats_with_queue_exec = scenario_with_queue.execution_queue.get_stats()
        stats_with_queue_feed = scenario_with_queue.feedback_queue.get_stats()

        print("\nRésultats:")
        print("  1. Sans File:")
        print(
            f"     Exec: {stats_no_queue_exec['jobs_completed']} complétés, {stats_no_queue_exec['rejection_rate']:.1%} rejets"
        )
        print(
            f"     Feed: {stats_no_queue_feed['jobs_completed']} complétés, {stats_no_queue_feed['rejection_rate']:.1%} rejets"
        )

        print(f"  2. Avec Files (ks={ks}, kf={kf}):")
        print(
            f"     Exec: {stats_with_queue_exec['jobs_completed']} complétés, {stats_with_queue_exec['rejection_rate']:.1%} rejets"
        )
        print(
            f"     Feed: {stats_with_queue_feed['jobs_completed']} complétés, {stats_with_queue_feed['rejection_rate']:.1%} rejets"
        )
        print(f"     Temps de séjour moyen: {sojourn_stats['mean_sojourn_time']:.4f}")
        print(f"     Variance empirique: {sojourn_stats['sojourn_variance']:.4f}")

        gain = (
            stats_with_queue_exec["jobs_completed"]
            - stats_no_queue_exec["jobs_completed"]
        )
        print(f"  Gain total (Exec): {gain:+d} jobs\n")

        return engine.get_results(), {
            "no_queue_exec": stats_no_queue_exec,
            "with_queue_exec": stats_with_queue_exec,
        }

    configs = [
        {
            "name": "Reference (Standard)",
            "arrival": 3.0,
            "exec": 2.5,
            "feed": 1.5,
            "servers": 2,
            "ks": 5,
            "kf": 5,
        },
        {
            "name": "Saturated Execution (Petit ks)",
            "arrival": 3.0,
            "exec": 2.5,
            "feed": 1.5,
            "servers": 2,
            "ks": 2,
            "kf": 10,
        },
        {
            "name": "Saturated Feedback (Petit kf)",
            "arrival": 3.0,
            "exec": 2.5,
            "feed": 1.5,
            "servers": 2,
            "ks": 10,
            "kf": 2,
        },
        {
            "name": "High Traffic",
            "arrival": 4.0,
            "exec": 3.0,
            "feed": 2.0,
            "servers": 3,
            "ks": 10,
            "kf": 10,
        },
        {
            "name": "Bottleneck Feedback",
            "arrival": 2.5,
            "exec": 4.0,
            "feed": 1.0,
            "servers": 2,
            "ks": 5,
            "kf": 2,
        },
        {
            "name": "Stable Feedback (High Feed Rate)",
            "arrival": 3.0,
            "exec": 2.5,
            "feed": 3.5,
            "servers": 2,
            "ks": 5,
            "kf": 5,
        },
    ]

    last_df = None
    all_results = {}

    for config in configs:
        df, res = run_waterfall_config(
            config["name"],
            config["arrival"],
            config["exec"],
            config["feed"],
            config["servers"],
            config["ks"],
            config["kf"],
        )
        last_df = df
        all_results[config["name"]] = res

    return last_df, all_results


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
        "systematic", num_servers, SystematicBackup(), backup_time_gen
    )

    comparison.add_server("random_50%", num_servers, RandomBackup(0.5), backup_time_gen)

    comparison.add_server("random_20%", num_servers, RandomBackup(0.2), backup_time_gen)

    # Exécution
    results = comparison.run_comparison(arrival_rate, service_rate, duration)

    for strategy, stats in results.items():
        print(f"Stratégie: {strategy}")
        print(f"  Jobs traités: {stats['jobs_processed']}")
        print(f"  Jobs sauvegardés: {stats['jobs_backed_up']}")
        print(f"  Taux backup: {stats['backup_rate']:.2%}")
        print(f"  Temps backup moyen: {stats['avg_backup_time']:.4f}\n")

    return engine.get_results(), results


def scenario_channels(
    duration: float = 1000.0, seed: int = 42, setup_only: bool = False
):
    """
    Scénario Channels: populations hétérogènes ING/PREPA

    Args:
        duration: Durée de la simulation
        seed: Graine aléatoire
        setup_only: Si True, retourne l'engine et les files pour le dashboard
    """
    print("=== SCÉNARIO CHANNELS: Populations Hétérogènes ===\n")

    # Paramètres
    lambda_ing = 1.5
    lambda_prepa = 0.5
    mu_ing = 2.5
    mu_prepa = 2.0
    num_servers = 2

    if setup_only:
        print("--- Mode Dashboard (Politique PRIORITY) ---")
        engine = SimulationEngine(random_seed=seed)
        scenario = ChannelsScenario(
            env=engine.env,
            logger=engine.logger,
            num_servers=num_servers,
            scheduling_policy="PRIORITY",
        )
        scenario.add_population("ING", lambda_ing, mu_ing)
        scenario.add_population("PREPA", lambda_prepa, mu_prepa)
        
        # Start generators for dashboard
        for pop_type, generator in scenario.populations.items():
            engine.env.process(generator.generate(scenario.server, duration))
            
        return engine, {"Priority Queue": [scenario.server.custom_queue]}

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
            scheduling_policy=policy,
        )

        scenario.add_population("ING", lambda_ing, mu_ing)
        scenario.add_population("PREPA", lambda_prepa, mu_prepa)

        stats = scenario.run(duration)
        results[policy] = stats

        print(
            f"  ING - Complétés: {stats['by_type']['ING']['completed']}, "
            f"Temps réponse: {stats['by_type']['ING']['avg_response_time']:.4f}"
        )
        print(
            f"  PREPA - Complétés: {stats['by_type']['PREPA']['completed']}, "
            f"Temps réponse: {stats['by_type']['PREPA']['avg_response_time']:.4f}\n"
        )

    return results


def scenario_real_data(tags_file: str, duration: float = 1000.0, seed: int = 42, use_replay: bool = False):
    """
    Scénario basé sur les données réelles

    Args:
        tags_file: Chemin vers le fichier tags
        duration: Durée de la simulation
        seed: Graine aléatoire
        use_replay: Si True, utilise le rejeu exact des timestamps
    """
    print("=== SCÉNARIO: Données Réelles ===\n")

    # Chargement des données réelles
    real_df = RealDataComparator.load_real_data(tags_file)
    
    # Analyse temporelle
    time_analyzer = TimeSeriesAnalyzer(real_df)
    patterns = time_analyzer.analyze_temporal_patterns()
    
    print(f"Analyse des données réelles:")
    print(f"  Nombre total de soumissions: {patterns['total_submissions']}")
    print(f"  Période: {patterns['period']['duration_days']} jours")
    print(f"  Heure de pic: {patterns['hourly_pattern']['peak_hour']}h")
    print(f"  Taux au pic: {patterns['hourly_pattern']['peak_rate']:.6f} jobs/s")
    print(f"  Ratio pic/creux: {patterns['hourly_pattern']['ratio_peak_to_min']:.2f}x\n")
    
    if use_replay:
        print("Mode: Rejeu exact des timestamps réels")
        service_rate = patterns['hourly_pattern']['peak_rate'] * 1.5
        num_servers = 3
        
        engine = SimulationEngine(random_seed=seed)
        
        from src.core import Server
        
        server = Server(
            env=engine.env,
            server_id="real_replay_server",
            num_servers=num_servers,
            logger=engine.logger,
        )
        
        def service_time_gen():
            return random.expovariate(service_rate)
        
        # Rejeu avec timestamps réels
        replay = ReplaySimulation(
            real_timestamps=real_df['receivedAt'].tolist(),
            env=engine.env,
            logger=engine.logger
        )
        
        engine.env.process(replay.replay_arrivals(
            server=server,
            service_time_generator=service_time_gen,
            duration=duration,
            time_scale=0.001  # Accélération 1000x
        ))
        
    else:
        print("Mode: Processus de Poisson avec λ moyen")
        arrival_rate = RealDataComparator.estimate_arrival_rate(real_df)
        service_rate = arrival_rate * 1.5
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
            logger=engine.logger,
        )

        generator = JobGenerator(
            env=engine.env, logger=engine.logger, arrival_rate=arrival_rate, job_type="ING"
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


def scenario_gating(duration: float = 1000.0, seed: int = 42):
    """
    Scénario Gating: test du barrage temporel avec populations hétérogènes
    
    Args:
        duration: Durée de la simulation
        seed: Graine aléatoire
    """
    print("=== SCÉNARIO GATING: Barrage Temporel ===\n")
    
    # Paramètres
    lambda_ing = 1.5
    lambda_prepa = 0.5
    mu_ing = 2.5
    mu_prepa = 2.0
    num_servers = 2
    
    # Intervalles de gating: fermeture de 100 unités, ouverture de 50 unités
    tb = 100
    gating_intervals = [
        (0, tb),           # Fermé 0-100
        (tb + 50, tb + 50 + tb),  # Fermé 150-250
        (tb + 50 + tb + 50, tb + 50 + tb + 50 + tb),  # Fermé 300-400
    ]
    
    print(f"Paramètres:")
    print(f"  Population ING: λ={lambda_ing}, μ={mu_ing}")
    print(f"  Population PREPA: λ={lambda_prepa}, μ={mu_prepa}")
    print(f"  Serveurs: {num_servers}")
    print(f"  Gating: tb={tb}, ouverture={tb//2}")
    print(f"  Intervalles de fermeture: {gating_intervals}\n")
    
    results = {}
    
    # Test 1: Sans gating (référence)
    print("--- Sans Gating (Référence) ---")
    engine_no_gating = SimulationEngine(random_seed=seed)
    scenario_no_gating = ChannelsScenario(
        env=engine_no_gating.env,
        logger=engine_no_gating.logger,
        num_servers=num_servers,
        scheduling_policy="FIFO",
        use_gating=False
    )
    
    scenario_no_gating.add_population("ING", lambda_ing, mu_ing)
    scenario_no_gating.add_population("PREPA", lambda_prepa, mu_prepa)
    
    stats_no_gating = scenario_no_gating.run(duration)
    results['no_gating'] = stats_no_gating
    
    print(f"  ING - Temps réponse: {stats_no_gating['by_type']['ING']['avg_response_time']:.4f}")
    print(f"  PREPA - Temps réponse: {stats_no_gating['by_type']['PREPA']['avg_response_time']:.4f}\n")
    
    # Test 2: Avec gating
    print("--- Avec Gating ---")
    engine_with_gating = SimulationEngine(random_seed=seed)
    scenario_with_gating = ChannelsScenario(
        env=engine_with_gating.env,
        logger=engine_with_gating.logger,
        num_servers=num_servers,
        scheduling_policy="FIFO",
        use_gating=True,
        gating_intervals=gating_intervals
    )
    
    scenario_with_gating.add_population("ING", lambda_ing, mu_ing)
    scenario_with_gating.add_population("PREPA", lambda_prepa, mu_prepa)
    
    stats_with_gating = scenario_with_gating.run(duration)
    results['with_gating'] = stats_with_gating
    
    print(f"  ING - Temps réponse: {stats_with_gating['by_type']['ING']['avg_response_time']:.4f}")
    print(f"  PREPA - Temps réponse: {stats_with_gating['by_type']['PREPA']['avg_response_time']:.4f}\n")
    
    # Comparaison
    print("--- Comparaison ---")
    for pop in ['ING', 'PREPA']:
        time_no_gating = stats_no_gating['by_type'][pop]['avg_response_time']
        time_with_gating = stats_with_gating['by_type'][pop]['avg_response_time']
        increase = ((time_with_gating - time_no_gating) / time_no_gating) * 100
        print(f"  {pop}: +{increase:.1f}% de temps avec gating")
    
    return results


def scenario_optimization(duration: float = 5000.0, seed: int = 42):
    """
    Scénario Optimization: recherche automatique des paramètres optimaux
    
    Args:
        duration: Durée de la simulation
        seed: Graine aléatoire
    """
    print("=== SCÉNARIO OPTIMIZATION: Recherche Paramètres Optimaux ===\n")
    
    # Paramètres du système
    arrival_rate = 3.0
    execution_rate = 2.5
    feedback_rate = 1.5
    num_servers = 2
    target_rejection = 0.05  # 5% maximum
    
    print(f"Configuration à optimiser:")
    print(f"  λ = {arrival_rate}")
    print(f"  μ_exec = {execution_rate}")
    print(f"  μ_feed = {feedback_rate}")
    print(f"  Serveurs = {num_servers}")
    print(f"  Taux de rejet cible: {target_rejection:.1%}\n")
    
    # Optimisation
    optimizer = ParameterOptimizer(random_seed=seed)
    
    results = optimizer.optimize_waterfall_capacity(
        arrival_rate=arrival_rate,
        execution_rate=execution_rate,
        feedback_rate=feedback_rate,
        num_servers=num_servers,
        duration=duration,
        target_rejection_rate=target_rejection,
        ks_range=(2, 12),
        kf_range=(2, 10)
    )
    
    # Affichage des résultats
    print(f"Statut: {results['status']}")
    print(f"Configurations évaluées: {results['total_evaluated']}")
    print(f"Solutions réalisables: {results['feasible_count']}\n")
    
    opt = results['optimal_configuration']
    print("Configuration optimale:")
    print(f"  ks (exécution): {opt['ks']}")
    print(f"  kf (feedback): {opt['kf']}")
    print(f"  Capacité totale: {opt['total_capacity']}")
    print(f"  Taux de rejet: {opt['overall_rejection_rate']:.2%}")
    print(f"  Débit: {opt['throughput']:.4f}")
    print(f"  Temps séjour moyen: {opt['mean_sojourn_time']:.4f}\n")
    
    # Génération des graphiques
    optimizer.plot_optimization_results('optimization_results')
    
    # Solutions Pareto-optimales
    pareto_solutions = optimizer.find_pareto_optimal(
        objectives=['total_capacity', 'overall_rejection_rate'],
        minimize=[True, True]
    )
    
    print(f"Solutions Pareto-optimales: {len(pareto_solutions)}")
    for i, sol in enumerate(pareto_solutions[:5], 1):
        print(f"  {i}. ks={sol['ks']}, kf={sol['kf']}, "
              f"capacité={sol['total_capacity']}, rejet={sol['overall_rejection_rate']:.2%}")
    
    return results


def scenario_advanced_analysis(duration: float = 1000.0, seed: int = 42):
    """
    Scénario Advanced Analysis: métriques avancées et comparaisons théoriques
    
    Args:
        duration: Durée de la simulation
        seed: Graine aléatoire
    """
    print("=== SCÉNARIO ADVANCED ANALYSIS: Métriques Avancées ===\n")
    
    # Paramètres
    arrival_rate = 2.0
    service_rate = 3.0
    num_servers = 2
    
    print(f"Paramètres:")
    print(f"  λ = {arrival_rate}")
    print(f"  μ = {service_rate}")
    print(f"  c = {num_servers}")
    print(f"  ρ = {arrival_rate/(service_rate*num_servers):.4f}\n")
    
    # Simulation
    engine = SimulationEngine(random_seed=seed)
    
    from src.core import Server, JobGenerator
    
    server = Server(
        env=engine.env,
        server_id="advanced_server",
        num_servers=num_servers,
        logger=engine.logger,
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
    
    # Analyse avancée
    df = engine.get_results()
    advanced_analyzer = AdvancedMetricsAnalyzer(df)
    
    # Vérification loi de Little
    print("--- Vérification Loi de Little ---")
    little = advanced_analyzer.calculate_little_law_verification()
    print(f"  L (observé): {little['L_observed']:.4f}")
    print(f"  λW: {little['lambda_W']:.4f}")
    print(f"  Erreur relative: {little['relative_error_percent']:.2f}%")
    print(f"  ✓ Loi vérifiée: {little['verifies_little_law']}\n")
    
    # Comparaison avec théorie M/M/c
    print("--- Comparaison avec Théorie M/M/c ---")
    comparison = advanced_analyzer.compare_simulation_to_theory(
        arrival_rate, service_rate, num_servers
    )
    
    if comparison['comparison_valid']:
        print(f"  Précision: {comparison['simulation_accuracy']}")
        print(f"  Erreur moyenne: {comparison['average_error_percent']:.2f}%\n")
        
        print("  Utilisation:")
        print(f"    Simulée: {comparison['utilization']['simulated']:.4f}")
        print(f"    Théorique: {comparison['utilization']['theoretical']:.4f}")
        print(f"    Erreur: {comparison['utilization']['error_percent']:.2f}%\n")
        
        print("  Temps d'attente:")
        print(f"    Simulé: {comparison['waiting_time']['simulated']:.4f}")
        print(f"    Théorique: {comparison['waiting_time']['theoretical']:.4f}")
        print(f"    Erreur: {comparison['waiting_time']['error_percent']:.2f}%\n")
    
    # Analyse variance/moyenne
    print("--- Analyse Variance/Moyenne ---")
    var_mean = advanced_analyzer.calculate_variance_to_mean_ratio()
    for metric, data in var_mean.items():
        print(f"  {metric}: ratio={data['ratio']:.4f} ({data['interpretation']})")
    print()
    
    # Génération rapport complet
    report = advanced_analyzer.generate_advanced_report(
        arrival_rate, service_rate, num_servers,
        output_file='advanced_analysis_report.txt'
    )
    
    print("Rapport complet généré: advanced_analysis_report.txt")
    
    return df, comparison


def scenario_gating_analysis(duration: float = 1000.0, seed: int = 42):
    """
    Scénario Gating Analysis: analyse approfondie du barrage temporel
    
    Args:
        duration: Durée de la simulation
        seed: Graine aléatoire
    """
    print("=== SCÉNARIO GATING ANALYSIS: Analyse Approfondie ===\n")
    
    # Configuration
    lambda_ing = 1.5
    lambda_prepa = 0.5
    mu_ing = 2.5
    mu_prepa = 2.0
    num_servers = 2
    
    print(f"Paramètres:")
    print(f"  Population ING: λ={lambda_ing}, μ={mu_ing}")
    print(f"  Population PREPA: λ={lambda_prepa}, μ={mu_prepa}")
    print(f"  Serveurs: {num_servers}\n")
    
    # Créer l'analyseur
    analyzer = GatingAnalyzer(
        lambda_ing=lambda_ing,
        mu_ing=mu_ing,
        lambda_prepa=lambda_prepa,
        mu_prepa=mu_prepa,
        num_servers=num_servers
    )
    
    # Test de différentes configurations
    tb_values = [50, 100, 150, 200]
    ratio_values = [0.25, 0.33, 0.5, 0.75]  # tb/4, tb/3, tb/2, 3tb/4
    
    print(f"Test de configurations:")
    print(f"  Blocking durations (tb): {tb_values}")
    print(f"  Opening ratios: {ratio_values}")
    print(f"  Total configurations: {len(tb_values) * len(ratio_values)}\n")
    
    print("Exécution des simulations...")
    results_df = analyzer.analyze_gating_variations(
        tb_values=tb_values,
        ratio_values=ratio_values,
        duration=duration,
        seed=seed
    )
    
    print(f"\n✓ {len(results_df)} configurations testées\n")
    
    # Générer visualisations
    print("Génération des visualisations...")
    analyzer.plot_gating_impact(results_df)
    
    # Recommandation
    print("\n--- Recherche de Configuration Optimale ---")
    recommendation = analyzer.recommend_gating_config(
        results_df,
        max_time_increase_pct=100.0  # Accepter jusqu'à 100% d'augmentation
    )
    
    print(f"Statut: {recommendation['status']}")
    if recommendation['status'] == 'optimal_found':
        print(f"  tb optimal: {recommendation['tb']} unités")
        print(f"  Ratio optimal: {recommendation['ratio']:.2f}")
        print(f"  Durée d'ouverture: {recommendation['opening_duration']} unités")
        print(f"  Impact ING: +{recommendation['ing_time_increase_pct']:.2f}%")
        print(f"  Impact PREPA: +{recommendation['prepa_time_increase_pct']:.2f}%")
        print(f"  Queue max: {recommendation['max_queue_length']:.1f} jobs")
    else:
        print(f"  Message: {recommendation['message']}")
    
    # Créer rapport détaillé
    print("\n--- Génération du Rapport ---")
    analyzer.create_analysis_report(results_df, recommendation)
    
    # Analyse des populations
    print("\n--- Analyse des Populations ---")
    
    # Exécuter une simulation de référence pour analyse détaillée
    engine = SimulationEngine(random_seed=seed)
    scenario = ChannelsScenario(
        env=engine.env,
        logger=engine.logger,
        num_servers=num_servers,
        scheduling_policy="FIFO",
        use_gating=False
    )
    scenario.add_population("ING", lambda_ing, mu_ing)
    scenario.add_population("PREPA", lambda_prepa, mu_prepa)
    scenario.run(duration)
    
    df = engine.logger.get_dataframe()
    pop_analyzer = PopulationAnalyzer(df)
    
    # Fairness index
    fairness = pop_analyzer.calculate_fairness_index()
    print(f"Jain's Fairness Index: {fairness['fairness_index']:.4f}")
    print(f"  Interprétation: {fairness['interpretation']}")
    print(f"  Ratio temps réponse: {fairness['response_time_ratio']:.2f}x")
    
    # Percentiles
    percentiles = pop_analyzer.calculate_percentiles_by_type()
    print("\nPercentiles par population:")
    for pop_type, stats in percentiles.items():
        print(f"  {pop_type}:")
        print(f"    P50: {stats['response_time']['p50']:.4f}s")
        print(f"    P95: {stats['response_time']['p95']:.4f}s")
        print(f"    P99: {stats['response_time']['p99']:.4f}s")
    
    # SLA compliance
    sla_thresholds = {"ING": 1.0, "PREPA": 2.0}
    compliance = pop_analyzer.calculate_sla_compliance(sla_thresholds)
    print("\nSLA Compliance:")
    for pop_type, comp in compliance.items():
        print(f"  {pop_type} (seuil {comp['threshold']}s):")
        print(f"    Conformité: {comp['compliance_percentage']:.2f}%")
        print(f"    Statut: {comp['status'].upper()}")
    
    # Génération rapport complet
    pop_analyzer.generate_population_report(
        sla_thresholds=sla_thresholds,
        output_file="population_analysis_report.txt"
    )
    
    print("\n✓ Tous les rapports générés")
    print("  - gating_analysis/gating_impact_heatmaps.png")
    print("  - gating_analysis/gating_impact_curves.png")
    print("  - gating_analysis/analysis_report.txt")
    print("  - population_analysis_report.txt")
    
    return results_df, recommendation, fairness


def main():
    """Point d'entrée principal"""
    parser = argparse.ArgumentParser(description="Simulateur de Moulinette ERO2")
    parser.add_argument(
        "--scenario",
        type=str,
        choices=["basic", "waterfall", "backup", "channels", "real", "gating", "optimization", "advanced", "gating-analysis"],
        default="basic",
        help="Scénario à exécuter",
    )
    parser.add_argument(
        "--duration", type=float, default=1000.0, help="Durée de la simulation"
    )
    parser.add_argument("--seed", type=int, default=42, help="Graine aléatoire")
    parser.add_argument(
        "--include-infinite",
        action="store_true",
        help="Inclure simulation avec files infinies (waterfall)",
    )
    parser.add_argument(
        "--use-replay",
        action="store_true",
        help="Utiliser le rejeu exact des timestamps (scénario real)",
    )
    parser.add_argument(
        "--tags-file",
        type=str,
        default="tags",
        help="Chemin vers le fichier tags (pour scénario real)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="results",
        help="Répertoire de sortie pour les graphiques",
    )
    parser.add_argument(
        "--visualize", action="store_true", help="Générer les visualisations"
    )
    parser.add_argument(
        "--dashboard", action="store_true", help="Lancer le dashboard interactif"
    )

    args = parser.parse_args()

    print(f"\n{'=' * 60}")
    print(f"  SIMULATEUR DE MOULINETTE - PROJET ERO2")
    print(f"{'=' * 60}\n")

    # Dashboard Mode
    if args.dashboard:
        print("Lancement du Dashboard Interactif...")
        engine = None
        queues_groups = None

        if args.scenario == "waterfall":
            engine, queues_groups = scenario_waterfall(
                args.duration, args.seed, setup_only=True
            )
        elif args.scenario == "channels":
            engine, queues_groups = scenario_channels(
                args.duration, args.seed, setup_only=True
            )
        else:
            print(f"Le scénario '{args.scenario}' ne supporte pas encore le dashboard.")
            return

        dashboard = Dashboard(engine, queues_groups, args.duration)
        dashboard.show()
        return

    # Exécution du scénario
    df = None
    results = None

    if args.scenario == "basic":
        df, results = scenario_basic(args.duration, args.seed)
    elif args.scenario == "waterfall":
        df, results = scenario_waterfall(
            args.duration, args.seed, args.include_infinite
        )
    elif args.scenario == "backup":
        df, results = scenario_backup(args.duration, args.seed)
    elif args.scenario == "channels":
        results = scenario_channels(args.duration, args.seed)
    elif args.scenario == "real":
        df, results = scenario_real_data(args.tags_file, args.duration, args.seed, args.use_replay)
    elif args.scenario == "gating":
        results = scenario_gating(args.duration, args.seed)
    elif args.scenario == "optimization":
        results = scenario_optimization(args.duration, args.seed)
    elif args.scenario == "advanced":
        df, results = scenario_advanced_analysis(args.duration, args.seed)
    elif args.scenario == "gating-analysis":
        results_df, recommendation, fairness = scenario_gating_analysis(args.duration, args.seed)
        df = None  # Multiple simulations, no single df

    # Visualisation
    if args.visualize and df is not None:
        print(f"Génération des visualisations dans {args.output_dir}/...")
        visualizer = Visualizer(df)
        visualizer.generate_full_report(args.output_dir, num_servers=2)
        print("Visualisations générées avec succès!\n")

    print(f"{'=' * 60}\n")


if __name__ == "__main__":
    main()
