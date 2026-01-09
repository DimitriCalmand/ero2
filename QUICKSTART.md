# Guide de Démarrage Rapide

## Installation Express

```bash
# 1. Activer l'environnement virtuel
source .venv/bin/activate

# 2. Installer les dépendances
pip install -r requirements.txt

# 3. Tester l'installation
python tests/run_all_tests.py
```

## Exemples d'Utilisation

### 1. Simulation Basique (5 minutes)
```bash
python main.py --scenario basic --duration 1000
```

### 2. Analyse des Capacités
```bash
python main.py --scenario waterfall --duration 1000
```

### 3. Comparaison des Backups
```bash
python main.py --scenario backup --duration 1000
```

### 4. Populations Multiples (ING/PREPA)
```bash
python main.py --scenario channels --duration 1000
```

### 5. Avec Visualisations
```bash
python main.py --scenario basic --visualize --output-dir my_results/
```

## Structure des Résultats

Quand vous utilisez `--visualize`, les fichiers suivants sont générés :

- `arrivals.png` : Graphique des arrivées cumulées
- `queue_length.png` : Évolution de la longueur de file
- `waiting_time.png` : Distribution des temps d'attente
- `response_time_by_type.png` : Temps de réponse par type
- `summary.txt` : Rapport textuel complet

## Tests Rapides

### Tester un module spécifique
```bash
python tests/test_core.py          # Module Core
python tests/test_capacity.py      # Module Capacity
python tests/test_reliability.py   # Module Reliability
python tests/test_regulation.py    # Module Regulation
```

### Tous les tests
```bash
python tests/run_all_tests.py
```

## Paramètres Importants

- `--scenario` : basic, waterfall, backup, channels, real
- `--duration` : Durée de simulation (défaut: 1000)
- `--seed` : Graine aléatoire pour reproductibilité (défaut: 42)
- `--visualize` : Active la génération de graphiques
- `--output-dir` : Dossier pour les résultats (défaut: results/)

## Utilisation Programmatique

```python
from src.core import SimulationEngine, Server, JobGenerator
from src.analysis import PerformanceAnalyzer, Visualizer
import random

# Configuration
engine = SimulationEngine(random_seed=42)

# Création du serveur
server = Server(
    env=engine.env,
    server_id="my_server",
    num_servers=3,
    logger=engine.logger
)

# Générateur de jobs
generator = JobGenerator(
    env=engine.env,
    logger=engine.logger,
    arrival_rate=2.0,
    job_type="ING"
)

# Lancement
def service_time():
    return random.expovariate(3.0)

engine.env.process(generator.generate(server, service_time, 1000.0))
engine.run(1000.0)

# Analyse
df = engine.get_results()
analyzer = PerformanceAnalyzer(df)
summary = analyzer.get_summary(num_servers=3)

print(f"Débit: {summary['throughput']:.4f}")
print(f"Utilisation: {summary['utilization']:.2%}")
```

## Données Réelles

Pour utiliser vos propres données :

```bash
python main.py --scenario real --tags-file path/to/tags --duration 1000
```

Le fichier doit être au format CSV avec :
- `assignmentUri` : Nom de l'assignment
- `receivedAt` : Timestamp ISO 8601

## Troubleshooting

### Problème : ModuleNotFoundError
```bash
# Vérifier l'environnement virtuel
source .venv/bin/activate
pip install -r requirements.txt
```

### Problème : Tests échouent
```bash
# Réinstaller les dépendances
pip install --upgrade -r requirements.txt
```

### Problème : Visualisations ne s'affichent pas
```bash
# Vérifier matplotlib
pip install --upgrade matplotlib
```

## Performance

Pour des simulations longues :
- Commencer avec `--duration 1000` pour tester
- Augmenter progressivement (5000, 10000, etc.)
- Utiliser `--seed` pour reproductibilité
- Monitorer l'utilisation mémoire pour très longues simulations

## Métriques Clés

- **Débit** : Jobs complétés / temps
- **Utilisation** : % temps serveurs occupés
- **Temps d'attente** : Temps dans la file
- **Temps de réponse** : Temps total (attente + service)
- **Taux de rejet** : % de jobs rejetés

## Prochaines Étapes

1. Exécuter les scénarios de base
2. Ajuster les paramètres (λ, μ, c)
3. Comparer différentes configurations
4. Analyser avec les données réelles
5. Générer un rapport complet
