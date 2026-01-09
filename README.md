# Simulateur de Moulinette - Projet ERO2

## Description

Simulation à Événements Discrets de l'infrastructure de la moulinette EPITA. Ce projet modélise le parcours des soumissions (git push) dans un réseau de files d'attente pour identifier les points de rupture et optimiser les performances.

## Structure du Projet

```
ero2/
├── src/
│   ├── core/              # Moteur de simulation (Étudiant 1)
│   │   └── simulation_engine.py
│   ├── capacity/          # Gestion des capacités (Étudiant 2)
│   │   └── limited_queue.py
│   ├── reliability/       # Stratégies de backup (Étudiant 3)
│   │   └── backup_strategies.py
│   ├── regulation/        # Régulation et hétérogénéité (Étudiant 4)
│   │   └── heterogeneous_queues.py
│   └── analysis/          # Analyse statistique (Étudiant 5)
│       └── statistics.py
├── tests/                 # Tests unitaires
│   ├── test_core.py
│   ├── test_capacity.py
│   ├── test_reliability.py
│   ├── test_regulation.py
│   └── run_all_tests.py
├── main.py               # Script principal
├── requirements.txt      # Dépendances
└── tags                  # Données réelles
```

## Installation

### 1. Activer l'environnement virtuel

```bash
source .venv/bin/activate
```

### 2. Installer les dépendances

```bash
pip install -r requirements.txt
```

## Utilisation

### Scénarios Disponibles

#### 1. Scénario Basique (M/M/c)
```bash
python main.py --scenario basic --duration 1000
```

#### 2. Scénario Waterfall (Files Finies)
```bash
python main.py --scenario waterfall --duration 1000
```

#### 3. Scénario Backup (Stratégies de Sauvegarde)
```bash
python main.py --scenario backup --duration 1000
```

#### 4. Scénario Channels (Populations Hétérogènes)
```bash
python main.py --scenario channels --duration 1000
```

#### 5. Scénario basé sur Données Réelles
```bash
python main.py --scenario real --tags-file tags --duration 1000
```

### Options Avancées

```bash
# Avec visualisations
python main.py --scenario basic --visualize --output-dir results/

# Avec graine spécifique pour reproductibilité
python main.py --scenario waterfall --seed 123

# Durée personnalisée
python main.py --scenario channels --duration 5000
```

## Tests

### Exécuter tous les tests
```bash
python tests/run_all_tests.py
```

### Exécuter un test spécifique
```bash
python tests/test_core.py
python tests/test_capacity.py
python tests/test_reliability.py
python tests/test_regulation.py
```

## Modules

### Module Core (Étudiant 1)
- Moteur de simulation SimPy
- Classes de base (Job, Server, JobGenerator)
- Système de logging centralisé
- Gestion du temps simulé

### Module Capacity (Étudiant 2)
- Files d'attente finies (capacités ks et kf)
- Loss System vs Queueing System
- Analyse des taux de rejet
- Scénario Waterfall complet

### Module Reliability (Étudiant 3)
- Stratégies de backup (Systématique, Aléatoire, Conditionnel)
- Délais de sauvegarde
- Gestion des pannes et récupération
- Analyse d'impact sur le débit

### Module Regulation (Étudiant 4)
- Gestion multi-populations (ING/PREPA)
- Gating (barrage temporel)
- Files prioritaires (FIFO, SJF, Priority)
- Scénario Channels complet

### Module Analysis (Étudiant 5)
- Calcul des intervalles de confiance
- Détection de période de chauffe (Warm-up)
- Métriques de performance (débit, utilisation, temps d'attente)
- Visualisations (matplotlib/seaborn)
- Comparaison avec données réelles

## Métriques Calculées

- **Débit** : Jobs complétés par unité de temps
- **Taux d'utilisation** : Occupation des serveurs
- **Taux de rejet** : Proportion de jobs rejetés
- **Temps d'attente** : Moyenne, médiane, P95, P99
- **Temps de réponse** : Distribution complète
- **Disponibilité** : MTBF, MTTR

## Visualisations Générées

Avec l'option `--visualize`, le simulateur génère :
- Arrivées cumulées au cours du temps
- Évolution de la longueur de file
- Distribution des temps d'attente
- Temps de réponse par type de job
- Rapport textuel complet

## Exemples d'Utilisation

### Analyse de Capacité
```python
from src.capacity import WaterfallScenario
from src.core import SimulationEngine

engine = SimulationEngine(random_seed=42)
scenario = WaterfallScenario(
    env=engine.env,
    logger=engine.logger,
    num_servers=3,
    max_queue_size=10
)

results = scenario.run_comparison(
    arrival_rate=2.5,
    service_rate=3.0,
    duration=1000.0
)
```

### Comparaison de Stratégies de Backup
```python
from src.reliability import BackupComparison, SystematicBackup, RandomBackup
from src.core import SimulationEngine
import random

engine = SimulationEngine(random_seed=42)
comparison = BackupComparison(env=engine.env, logger=engine.logger)

comparison.add_server(
    "systematic",
    num_servers=2,
    backup_strategy=SystematicBackup(),
    backup_time_generator=lambda: random.expovariate(5.0)
)

comparison.add_server(
    "random_50",
    num_servers=2,
    backup_strategy=RandomBackup(0.5),
    backup_time_generator=lambda: random.expovariate(5.0)
)

results = comparison.run_comparison(
    arrival_rate=2.0,
    service_rate=3.0,
    duration=1000.0
)
```

### Analyse Multi-Population
```python
from src.regulation import ChannelsScenario
from src.core import SimulationEngine

engine = SimulationEngine(random_seed=42)
scenario = ChannelsScenario(
    env=engine.env,
    logger=engine.logger,
    num_servers=3,
    scheduling_policy="SJF"  # ou "FIFO", "PRIORITY"
)

scenario.add_population("ING", arrival_rate=1.5, service_rate=2.5)
scenario.add_population("PREPA", arrival_rate=0.5, service_rate=2.0)

results = scenario.run(duration=1000.0)
```

## Données Réelles

Le fichier `tags` contient l'historique réel des soumissions avec :
- `assignmentUri` : Nom de l'assignment
- `receivedAt` : Timestamp de réception (ISO 8601)

Le module d'analyse peut extraire :
- Taux d'arrivée λ
- Distributions des temps inter-arrivées
- Patterns temporels

## Formules Théoriques

### File M/M/c
- Taux d'utilisation : ρ = λ/(cμ)
- Nombre moyen dans le système : L (formule d'Erlang C)
- Temps moyen dans le système : W = L/λ (Little's Law)

### Loss System (Erlang B)
- Probabilité de blocage : B(c, a) avec a = λ/μ

### Intervalles de Confiance
- IC à 95% : μ ± t₀.₉₇₅ × (σ/√n)

## Recommandations

Pour des résultats fiables :
1. Utiliser une période de chauffe (warm-up) appropriée
2. Exécuter plusieurs réplications avec différentes graines
3. Calculer les intervalles de confiance
4. Comparer avec les données réelles
5. Tester différents dimensionnements (ks, kf)

## Auteurs

Projet ERO2 - EPITA
Groupe de 5 étudiants

## Licence

Projet académique - EPITA
