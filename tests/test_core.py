#!/usr/bin/env python3
"""
Tests unitaires pour le module Core
"""

import sys
import random
from pathlib import Path

# Ajout du répertoire racine au PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core import (
    SimulationEngine, Job, Server, JobGenerator, EventType
)


def test_job_creation():
    """Test de création de jobs"""
    print("Test: Création de jobs...")
    
    job = Job(arrival_time=0.0, job_type="ING", assignment="test")
    assert job.arrival_time == 0.0
    assert job.job_type == "ING"
    assert job.assignment == "test"
    assert job.was_rejected == False
    
    print("  ✓ Job créé correctement")


def test_simulation_engine():
    """Test du moteur de simulation"""
    print("Test: Moteur de simulation...")
    
    engine = SimulationEngine(random_seed=42)
    
    # Création d'un serveur simple
    server = Server(
        env=engine.env,
        server_id="test_server",
        num_servers=1,
        logger=engine.logger
    )
    
    # Création d'un générateur
    generator = JobGenerator(
        env=engine.env,
        logger=engine.logger,
        arrival_rate=2.0,
        job_type="ING"
    )
    
    # Temps de service
    def service_time_gen():
        return random.expovariate(3.0)
    
    # Lancement
    engine.env.process(generator.generate(server, service_time_gen, 100.0))
    engine.run(100.0)
    
    # Vérifications
    results = engine.get_results()
    assert len(results) > 0, "Aucun événement enregistré"
    
    summary = engine.get_summary()
    assert summary['total_arrivals'] > 0, "Aucune arrivée"
    assert summary['total_completed'] > 0, "Aucun job complété"
    
    print(f"  ✓ {summary['total_arrivals']} arrivées")
    print(f"  ✓ {summary['total_completed']} complétés")
    print(f"  ✓ Durée: {summary['simulation_duration']:.2f}")


def test_job_metrics():
    """Test des métriques de jobs"""
    print("Test: Métriques de jobs...")
    
    job = Job(arrival_time=10.0, job_type="ING")
    job.start_time = 15.0
    job.service_time = 5.0
    job.end_time = 20.0
    
    assert job.get_waiting_time() == 5.0, "Temps d'attente incorrect"
    assert job.get_response_time() == 10.0, "Temps de réponse incorrect"
    
    print("  ✓ Temps d'attente: 5.0")
    print("  ✓ Temps de réponse: 10.0")


def run_all_tests():
    """Exécute tous les tests"""
    print("\n" + "="*60)
    print("  TESTS MODULE CORE")
    print("="*60 + "\n")
    
    try:
        test_job_creation()
        print()
        test_job_metrics()
        print()
        test_simulation_engine()
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
