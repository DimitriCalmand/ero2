# 📚 GUIDE COMPLET - Simulateur Moulinette ERO2

**Version:** 2.0  
**Date:** 11 janvier 2026  
**Statut:** Production Ready ✅

---

## 📋 TABLE DES MATIÈRES

1. [À Propos du Projet](#about)
2. [Installation Rapide](#installation)
3. [Utilisation](#usage)
4. [Architecture](#architecture)
5. [Scénarios Disponibles](#scenarios)
6. [Métriques et Analyses](#metrics)
7. [Tests](#tests)
8. [Documentation Avancée](#advanced)

---

<a name="about"></a>
## 🎯 À PROPOS DU PROJET

### Objectif
Modéliser l'infrastructure de la moulinette EPITA comme un réseau de files d'attente à événements discrets (Discrete Event Simulation) pour :
- Identifier les points de rupture du système
- Optimiser le dimensionnement (nombre de serveurs, tailles de files)
- Analyser l'impact des stratégies de régulation
- Proposer des configurations optimales

### Contexte Académique
**Cours:** ERO2 (Évaluation et Recherche Opérationnelle 2)  
**École:** EPITA - ING3  
**Sujet:** Analyse de l'infrastructure de correction automatique (moulinette)

### Workflow Simulé
```
Étudiant → git push tag → Vérification → File d'attente → Exécution test-suite → Résultat
                              ↓              ↓              ↓
                         Rejets      Temps d'attente   Feedback loop
```

### Technologies
- **SimPy 4.1.1** - Simulation à événements discrets
- **Pandas 2.3.3** - Manipulation et analyse de données
- **NumPy 2.2.6** - Calculs numériques
- **Matplotlib 3.10.8** - Visualisations
- **Seaborn 0.13.2** - Graphiques avancés
- **SciPy 1.15.3** - Statistiques et optimisation

---

<a name="installation"></a>
## ⚡ INSTALLATION RAPIDE

### Prérequis
- Python 3.10+
- pip
- virtualenv (recommandé)

### Installation (30 secondes)

```bash
# 1. Activer l'environnement virtuel
source .venv/bin/activate

# 2. Installer les dépendances
pip install -r requirements.txt

# 3. Vérifier l'installation
python tests/run_all_tests.py
```

**Résultat attendu:** `✓ ALL TESTS PASSED (100%)`

---

<a name="usage"></a>
## 🚀 UTILISATION

### Commande de Base

```bash
python main.py --scenario <nom> --duration <temps> [options]
```

### Options Disponibles

| Option | Description | Valeur par défaut |
|--------|-------------|-------------------|
| `--scenario` | Nom du scénario à exécuter | `basic` |
| `--duration` | Durée de simulation (unités de temps) | `1000` |
| `--seed` | Graine aléatoire pour reproductibilité | `42` |
| `--visualize` | Générer des visualisations | `False` |
| `--output-dir` | Répertoire de sortie | `./output/` |
| `--tags-file` | Fichier de données réelles | `tags` |
| `--use-replay` | Rejouer timestamps réels | `False` |

### Exemples Rapides

#### Simulation basique (5 min)
```bash
python main.py --scenario basic --duration 1000
```

#### Avec visualisations
```bash
python main.py --scenario channels --duration 1000 --visualize
```

#### Analyse complète
```bash
python main.py --scenario gating-analysis --duration 5000 --visualize --output-dir results/
```

---

<a name="architecture"></a>
## 🏗️ ARCHITECTURE

### Structure Modulaire

```
ero2/
├── src/                           # Code source
│   ├── core/                      # Module 1: Moteur de simulation
│   │   ├── __init__.py
│   │   └── simulation_engine.py   (SimulationEngine, JobGenerator, etc.)
│   │
│   ├── capacity/                  # Module 2: Gestion des capacités
│   │   ├── __init__.py
│   │   └── limited_queue.py       (LimitedQueue, WaterfallScenario)
│   │
│   ├── reliability/               # Module 3: Fiabilité et backup
│   │   ├── __init__.py
│   │   └── backup_strategies.py   (BackupManager, strategies)
│   │
│   ├── regulation/                # Module 4: Régulation
│   │   ├── __init__.py
│   │   ├── population.py          (PopulationGenerator)
│   │   ├── priority_queue.py      (PriorityQueue, policies)
│   │   ├── gating.py              (GatingController)
│   │   ├── server.py              (HeterogeneousServer)
│   │   ├── scenario.py            (ChannelsScenario)
│   │   └── gating_analysis.py     (GatingAnalyzer) ✨
│   │
│   └── analysis/                  # Module 5: Analyse statistique
│       ├── __init__.py
│       ├── statistics.py          (Statistiques, PopulationAnalyzer) ✨
│       └── dashboard.py           (Visualisations)
│
├── tests/                         # Tests unitaires
│   ├── test_core.py              (4 tests)
│   ├── test_capacity.py          (3 tests)
│   ├── test_reliability.py       (4 tests)
│   ├── test_regulation.py        (6 tests) ✨
│   └── run_all_tests.py
│
├── main.py                        # Script principal (8 scénarios)
├── requirements.txt               # Dépendances Python
├── tags                           # Données réelles (159K lignes)
│
├── README.md                      # Documentation principale
├── GUIDE_COMPLET.md              # Ce fichier ✨
├── CHANNELS_RECOMMENDATIONS.md    # Guide de décision Channels & Dams
└── IMPLEMENTATION_COMPLETE.md     # Rapport d'implémentation final
```

### Statistiques du Code

| Module | Fichiers | Lignes | Description |
|--------|----------|--------|-------------|
| **Core** | 1 | 420 | Moteur SimPy, générateurs |
| **Capacity** | 1 | 360 | Files limitées, waterfall |
| **Reliability** | 1 | 410 | Backup, cold/warm standby |
| **Regulation** | 7 | 1200+ | Populations, gating, priorités |
| **Analysis** | 2 | 800+ | Statistiques, visualisations |
| **Tests** | 5 | 450 | 17 tests (100% succès) |
| **Main** | 1 | 450+ | 8 scénarios orchestrés |
| **TOTAL** | 18 | **4090+** | Production-ready |

---

<a name="scenarios"></a>
## 🎬 SCÉNARIOS DISPONIBLES

### 1. **Basic** - M/M/c Standard
**Commande:** `python main.py --scenario basic --duration 1000`

**Description:** Simulation d'un système M/M/c classique avec:
- Arrivées poissonniennes (λ = 3.0 jobs/s)
- Service exponentiel (μ = 2.5 jobs/s)
- c serveurs en parallèle

**Métriques:**
- Temps moyen d'attente
- Temps moyen de réponse
- Utilisation des serveurs
- Longueur moyenne de file

**Use case:** Comprendre les bases, valider le moteur de simulation

---

### 2. **Waterfall** - Files en Cascade
**Commande:** `python main.py --scenario waterfall --duration 1000`

**Description:** Modélise le flux à deux étapes:
1. **File d'exécution** (ks capacité, μ_exec)
2. **File de feedback** (kf capacité, μ_feedback)

**Caractéristiques:**
- Files d'attente finies (rejets possibles)
- Chaînage automatique entre étapes
- Probabilité de retour (feedback loop)

**Métriques:**
- Taux de rejet en cascade
- Temps de séjour moyen end-to-end
- Taux de complétion total

**Use case:** Dimensionnement capacités, analyse rejets

---

### 3. **Backup** - Stratégies de Fiabilité
**Commande:** `python main.py --scenario backup --duration 1000`

**Description:** Compare 3 stratégies de redondance:
- **Cold Standby**: Serveur de secours inactif (activation lente)
- **Warm Standby**: Serveur de secours en veille (activation rapide)
- **Hot Standby**: Serveurs actifs en parallèle (répartition de charge)

**Métriques:**
- Disponibilité système
- Temps moyen de réponse par stratégie
- Impact des pannes
- Overhead de redondance

**Use case:** Choix stratégie backup, analyse coût/fiabilité

---

### 4. **Channels** - Populations Hétérogènes
**Commande:** `python main.py --scenario channels --duration 1000`

**Description:** Simulation avec 2 populations distinctes:
- **ING**: arrivées fréquentes (λ=1.5), traitement rapide (μ=2.5)
- **PREPA**: arrivées rares (λ=0.5), traitement long (μ=2.0)

**Politiques d'ordonnancement:**
- **FIFO**: First In First Out (fairness)
- **SJF**: Shortest Job First (performance)
- **PRIORITY**: Priorité ING > PREPA (SLA différenciés)

**Métriques:**
- Temps de réponse par population
- Fairness Index (Jain)
- Percentiles P50/P95/P99
- SLA compliance

**Use case:** Analyse fairness, choix politique ordonnancement

---

### 5. **Gating** - Barrage Temporel
**Commande:** `python main.py --scenario gating --duration 1000`

**Description:** Mécanisme de régulation temporelle:
- **Fermeture**: tb unités (blocage arrivées)
- **Ouverture**: ratio × tb unités (acceptation)
- Cycle répétitif

**Configurations:**
```python
tb = 100          # Durée de fermeture
ratio = 0.5       # tb × 0.5 = 50 unités d'ouverture
```

**Métriques:**
- Impact sur temps d'attente (+% par population)
- Débit système (jobs/s)
- Variation temporelle

**Use case:** Maintenance programmée, pics de charge

---

### 6. **Optimization** - Recherche Paramètres Optimaux
**Commande:** `python main.py --scenario optimization --duration 5000`

**Description:** Optimisation automatique des capacités:
- Balayage de (ks, kf) dans [10, 100]
- Objectifs: minimiser rejets, temps de réponse
- Génération de heatmaps

**Algorithme:**
1. Test exhaustif de configurations
2. Calcul métriques pour chaque (ks, kf)
3. Recherche front de Pareto
4. Recommandation configuration optimale

**Sorties:**
- `optimization_results.csv`
- `rejection_rate_heatmap.png`
- `response_time_heatmap.png`
- Recommandation texte

**Use case:** Dimensionnement optimal, analyse coût/performance

---

### 7. **Advanced** - Métriques Avancées
**Commande:** `python main.py --scenario advanced --duration 1000`

**Description:** Validation théorique et métriques poussées:
- **Loi de Little**: L = λ × W
- **Comparaison M/M/c**: vs formules théoriques
- **Analyse stabilité**: ρ = λ / (c × μ)

**Vérifications:**
```
✓ Little Law: |L - λW| / L < 5%
✓ M/M/c Match: |W_sim - W_theory| / W_theory < 10%
✓ Stabilité: ρ < 1.0
```

**Sorties:**
- Rapport de vérification complet
- Écarts relatifs
- Diagnostics de stabilité

**Use case:** Validation modèle, debug, analyse théorique

---

### 8. **Gating-Analysis** - Analyse Approfondie Gating ✨
**Commande:** `python main.py --scenario gating-analysis --duration 5000`

**Description:** Analyse exhaustive du gating avec:
- Test de 16+ configurations (tb × ratio)
- Génération de visualisations avancées
- Recommandation automatique
- Analyse fairness et SLA

**Configurations testées:**
```python
tb_values = [50, 100, 150, 200]       # 4 durées de blocage
ratio_values = [0.25, 0.33, 0.5, 0.75] # 4 ratios ouverture
# → 16 combinaisons
```

**Visualisations générées:**
1. **Heatmaps** (4 graphiques):
   - Temps de réponse ING (ms)
   - Temps de réponse PREPA (ms)
   - Longueur max de file
   - Débit système (jobs/s)

2. **Courbes d'évolution** (4 graphiques):
   - Impact par ratio pour chaque tb

**Analyses:**
- **Fairness Index** (Jain): 0-1 (1 = parfait)
- **Percentiles**: P50, P95, P99 par population
- **SLA Compliance**: % jobs dans SLA
- **Patterns temporels**: stabilité dans le temps

**Sorties:**
```
gating_analysis/
├── gating_impact_heatmaps.png     # 4 heatmaps
├── gating_impact_curves.png       # 4 courbes
├── analysis_report.txt            # Rapport gating
└── population_analysis_report.txt # Rapport populations
```

**Recommandation automatique:**
```
Configuration Optimale Recommandée:
tb = 100, ratio = 0.5
→ ING: +25% temps, PREPA: +45% temps
→ Fairness: 0.95 (Excellent)
→ SLA Compliance: 98%
```

**Use case:** 
- Choix configuration gating optimale
- Analyse impact multi-objectifs
- Validation fairness inter-populations

---

<a name="metrics"></a>
## 📊 MÉTRIQUES ET ANALYSES

### Métriques de Base

| Métrique | Description | Formule |
|----------|-------------|---------|
| **λ** (lambda) | Taux d'arrivée | jobs/s |
| **μ** (mu) | Taux de service | jobs/s |
| **ρ** (rho) | Utilisation | λ / (c × μ) |
| **W** | Temps d'attente moyen | ∑ wait_time / n_jobs |
| **R** | Temps de réponse moyen | ∑ response_time / n_jobs |
| **L** | Longueur moyenne file | ∑ queue_length / n_samples |
| **P_reject** | Taux de rejet | rejets / arrivées |

### Métriques Avancées

#### 1. Loi de Little
```
L = λ × W
```
**Interprétation:**
- Relation fondamentale en théorie des files
- Valide pour systèmes stables
- Permet vérification simulation

**Validation:** `|L - λW| / L < 5%`

#### 2. Jain's Fairness Index
```
J = (∑ xi)² / (n × ∑ xi²)
```
où `xi` = temps de réponse moyen population i

**Interprétation:**
- J = 1.0 → parfaitement équitable
- J ≥ 0.95 → Excellent ⭐⭐⭐
- J ∈ [0.85, 0.95] → Bon ⭐⭐
- J ∈ [0.70, 0.85] → Fair ⭐
- J < 0.70 → Unfair ⚠️

#### 3. Response Time Ratio
```
Ratio = max(R_i) / min(R_i)
```

**Interprétation:**
- Ratio < 1.5x → Excellent
- Ratio ∈ [1.5x, 2.0x] → Bon
- Ratio ∈ [2.0x, 3.0x] → Acceptable
- Ratio > 3.0x → Problématique ⚠️

#### 4. SLA Compliance
```
Compliance = (jobs within SLA) / (total jobs) × 100%
```

**Thresholds typiques:**
- ING: SLA ≤ 1.0s
- PREPA: SLA ≤ 2.0s

**Interprétation:**
- ≥95% → Compliant ✅
- <95% → Non-compliant ❌

#### 5. Percentiles
- **P50 (médiane)**: 50% jobs plus rapides
- **P95**: 95% jobs plus rapides (tail latency)
- **P99**: 99% jobs plus rapides (worst case)

**Use case:** Détecter outliers, garantir SLA

### Utilisation Programmatique

#### Métriques Basiques
```python
from src.analysis import BasicStatistics

# Après simulation
df = engine.logger.get_dataframe()
stats = BasicStatistics(df)

print(f"Temps moyen d'attente: {stats.mean_waiting_time():.4f}s")
print(f"Temps moyen de réponse: {stats.mean_response_time():.4f}s")
print(f"Utilisation: {stats.server_utilization():.2%}")
```

#### Fairness et Populations
```python
from src.analysis import PopulationAnalyzer

analyzer = PopulationAnalyzer(df)

# Fairness
fairness = analyzer.calculate_fairness_index()
print(f"Fairness Index: {fairness['fairness_index']:.4f}")
print(f"Interprétation: {fairness['interpretation']}")

# Percentiles
percentiles = analyzer.calculate_percentiles_by_type()
for pop, metrics in percentiles.items():
    print(f"{pop} - P95: {metrics['response_time']['p95']:.4f}s")

# SLA
compliance = analyzer.calculate_sla_compliance({
    "ING": 1.0,
    "PREPA": 2.0
})
for pop, result in compliance.items():
    print(f"{pop} Compliance: {result['compliance_percentage']:.2f}%")
```

#### Gating Analysis
```python
from src.regulation import GatingAnalyzer

analyzer = GatingAnalyzer(
    lambda_ing=1.5, mu_ing=2.5,
    lambda_prepa=0.5, mu_prepa=2.0,
    num_servers=2
)

# Test multi-configs
results = analyzer.analyze_gating_variations(
    tb_values=[50, 100, 150, 200],
    ratio_values=[0.25, 0.5, 0.75],
    duration=5000
)

# Visualisations
analyzer.plot_gating_impact(results)

# Recommandation
recommendation = analyzer.recommend_gating_config(
    results, 
    max_time_increase_pct=50.0
)
print(f"Optimal: tb={recommendation['tb']}, ratio={recommendation['ratio']}")
```

---

<a name="tests"></a>
## 🧪 TESTS

### Suite de Tests Complète

| Module | Fichier | Tests | Statut |
|--------|---------|-------|--------|
| Core | test_core.py | 4 | ✅ 100% |
| Capacity | test_capacity.py | 3 | ✅ 100% |
| Reliability | test_reliability.py | 4 | ✅ 100% |
| Regulation | test_regulation.py | 6 | ✅ 100% |
| **TOTAL** | | **17** | ✅ **100%** |

### Exécution

#### Tous les tests
```bash
python tests/run_all_tests.py
```

**Résultat:**
```
✓ test_core: 4/4 tests passed
✓ test_capacity: 3/3 tests passed
✓ test_reliability: 4/4 tests passed
✓ test_regulation: 6/6 tests passed

✓ TOUS LES TESTS RÉUSSIS (17/17)
```

#### Test individuel
```bash
python -m pytest tests/test_regulation.py -v
```

### Couverture des Tests

#### test_core.py
- `test_basic_simulation()` - Simulation M/M/c de base
- `test_job_generation()` - Générateur de jobs
- `test_server_processing()` - Traitement par serveur
- `test_logging()` - Système de logging

#### test_capacity.py
- `test_limited_queue()` - File d'attente finie
- `test_waterfall_scenario()` - Cascade à deux étages
- `test_rejection_rates()` - Calcul taux de rejet

#### test_reliability.py
- `test_cold_standby()` - Backup froid
- `test_warm_standby()` - Backup tiède
- `test_hot_standby()` - Backup chaud
- `test_failure_recovery()` - Récupération après panne

#### test_regulation.py
- `test_fifo_policy()` - Politique FIFO
- `test_sjf_policy()` - Politique SJF
- `test_priority_policy()` - Politique PRIORITY
- `test_gating_controller()` - Contrôleur gating
- `test_population_analyzer()` - Analyse populations ✨
- `test_gating_analyzer()` - Analyse gating multi-configs ✨

---

<a name="advanced"></a>
## 📖 DOCUMENTATION AVANCÉE

### Fichiers de Documentation

| Fichier | Contenu | Audience |
|---------|---------|----------|
| **README.md** | Documentation principale, quick start | Tous |
| **GUIDE_COMPLET.md** | Guide exhaustif (ce fichier) | Développeurs |
| **CHANNELS_RECOMMENDATIONS.md** | Guide de décision Channels & Dams | Analystes |
| **IMPLEMENTATION_COMPLETE.md** | Rapport d'implémentation final | Tech leads |

### Guides Spécialisés

#### 1. CHANNELS_RECOMMENDATIONS.md
**Contenu:** (687 lignes)
- Choix politique d'ordonnancement (FIFO/SJF/PRIORITY)
- Configuration gating par cas d'usage
- Optimisation multi-objectifs
- 5 use cases complets avec code
- Arbre de décision
- Checklist de production

**Quand l'utiliser:**
- Besoin de choisir entre FIFO/SJF/PRIORITY
- Configuration de gating pour maintenance
- Optimisation fairness vs performance
- Mise en production

#### 2. IMPLEMENTATION_COMPLETE.md
**Contenu:** (rapport technique)
- Détails d'implémentation des 3 recommandations
- Statistiques du code (1808 lignes ajoutées)
- Résultats de tests complets
- Impact et bénéfices

**Quand l'utiliser:**
- Revue technique du code
- Comprendre les choix d'architecture
- Validation de l'implémentation

### Ressources Théoriques

#### Théorie des Files d'Attente
- **Notation de Kendall**: A/S/c/K/N/D
  - A = distribution arrivées (M=Markov, D=Déterministe)
  - S = distribution service
  - c = nombre de serveurs
  - K = capacité file (∞ par défaut)
  - N = population source (∞ par défaut)
  - D = discipline (FIFO par défaut)

- **Formules M/M/c**:
  ```
  ρ = λ / (c × μ)          [utilisation]
  W = E[temps d'attente]
  R = W + 1/μ              [temps de réponse]
  L = λ × W                [loi de Little]
  ```

#### SimPy - Event Driven Simulation
- **Process**: générateurs Python (yield)
- **Environment**: horloge globale, ordonnanceur
- **Resource**: serveurs, files d'attente
- **Store**: stockage FIFO/LIFO
- **Container**: ressources continues

**Documentation:** https://simpy.readthedocs.io/

### Support et Contact

**Questions techniques:**
- Consulter les docstrings dans le code
- Lire les tests unitaires (exemples d'usage)
- Vérifier CHANNELS_RECOMMENDATIONS.md pour décisions

**Bugs ou suggestions:**
- Créer une issue dans le repo
- Fournir contexte, commande, traceback
- Inclure version Python et dépendances

---

## 🎓 EXEMPLES D'UTILISATION AVANCÉE

### 1. Optimisation Multi-Objectifs

**Objectif:** Trouver configuration minimisant temps de réponse ET maximisant fairness

```python
from src.regulation import GatingAnalyzer
from src.analysis import PopulationAnalyzer

# Configuration
analyzer = GatingAnalyzer(
    lambda_ing=1.5, mu_ing=2.5,
    lambda_prepa=0.5, mu_prepa=2.0,
    num_servers=2
)

# Test exhaustif
results = analyzer.analyze_gating_variations(
    tb_values=[50, 100, 150, 200],
    ratio_values=[0.25, 0.33, 0.5, 0.75],
    duration=5000
)

# Filtrer par contraintes
feasible = results[
    (results['ing_avg_time'] < 1.0) &           # SLA ING
    (results['prepa_avg_time'] < 2.0) &         # SLA PREPA
    (results['fairness_index'] >= 0.95)         # Fairness excellent
]

# Meilleure config
if not feasible.empty:
    best = feasible.loc[feasible['total_avg_time'].idxmin()]
    print(f"Optimal: tb={best['tb']}, ratio={best['ratio']}")
else:
    print("Aucune configuration ne satisfait les contraintes")
```

### 2. Replay de Données Réelles

**Objectif:** Simuler avec timestamps exacts du fichier `tags`

```python
from src.core import SimulationEngine
from src.capacity import LimitedQueue

# Charger données réelles
import pandas as pd
tags_df = pd.read_csv('tags', header=None, names=['timestamp'])
tags_df['timestamp'] = pd.to_datetime(tags_df['timestamp'])

# Extraire inter-arrival times
tags_df = tags_df.sort_values('timestamp')
tags_df['interarrival'] = tags_df['timestamp'].diff().dt.total_seconds()

# Simulation avec replay
env = simpy.Environment()
queue = LimitedQueue(env, capacity=50, num_servers=3, service_rate=2.5)

def replayer():
    for delta in tags_df['interarrival'].dropna():
        yield env.timeout(delta)
        queue.arrival_process()

env.process(replayer())
env.run()

# Analyse
stats = queue.get_statistics()
print(f"Taux de rejet réel: {stats['rejection_rate']:.2%}")
```

### 3. Analyse de Sensibilité

**Objectif:** Évaluer impact de λ sur temps de réponse

```python
import numpy as np
import matplotlib.pyplot as plt

lambdas = np.linspace(0.5, 2.5, 20)
response_times = []

for lam in lambdas:
    env = simpy.Environment()
    scenario = BasicScenario(
        env, 
        arrival_rate=lam, 
        service_rate=2.5, 
        num_servers=2
    )
    env.run(until=5000)
    
    stats = scenario.get_statistics()
    response_times.append(stats['mean_response_time'])

# Visualisation
plt.figure(figsize=(10, 6))
plt.plot(lambdas, response_times, marker='o')
plt.axhline(y=1.0, color='r', linestyle='--', label='SLA Threshold')
plt.xlabel('Taux d\'arrivée λ (jobs/s)')
plt.ylabel('Temps de réponse moyen (s)')
plt.title('Analyse de Sensibilité: Impact de λ')
plt.legend()
plt.grid(True)
plt.savefig('sensitivity_analysis.png')
```

---

## 🏆 CONCLUSION

### Réalisations
✅ 5 modules complets (4090+ lignes)  
✅ 8 scénarios fonctionnels  
✅ 17 tests unitaires (100% succès)  
✅ Métriques avancées (Fairness, SLA, Percentiles)  
✅ Analyse multi-configurations  
✅ Documentation exhaustive  

### Production-Ready
- Code structuré et modulaire
- Tests complets validés
- Documentation technique et utilisateur
- Exemples d'utilisation variés
- Visualisations automatiques

### Prochaines Étapes Possibles
- Ajout de nouveaux scénarios hybrides
- Interface web (Dashboard interactif)
- Optimisation bayésienne des paramètres
- Intégration CI/CD
- Déploiement cloud

---

**Version:** 2.0  
**Date:** 11 janvier 2026  
**Maintainers:** Équipe ERO2  
**License:** Academic Use  

🎉 **Projet complet et opérationnel!**
