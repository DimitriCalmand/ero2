#!/usr/bin/env python3
"""
Tests unitaires pour le module Reliability
"""

import sys
import random
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core import SimulationEngine, Job
from src.reliability import (
    SystematicBackup, RandomBackup, ReliableServer, BackupComparison
)


def test_systematic_backup():
    """Test du backup systématique"""
    print("Test: Backup systématique...")
    
    strategy = SystematicBackup()
    job = Job(arrival_time=0.0, job_type="ING")
    
    assert strategy.should_backup(job) == True, "Devrait toujours sauvegarder"
    print("  ✓ Backup systématique fonctionne")


def test_random_backup():
    """Test du backup aléatoire"""
    print("Test: Backup aléatoire...")
    
    strategy = RandomBackup(backup_probability=0.5)
    
    # Test sur plusieurs jobs
    backups = 0
    for i in range(100):
        job = Job(arrival_time=i, job_type="ING")
        if strategy.should_backup(job):
            backups += 1
    
    # Devrait être proche de 50%
    ratio = backups / 100
    assert 0.3 < ratio < 0.7, f"Ratio de backup {ratio:.2f} trop éloigné de 0.5"
    print(f"  ✓ Backup aléatoire: {ratio:.2%} (attendu ~50%)")


def test_reliable_server():
    """Test du serveur avec backup"""
    print("Test: Serveur avec backup...")
    
    engine = SimulationEngine(random_seed=42)
    
    server = ReliableServer(
        env=engine.env,
        server_id="reliable_test",
        num_servers=2,
        logger=engine.logger,
        backup_strategy=RandomBackup(0.5),
        backup_time_generator=lambda: random.expovariate(10.0)
    )
    
    def service_time_gen():
        return random.expovariate(3.0)
    
    def arrivals():
        for i in range(10):
            yield engine.env.timeout(random.expovariate(2.0))
            job = Job(arrival_time=engine.env.now, job_type="ING")
            engine.env.process(server.process_with_backup(job, service_time_gen))
    
    engine.env.process(arrivals())
    engine.run(20.0)
    
    stats = server.get_stats()
    print(f"  ✓ Jobs traités: {stats['jobs_processed']}")
    print(f"  ✓ Jobs sauvegardés: {stats['jobs_backed_up']}")
    print(f"  ✓ Taux backup: {stats['backup_rate']:.2%}")


def test_backup_comparison():
    """Test de comparaison des stratégies"""
    print("Test: Comparaison stratégies backup...")
    
    engine = SimulationEngine(random_seed=42)
    comparison = BackupComparison(env=engine.env, logger=engine.logger)
    
    comparison.add_server(
        "systematic",
        num_servers=2,
        backup_strategy=SystematicBackup(),
        backup_time_generator=lambda: random.expovariate(10.0)
    )
    
    comparison.add_server(
        "random",
        num_servers=2,
        backup_strategy=RandomBackup(0.5),
        backup_time_generator=lambda: random.expovariate(10.0)
    )
    
    results = comparison.run_comparison(
        arrival_rate=2.0,
        service_rate=3.0,
        duration=50.0
    )
    
    print(f"  ✓ Systematic: {results['systematic']['jobs_processed']} jobs")
    print(f"  ✓ Random: {results['random']['jobs_processed']} jobs")
    
    assert results['systematic']['jobs_processed'] > 0
    assert results['random']['jobs_processed'] > 0


def run_all_tests():
    """Exécute tous les tests"""
    print("\n" + "="*60)
    print("  TESTS MODULE RELIABILITY")
    print("="*60 + "\n")
    
    try:
        test_systematic_backup()
        print()
        test_random_backup()
        print()
        test_reliable_server()
        print()
        test_backup_comparison()
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
