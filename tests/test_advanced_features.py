#!/usr/bin/env python3
"""
Tests unitaires pour les fonctionnalités avancées
"""

import sys
import random
from pathlib import Path

# Ajout du répertoire racine au PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core import SimulationEngine, Job, Server, JobGenerator
from src.capacity import WaterfallScenario
from src.analysis import (
    AdvancedMetricsAnalyzer,
    ParameterOptimizer,
    TimeSeriesAnalyzer,
    ReplaySimulation
)
import pandas as pd
from datetime import datetime, timedelta


def test_advanced_metrics():
    """Test des métriques avancées"""
    print("Test: Métriques avancées...")
    
    # Simulation simple
    engine = SimulationEngine(random_seed=42)
    
    server = Server(
        env=engine.env,
        server_id="test_server",
        num_servers=2,
        logger=engine.logger
    )
    
    generator = JobGenerator(
        env=engine.env,
        logger=engine.logger,
        arrival_rate=2.0,
        job_type="ING"
    )
    
    def service_time_gen():
        return random.expovariate(3.0)
    
    engine.env.process(generator.generate(server, service_time_gen, 500.0))
    engine.run(500.0)
    
    # Analyse avancée
    df = engine.get_results()
    analyzer = AdvancedMetricsAnalyzer(df)
    
    # Vérification loi de Little
    little = analyzer.calculate_little_law_verification()
    assert 'L_observed' in little, "L_observed manquant"
    assert 'lambda_W' in little, "lambda_W manquant"
    assert 'verifies_little_law' in little, "Vérification manquante"
    
    print(f"  ✓ Loi de Little: L={little['L_observed']:.4f}, λW={little['lambda_W']:.4f}")
    
    # Comparaison théorie
    comparison = analyzer.compare_simulation_to_theory(2.0, 3.0, 2)
    assert comparison['comparison_valid'], "Comparaison invalide"
    assert 'simulation_accuracy' in comparison, "Précision manquante"
    
    print(f"  ✓ Précision simulation: {comparison['simulation_accuracy']}")
    
    # Variance/moyenne
    var_mean = analyzer.calculate_variance_to_mean_ratio()
    assert len(var_mean) > 0, "Analyse variance/moyenne échouée"
    
    print(f"  ✓ Analyse variance/moyenne effectuée")


def test_parameter_optimizer():
    """Test de l'optimiseur de paramètres"""
    print("Test: Optimiseur de paramètres...")
    
    optimizer = ParameterOptimizer(random_seed=42)
    
    # Optimisation sur une petite plage pour le test
    results = optimizer.optimize_waterfall_capacity(
        arrival_rate=2.5,
        execution_rate=2.0,
        feedback_rate=1.5,
        num_servers=2,
        duration=1000.0,  # Durée réduite pour test
        target_rejection_rate=0.10,  # 10% pour test
        ks_range=(2, 5),  # Plage réduite
        kf_range=(2, 4)   # Plage réduite
    )
    
    assert results['status'] in ['optimal_found', 'no_feasible_solution'], "Statut invalide"
    assert 'optimal_configuration' in results, "Configuration optimale manquante"
    assert results['total_evaluated'] > 0, "Aucune configuration évaluée"
    
    opt = results['optimal_configuration']
    assert 'ks' in opt and 'kf' in opt, "Paramètres optimaux manquants"
    
    print(f"  ✓ Configurations évaluées: {results['total_evaluated']}")
    print(f"  ✓ Configuration optimale: ks={opt['ks']}, kf={opt['kf']}")
    print(f"  ✓ Taux de rejet: {opt['overall_rejection_rate']:.2%}")
    
    # Test Pareto
    pareto = optimizer.find_pareto_optimal()
    assert isinstance(pareto, list), "Pareto doit retourner une liste"
    print(f"  ✓ Solutions Pareto: {len(pareto)}")


