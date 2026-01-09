#!/usr/bin/env python3
"""
Script de test global - exécute tous les tests
"""

import sys
import subprocess
from pathlib import Path


def run_test_file(test_file: str) -> bool:
    """
    Exécute un fichier de test
    
    Args:
        test_file: Chemin vers le fichier de test
        
    Returns:
        True si les tests réussissent
    """
    try:
        result = subprocess.run(
            [sys.executable, test_file],
            cwd=Path(__file__).parent.parent,
            capture_output=False,
            check=True
        )
        return result.returncode == 0
    except subprocess.CalledProcessError:
        return False


def main():
    """Exécute tous les tests"""
    print("\n" + "="*60)
    print("  EXÉCUTION DE TOUS LES TESTS")
    print("="*60 + "\n")
    
    tests_dir = Path(__file__).parent
    test_files = [
        "test_core.py",
        "test_capacity.py",
        "test_reliability.py",
        "test_regulation.py"
    ]
    
    results = {}
    
    for test_file in test_files:
        test_path = tests_dir / test_file
        if test_path.exists():
            print(f"Exécution de {test_file}...")
            success = run_test_file(str(test_path))
            results[test_file] = success
            
            if not success:
                print(f"✗ {test_file} a échoué\n")
        else:
            print(f"⚠ {test_file} introuvable\n")
            results[test_file] = False
    
    # Résumé
    print("\n" + "="*60)
    print("  RÉSUMÉ DES TESTS")
    print("="*60 + "\n")
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    
    for test_file, success in results.items():
        status = "✓ RÉUSSI" if success else "✗ ÉCHOUÉ"
        print(f"  {test_file:25s} {status}")
    
    print(f"\n  Total: {passed}/{total} tests réussis")
    print("="*60 + "\n")
    
    return all(results.values())


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
