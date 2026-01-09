#!/usr/bin/env python3
"""
Tests unitaires pour le module Regulation
"""

import sys
import random
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core import SimulationEngine
from src.regulation import (
    PriorityQueue, GatingController, HeterogeneousServer, ChannelsScenario
)
from src.core import Job


def test_priority_queue():
    """Test de la file prioritaire"""
    print("Test: File prioritaire...")
    
    queue = PriorityQueue()
    
    # Ajout de jobs
    job1 = Job(arrival_time=0.0, job_type="ING")
    job1.service_time = 5.0
    
    job2 = Job(arrival_time=1.0, job_type="PREPA")
    job2.service_time = 2.0
    
    job3 = Job(arrival_time=2.0, job_type="ING")
    job3.service_time = 8.0
    
    queue.add(job1)
    queue.add(job2)
    queue.add(job3)
    
    # Test FIFO
    next_job = queue.get_next_fifo()
    assert next_job.id == job1.id, "FIFO devrait retourner job1"
    print("  ✓ FIFO fonctionne")
    
    # Réinitialisation
    queue = PriorityQueue()
    queue.add(job1)
    queue.add(job2)
    queue.add(job3)
    
    # Test SJF
    next_job = queue.get_next_sjf()
    assert next_job.id == job2.id, "SJF devrait retourner job2 (plus court)"
    print("  ✓ SJF fonctionne")
    
    # Test Priority
    queue = PriorityQueue()
    queue.add(job2)  # PREPA
    queue.add(job1)  # ING
    
    next_job = queue.get_next_priority(["ING", "PREPA"])
    assert next_job.id == job1.id, "Priority devrait favoriser ING"
    print("  ✓ Priority fonctionne")


def test_gating_controller():
    """Test du contrôleur de gating"""
    print("Test: Gating Controller...")
    
    engine = SimulationEngine(random_seed=42)
    
    # Fermeture entre t=10 et t=20
    gating = GatingController(
        env=engine.env,
        gating_intervals=[(10.0, 20.0), (30.0, 40.0)]
    )
    
    # Test à différents moments
    assert gating.is_open(5.0) == True, "Devrait être ouvert à t=5"
    assert gating.is_open(15.0) == False, "Devrait être fermé à t=15"
    assert gating.is_open(25.0) == True, "Devrait être ouvert à t=25"
    assert gating.is_open(35.0) == False, "Devrait être fermé à t=35"
    
    print("  ✓ Gating Controller fonctionne")


def test_heterogeneous_server():
    """Test du serveur hétérogène"""
    print("Test: Serveur hétérogène...")
    
    engine = SimulationEngine(random_seed=42)
    
    server = HeterogeneousServer(
        env=engine.env,
        server_id="hetero_test",
        num_servers=2,
        logger=engine.logger,
        scheduling_policy="FIFO"
    )
    
    def service_time_gen():
        return random.expovariate(3.0)
    
    def arrivals():
        for i in range(5):
            yield engine.env.timeout(random.expovariate(2.0))
            job = Job(arrival_time=engine.env.now, job_type="ING")
            engine.env.process(server.process_job(job, service_time_gen))
        
        for i in range(5):
            yield engine.env.timeout(random.expovariate(2.0))
            job = Job(arrival_time=engine.env.now, job_type="PREPA")
            engine.env.process(server.process_job(job, service_time_gen))
    
    engine.env.process(arrivals())
    engine.run(20.0)
    
    stats = server.get_stats()
    print(f"  ✓ ING complétés: {stats['by_type'].get('ING', {}).get('completed', 0)}")
    print(f"  ✓ PREPA complétés: {stats['by_type'].get('PREPA', {}).get('completed', 0)}")


def test_channels_scenario():
    """Test du scénario Channels"""
    print("Test: Scénario Channels...")
    
    engine = SimulationEngine(random_seed=42)
    
    scenario = ChannelsScenario(
        env=engine.env,
        logger=engine.logger,
        num_servers=2,
        scheduling_policy="FIFO"
    )
    
    scenario.add_population("ING", arrival_rate=1.5, service_rate=2.5)
    scenario.add_population("PREPA", arrival_rate=0.5, service_rate=2.0)
    
    results = scenario.run(50.0)
    
    print(f"  ✓ ING: {results['by_type']['ING']['completed']} complétés")
    print(f"  ✓ PREPA: {results['by_type']['PREPA']['completed']} complétés")
    
    assert results['by_type']['ING']['completed'] > 0
    assert results['by_type']['PREPA']['completed'] > 0


def run_all_tests():
    """Exécute tous les tests"""
    print("\n" + "="*60)
    print("  TESTS MODULE REGULATION")
    print("="*60 + "\n")
    
    try:
        test_priority_queue()
        print()
        test_gating_controller()
        print()
        test_heterogeneous_server()
        print()
        test_channels_scenario()
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