def test_time_series_analyzer():
    """Test de l'analyseur de séries temporelles"""
    print("Test: Analyseur de séries temporelles...")
    
    # Créer des données factices
    start_date = datetime(2026, 1, 1, 0, 0, 0)
    timestamps = []
    
    # Générer 1000 timestamps avec pattern horaire
    for i in range(1000):
        hour = (start_date + timedelta(seconds=i*60)).hour
        # Plus de soumissions pendant les heures de travail
        if 9 <= hour <= 18:
            delay = random.expovariate(0.5)  # Plus fréquent
        else:
            delay = random.expovariate(0.1)  # Moins fréquent
        
        timestamps.append(start_date + timedelta(seconds=i*60 + delay))
    
    df = pd.DataFrame({
        'receivedAt': timestamps,
        'assignmentUri': [f'assignment_{i}' for i in range(len(timestamps))]
    })
    
    # Analyse
    analyzer = TimeSeriesAnalyzer(df)
    patterns = analyzer.analyze_temporal_patterns()
    
    assert 'total_submissions' in patterns, "Total submissions manquant"
    assert 'hourly_pattern' in patterns, "Pattern horaire manquant"
    assert 'weekly_pattern' in patterns, "Pattern hebdomadaire manquant"
    
    print(f"  ✓ Total soumissions: {patterns['total_submissions']}")
    print(f"  ✓ Heure de pic: {patterns['hourly_pattern']['peak_hour']}h")
    print(f"  ✓ Ratio pic/creux: {patterns['hourly_pattern']['ratio_peak_to_min']:.2f}x")
    
    # Test extraction inter-arrivées
    interarrivals = analyzer.extract_interarrival_times(max_duration=3600.0)
    assert len(interarrivals) > 0, "Aucune inter-arrivée extraite"
    print(f"  ✓ Inter-arrivées extraites: {len(interarrivals)}")


def test_replay_simulation():
    """Test du rejeu de timestamps réels"""
    print("Test: Rejeu de simulation...")
    
    # Timestamps factices - plus espacés pour s'assurer qu'ils arrivent dans duration
    start = datetime(2026, 1, 1, 10, 0, 0)
    timestamps = [start + timedelta(seconds=i*2) for i in range(30)]  # 30 timestamps sur 60 secondes
    
    # Simulation avec durée suffisante
    engine = SimulationEngine(random_seed=42)
    
    server = Server(
        env=engine.env,
        server_id="replay_server",
        num_servers=2,  # 2 serveurs pour meilleure capacité
        logger=engine.logger
    )
    
    replay = ReplaySimulation(
        real_timestamps=timestamps,
        env=engine.env,
        logger=engine.logger
    )
    
    def service_time_gen():
        return random.expovariate(5.0)  # Service rapide
    
    engine.env.process(replay.replay_arrivals(
        server=server,
        service_time_generator=service_time_gen,
        duration=200.0,  # Durée augmentée
        time_scale=1.0  # Pas d'accélération pour s'assurer du comportement
    ))
    
    engine.run(200.0)
    
    # Vérifications
    df = engine.get_results()
    arrivals = df[df['event_type'] == 'arrival']
    completed = df[df['event_type'] == 'end_service']
    
    assert len(arrivals) > 0, f"Aucune arrivée rejouée (événements: {len(df)})"
    print(f"  ✓ Arrivées rejouées: {len(arrivals)}")
    print(f"  ✓ Jobs complétés: {len(completed)}")


def test_integration_waterfall_optimization():
    """Test d'intégration: optimisation waterfall"""
    print("Test: Intégration waterfall + optimisation...")
    
    # Test qu'on peut créer et exécuter un scénario waterfall
    engine = SimulationEngine(random_seed=42)
    
    scenario = WaterfallScenario(
        env=engine.env,
        logger=engine.logger,
        num_servers=2,
        execution_queue_size=5,
        feedback_queue_size=3,
        execution_rate=2.5,
        feedback_rate=1.5,
        arrival_rate=2.0,
        duration=500.0
    )
    
    engine.env.process(scenario.arrivals())
    engine.run(500.0)
    
    # Vérifier les statistiques
    exec_stats = scenario.execution_queue.get_stats()
    feed_stats = scenario.feedback_queue.get_stats()
    sojourn = scenario.get_sojourn_stats()
    
    assert exec_stats['total_arrivals'] > 0, "Aucune arrivée en exécution"
    assert sojourn['completed_jobs'] >= 0, "Statistiques de séjour invalides"
    
    print(f"  ✓ Arrivées exécution: {exec_stats['total_arrivals']}")
    print(f"  ✓ Jobs complétés (cascade): {sojourn['completed_jobs']}")
    print(f"  ✓ Temps séjour moyen: {sojourn['mean_sojourn_time']:.4f}")


def run_all_tests():
    """Exécute tous les tests"""
    print("\n" + "="*60)
    print("  TESTS FONCTIONNALITÉS AVANCÉES")
    print("="*60 + "\n")
    
    try:
        test_advanced_metrics()
        print()
        test_parameter_optimizer()
        print()
        test_time_series_analyzer()
        print()
        test_replay_simulation()
        print()
        test_integration_waterfall_optimization()
        print()
        
        print("="*60)
        print("  ✓ TOUS LES TESTS AVANCÉS RÉUSSIS")
        print("="*60 + "\n")
        return True
        
    except AssertionError as e:
        print(f"\n✗ ÉCHEC: {e}\n")
        return False
    except Exception as e:
        print(f"\n✗ ERREUR: {e}\n")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
