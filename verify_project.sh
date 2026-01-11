#!/bin/bash
# Script de vérification complète du projet

echo "=========================================="
echo "  VÉRIFICATION DU PROJET ERO2"
echo "=========================================="
echo ""

# Activation de l'environnement virtuel
echo "1. Activation de l'environnement virtuel..."
source .venv/bin/activate

# Vérification des dépendances
echo "2. Vérification des dépendances..."
pip list | grep -E "(simpy|pandas|numpy|scipy|matplotlib|seaborn)" && echo "   ✓ Dépendances installées" || echo "   ✗ Erreur dépendances"
echo ""

# Tests unitaires
echo "3. Exécution des tests unitaires..."
python tests/run_all_tests.py
TEST_RESULT=$?
echo ""

# Test des imports
echo "4. Vérification des imports..."
python -c "
from src.core import SimulationEngine
from src.capacity import WaterfallScenario
from src.reliability import BackupComparison
from src.regulation import ChannelsScenario
from src.analysis import PerformanceAnalyzer
print('   ✓ Tous les imports fonctionnent')
" || echo "   ✗ Erreur d'import"
echo ""

# Test rapide de simulation
echo "5. Test de simulation rapide..."
python main.py --scenario basic --duration 100 --seed 42 > /tmp/test_sim.txt 2>&1
if [ $? -eq 0 ]; then
    echo "   ✓ Simulation fonctionnelle"
    grep "Débit:" /tmp/test_sim.txt
else
    echo "   ✗ Erreur de simulation"
fi
echo ""

# Statistiques du projet
echo "6. Statistiques du projet..."
echo "   Fichiers Python: $(find src tests -name "*.py" | wc -l)"
echo "   Lignes de code: $(find src tests main.py -name "*.py" -exec wc -l {} + | tail -1 | awk '{print $1}')"
echo "   Modules: 5 (Core, Capacity, Reliability, Regulation, Analysis)"
echo ""

# Résumé
echo "=========================================="
if [ $TEST_RESULT -eq 0 ]; then
    echo "  ✓ PROJET VALIDÉ - TOUS LES TESTS PASSENT"
else
    echo "  ✗ ATTENTION - CERTAINS TESTS ÉCHOUENT"
fi
echo "=========================================="
