#!/usr/bin/env python3
"""
Tests unitaires pour le module Capacity
"""

import sys
import random
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core import SimulationEngine, Job
from src.capacity import LimitedQueue, LossSystem, WaterfallScenario


def test_limited_queue():
    """Test de la file limitée"""
    print("Test: File limitée...")
    
    engine = SimulationEngine(random_seed=42)
    
    queue = LimitedQueue(
        env=engine.env,
        queue_id="test_queue",
        max_queue_size=5,
        num_servers=2,
        logger=engine.logger
    )
    
    # Génération de jobs
    def service_time_gen():
        return random.expovariate(3.0)
    
    def arrivals():
        for i in range(20):
            yield engine.env.timeout(random.expovariate(5.0))
            job = Job(arrival_time=engine.env.now, job_type="ING")
            engine.env.process(queue.process_job(job, service_time_gen))
    
    engine.env.process(arrivals())
    engine.run(10.0)
    
    stats = queue.get_stats()
    print(f"  ✓ Arrivées: {stats['total_arrivals']}")
    print(f"  ✓ Complétés: {stats['jobs_completed']}")
    print(f"  ✓ Rejets: {stats['total_rejections']}")
    print(f"  ✓ Taux de rejet: {stats['rejection_rate']:.2%}")
    
    assert stats['total_arrivals'] > 0, "Aucune arrivée"


def test_loss_system():
    """Test du système avec perte"""
    print("Test: Loss System...")
    
    engine = SimulationEngine(random_seed=42)
    
    loss_system = LossSystem(
        env=engine.env,
        system_id="test_loss",
        num_servers=2,
        logger=engine.logger
    )
    
    def service_time_gen():
        return random.expovariate(1.0)
    
    def arrivals():
        for i in range(20):
            yield engine.env.timeout(random.expovariate(5.0))
            job = Job(arrival_time=engine.env.now, job_type="ING")
            engine.env.process(loss_system.process_job(job, service_time_gen))
    
    engine.env.process(arrivals())
    engine.run(10.0)
    
    stats = loss_system.get_stats()
    print(f"  ✓ Arrivées: {stats['total_arrivals']}")
    print(f"  ✓ Complétés: {stats['jobs_completed']}")
    print(f"  ✓ Rejets: {stats['total_rejections']}")
    print(f"  ✓ Prob. blocage: {stats['blocking_probability']:.2%}")


def test_waterfall_comparison():
    """Test de comparaison Waterfall"""
    print("Test: Comparaison Waterfall...")
    
    engine = SimulationEngine(random_seed=42)
    
    scenario = WaterfallScenario(
        env=engine.env,
        logger=engine.logger,
        num_servers=2,
        max_queue_size=5
    )
    
    results = scenario.run_comparison(
        arrival_rate=3.0,
        service_rate=2.0,
        duration=50.0
    )
    
    print(f"  ✓ File limitée - Complétés: {results['limited_queue']['jobs_completed']}")
    print(f"  ✓ Loss system - Complétés: {results['loss_system']['jobs_completed']}")
    print(f"  ✓ Avantage file: +{results['comparison']['queue_advantage']} jobs")
    
    assert results['limited_queue']['total_arrivals'] > 0
    assert results['loss_system']['total_arrivals'] > 0


def run_all_tests():
    """Exécute tous les tests"""
    print("\n" + "="*60)
    print("  TESTS MODULE CAPACITY")
    print("="*60 + "\n")
    
    try:
        test_limited_queue()
        print()
        test_loss_system()
        print()
        test_waterfall_comparison()
        print()
        
        print("="*60)
        print("  ✓ TOUS LES TESTS RÉUSSIS")
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
