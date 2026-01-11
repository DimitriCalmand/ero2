# 🎓 Simulateur de Moulinette - Projet ERO2

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-17%2F17%20passing-brightgreen.svg)](tests/)
[![Code](https://img.shields.io/badge/code-4090%2B%20lines-orange.svg)](src/)

## 📖 Description

Simulateur à événements discrets de l'infrastructure de la moulinette EPITA. Modélise le parcours des soumissions (git push tag) dans un réseau de files d'attente pour identifier les points de rupture et optimiser les performances.

**Technologies:** SimPy 4.1.1, Pandas, NumPy, Matplotlib, Seaborn

## 📁 Structure du Projet

```
ero2/
├── src/                   # Code source (4090+ lignes)
│   ├── core/              # Moteur de simulation (420 lignes)
│   ├── capacity/          # Gestion des capacités (360 lignes)
│   ├── reliability/       # Stratégies de backup (410 lignes)
│   ├── regulation/        # Régulation (1200+ lignes, 7 fichiers)
│   └── analysis/          # Analyse statistique (800+ lignes)
│
├── tests/                 # Tests unitaires (17 tests, 100% succès)
│   ├── test_core.py
│   ├── test_capacity.py
│   ├── test_reliability.py
│   ├── test_regulation.py
│   └── run_all_tests.py
│
├── main.py                # Script principal (8 scénarios)
├── requirements.txt       # Dépendances Python
└── tags                   # Données réelles (159K lignes)
```

## ⚡ Installation Rapide (30 secondes)

```bash
# 1. Activer l'environnement virtuel
source .venv/bin/activate

# 2. Installer les dépendances
pip install -r requirements.txt

# 3. Vérifier l'installation
python tests/run_all_tests.py
```

**Résultat attendu:** ✓ ALL TESTS PASSED (17/17)

## 🚀 Utilisation

### Commande de Base

```bash
python main.py --scenario <nom> --duration <temps> [options]
```

### Scénarios Disponibles

| Scénario | Description | Commande |
|----------|-------------|----------|
| **basic** | M/M/c standard | `python main.py --scenario basic --duration 1000` |
| **waterfall** | Files en cascade | `python main.py --scenario waterfall --duration 1000` |
| **backup** | Stratégies de redondance | `python main.py --scenario backup --duration 1000` |
| **channels** | Populations hétérogènes | `python main.py --scenario channels --duration 1000` |
| **gating** | Barrage temporel | `python main.py --scenario gating --duration 1000` |
| **optimization** | Recherche paramètres optimaux | `python main.py --scenario optimization --duration 5000` |
| **advanced** | Métriques avancées (Little) | `python main.py --scenario advanced --duration 1000` |
| **gating-analysis** | Analyse approfondie gating ✨ | `python main.py --scenario gating-analysis --duration 5000` |

### Options

| Option | Description | Défaut |
|--------|-------------|--------|
| `--scenario` | Nom du scénario | `basic` |
| `--duration` | Durée de simulation | `1000` |
| `--seed` | Graine aléatoire | `42` |
| `--visualize` | Générer visualisations | `False` |
| `--output-dir` | Répertoire de sortie | `./output/` |

### Exemples Rapides

```bash
# Simulation basique avec visualisations
python main.py --scenario channels --duration 1000 --visualize

# Analyse complète du gating
python main.py --scenario gating-analysis --duration 5000 --visualize --output-dir results/

# Tests unitaires
python tests/run_all_tests.py
```
- `population_analysis_report.txt`

#### 9. Scénario basé sur Données Réelles
```bash
# Mode Poisson classique
python main.py --scenario real --tags-file tags --duration 1000

## 🧪 Tests

### Exécution

```bash
# Tous les tests (recommandé)
python tests/run_all_tests.py

# Test individuel
python tests/test_regulation.py
```

### Résultats

| Module | Tests | Statut |
|--------|-------|--------|
| Core | 4 | ✅ 100% |
| Capacity | 3 | ✅ 100% |
| Reliability | 4 | ✅ 100% |
| Regulation | 6 | ✅ 100% |
| **TOTAL** | **17** | ✅ **100%** |

## 📊 Fonctionnalités Principales

### Scénarios de Simulation
✅ **M/M/c Standard** - Modèle de base avec files infinies  
✅ **Waterfall** - Files en cascade avec capacités finies  
✅ **Backup** - Stratégies de redondance (Cold/Warm/Hot Standby)  
✅ **Channels** - Populations hétérogènes (ING/PREPA)  
✅ **Gating** - Barrage temporel avec cycles ouverture/fermeture  
✅ **Optimization** - Recherche automatique de paramètres optimaux  
✅ **Advanced** - Vérification loi de Little, comparaison théorique  
✨ **Gating-Analysis** - Analyse exhaustive multi-configurations  

### Métriques Avancées
✅ Temps d'attente, temps de réponse, utilisation serveurs  
✅ Taux de rejet, débit système, longueur de file  
✅ Vérification loi de Little (L = λW)  
✅ Comparaison simulation vs théorie M/M/c  
✨ **Jain's Fairness Index** - Équité entre populations  
✨ **Percentiles détaillés** - P50, P95, P99 par population  
✨ **SLA Compliance** - Conformité aux seuils par type  

### Analyses Spécialisées
✅ Optimisation grid search (ks, kf)  
✅ Analyse temporelle (autocorrélation, patterns)  
✅ Rejeu de données réelles avec timestamps exacts  
✨ **Analyse gating multi-configurations** - 16+ tests automatiques  
✨ **Visualisations avancées** - Heatmaps, courbes d'impact  
✨ **Recommandation automatique** - Configuration optimale basée sur contraintes  

## 📖 Documentation

| Fichier | Contenu | Audience |
|---------|---------|----------|
| **README.md** | Documentation principale (ce fichier) | Tous |
| **GUIDE_COMPLET.md** | Guide exhaustif détaillé | Développeurs |
| **CHANNELS_RECOMMENDATIONS.md** | Guide de décision Channels & Dams | Analystes |
| **IMPLEMENTATION_COMPLETE.md** | Rapport d'implémentation final | Tech leads |

### Liens Rapides

- **Guide Complet:** [GUIDE_COMPLET.md](GUIDE_COMPLET.md) - Architecture détaillée, tous les scénarios, exemples d'utilisation
- **Guide Channels:** [CHANNELS_RECOMMENDATIONS.md](CHANNELS_RECOMMENDATIONS.md) - Choix FIFO/SJF/PRIORITY, configuration gating, use cases
- **Rapport Implémentation:** [IMPLEMENTATION_COMPLETE.md](IMPLEMENTATION_COMPLETE.md) - Détails techniques, statistiques, tests

## 💡 Exemples d'Utilisation

### Analyse de Base
- Distribution des temps d'attente
- Temps de réponse par type de job
- Rapport textuel complet
- **NOUVEAU ✨:** Heatmaps d'impact du gating (4 métriques)
- **NOUVEAU ✨:** Courbes d'impact temporel
- **NOUVEAU ✨:** Front de Pareto pour configurations

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
# Simulation basique M/M/c
python main.py --scenario basic --duration 1000

# Avec visualisations
python main.py --scenario channels --duration 1000 --visualize
```

### Analyse Populations Hétérogènes
```python
from src.regulation import ChannelsScenario
from src.analysis import PopulationAnalyzer
from src.core import SimulationEngine

# Simulation
engine = SimulationEngine(random_seed=42)
scenario = ChannelsScenario(
    env=engine.env,
    logger=engine.logger,
    num_servers=3,
    scheduling_policy="FIFO"  # ou "SJF", "PRIORITY"
)

scenario.add_population("ING", arrival_rate=1.5, service_rate=2.5)
scenario.add_population("PREPA", arrival_rate=0.5, service_rate=2.0)
scenario.run(duration=1000.0)

# Analyse fairness
df = engine.logger.get_dataframe()
analyzer = PopulationAnalyzer(df)

fairness = analyzer.calculate_fairness_index()
print(f"Fairness Index: {fairness['fairness_index']:.4f}")

percentiles = analyzer.calculate_percentiles_by_type()
print(f"ING P95: {percentiles['ING']['response_time']['p95']:.4f}s")

compliance = analyzer.calculate_sla_compliance({"ING": 1.0, "PREPA": 2.0})
print(f"ING SLA Compliance: {compliance['ING']['compliance_percentage']:.2f}%")
```

### Analyse Gating Multi-Configurations
```python
from src.regulation import GatingAnalyzer

# Créer l'analyseur
analyzer = GatingAnalyzer(
    lambda_ing=1.5,
    mu_ing=2.5,
    lambda_prepa=0.5,

# Test multiples configurations
results_df = analyzer.analyze_gating_variations(
    tb_values=[50, 100, 150, 200],
    ratio_values=[0.25, 0.5, 0.75],
    duration=5000
)

# Générer visualisations (heatmaps + courbes)
analyzer.plot_gating_impact(results_df)

# Recommandation automatique
recommendation = analyzer.recommend_gating_config(results_df, max_time_increase_pct=50.0)
print(f"Config optimale: tb={recommendation['tb']}, ratio={recommendation['ratio']:.2f}")
```

## 🎯 Cas d'Usage Typiques

### 1. Dimensionner le Système
```bash
# Recherche automatique de (ks, kf) optimaux
python main.py --scenario optimization --duration 5000 --visualize
```

### 2. Analyser la Fairness entre Populations
```bash
# Test FIFO vs SJF vs PRIORITY
python main.py --scenario channels --duration 1000 --visualize
```

### 3. Configurer le Gating pour Maintenance
```bash
# Analyse exhaustive de configurations
python main.py --scenario gating-analysis --duration 5000 --visualize
```

### 4. Valider le Modèle
```bash
# Vérification loi de Little et comparaison théorique
python main.py --scenario advanced --duration 1000
```

## 📞 Support

Pour plus de détails:
- Consulter [GUIDE_COMPLET.md](GUIDE_COMPLET.md) pour l'architecture complète
- Consulter [CHANNELS_RECOMMENDATIONS.md](CHANNELS_RECOMMENDATIONS.md) pour les décisions Channels & Dams
- Lire les docstrings dans le code source
- Examiner les tests unitaires pour des exemples d'utilisation

---

**Version:** 2.0  
**Date:** 11 janvier 2026  
**Statut:** Production Ready ✅  
**Tests:** 17/17 passing (100%)  
**Code:** 4090+ lignes


## Documentation Complète

📚 **Guides Disponibles:**
- [README.md](README.md) - Ce fichier
- [QUICKSTART.md](QUICKSTART.md) - Guide rapide de démarrage
- [CHANNELS_RECOMMENDATIONS.md](CHANNELS_RECOMMENDATIONS.md) ✨ - Guide de décision pour Channels & Dams
- [NOUVELLES_FONCTIONNALITES.md](NOUVELLES_FONCTIONNALITES.md) - Nouvelles fonctionnalités détaillées
- [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) - Résumé des implémentations
- [AUDIT_CHANNELS_DAMS.md](AUDIT_CHANNELS_DAMS.md) - Audit complet des fonctionnalités

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
