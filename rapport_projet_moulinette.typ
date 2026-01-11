#set document(
  title: "Rapport de Projet : Moulinette en tant que Système de File d'Attente",
)

#set page(
  paper: "a4",
  margin: (top: 2.5cm, bottom: 2.5cm, left: 2.5cm, right: 2.5cm),
  header: [
    #h(1fr)
    #set text(8pt)
    #context counter(page).display("1")
  ],
  footer: [
    #set text(8pt)
    EPITA - Rapport de Projet
    #h(1fr)
  ]
)

#set text(
  font: "New Computer Modern",
  lang: "fr",
)

// Title page
#align(center)[
  #v(2em)
  #text(2em, strong("Rapport de Projet"))
  #v(1em)
  #text(2.5em, strong("Moulinette en tant que Système de File d'Attente"))
  #v(3em)
  #text(1.2em, "Auteurs :")
  #v(0.5em)
  #text(1.2em, "Date : Janvier 2026") // Static date for template
  #v(5em)
  #text(1em, "EPITA")
]

#pagebreak()

#outline()

#pagebreak()

= Introduction
Ce rapport présente une analyse factuelle du simulateur de moulinette EPITA modélisé comme un système de files d'attente. Nous avons testé différents scénarios avec des paramètres variés pour évaluer le comportement du système. Les résultats sont basés sur des simulations à événements discrets utilisant SimPy.

= Terminologie
Voici quelques précisions sur la terminologie utilisée dans ce projet.

== Qu'est-ce qu'un utilisateur?
Dans ce contexte, un utilisateur est une personne ayant accès à l'infrastructure de correction dans le cadre d'une activité pédagogique spécifique. Cette personne peut effectuer deux actions :
#list(
  [Pousser son code sur l'infrastructure dans le cadre d'une mécanique standard de versionnage.],
  [Pousser un tag sur un commit pour déclencher l'exécution des test-suites associées à l'activité sur le code rendu, afin d'obtenir un retour sur sa conformité aux attentes.]
)

== Qu'est-ce qu'une moulinette?
Une moulinette est constituée formellement de :
#list(
  [Une #text(blue)[test-suite] : un ensemble de tests unitaires, éventuellement stratifiés.],
  [Un niveau d'information de retour : quel niveau d'information met-on à disposition des étudiants?],
  [Des ressources : nombre de push tags autorisés au total, par heure, ou dans des plages horaires définies.]
)

== Workflow nominal
Un étudiant code les réponses à des exercices dans un repository git dédié. Lorsqu'un tag est utilisé, une vérification est effectuée pour s'assurer qu'il correspond à un tag réservé. Si tel est le cas, la test-suite associée est exécutée selon le schéma du système d'attente.

= Étude de cas
L'étude d'un modèle de moulinettage implique des choix dépendants du contexte dans lequel le système est déployé. Les cas suivants sont présentés par ordre croissant de complexité.

== Waterfall
Dans ce modèle, tout agent de la population suit le processus séquentiel suivant :
1. Un push tag place le code dans une file d'attente FIFO pour l'exécution de la test-suite (K serveurs).
2. Le résultat de la test-suite est placé dans une file d'attente FIFO pour l'envoi vers le front (1 serveur).

Nous proposons un système d'attente modélisant ce contexte, en commençant par des files infinies, puis en introduisant des contraintes finies pour analyser les proportions de refus.



= Cas 1: File M/M/c Standard (Scénario Basique)

== Paramètres
- Taux d'arrivée λ = 2.0 jobs/unité de temps
- Taux de service μ = 3.0 jobs/unité de temps  
- Nombre de serveurs c = 1
- Taux d'utilisation théorique ρ = λ/(μ×c) = 0.67
- Durée de simulation: 2000 unités de temps

== Comportement du système

Le système avec ρ = 0.67 < 1 est *stable*. La file M/M/1 avec cette charge permet au système de traiter toutes les arrivées sans accumulation infinie.

#figure(
  image("results/basic_scenario/queue_length.png", width: 90%),
  caption: [Évolution de la longueur de file pour le scénario basique]
)

== Métriques observées

#table(
  columns: (auto, auto),
  [*Métrique*], [*Valeur*],
  [Débit], [1.9868 jobs/unité],
  [Utilisation serveur], [65.32%],
  [Temps d'attente moyen], [0.7048],
  [Temps de réponse moyen], [1.0336],
  [Temps d'attente P95], [2.9860],
  [Temps d'attente P99], [4.8134],
  [Taux de rejet], [0.00%]
)

#figure(
  image("results/basic_scenario/waiting_time.png", width: 90%),
  caption: [Distribution des temps d'attente]
)

= Cas 2: Files en Cascade (Waterfall)

== Paramètres

Configuration de référence testée:
- λ = 3.0 jobs/unité
- μ_exec = 2.5 jobs/unité (file d'exécution)
- μ_feed = 1.5 jobs/unité (file de feedback)
- c = 2 serveurs
- ks = 5 (capacité file exécution)
- kf = 5 (capacité file feedback)

== Comportement du système

Le système waterfall présente deux files en cascade avec capacités finies. Le comportement varie selon les capacités:

#table(
  columns: (auto, auto, auto, auto),
  [*Configuration*], [*Jobs Exec*], [*Rejet Exec*], [*Temps séjour*],
  [Sans files (loss)], [4499], [26.0%], [-],
  [Reference (ks=5, kf=5)], [5897], [1.0%], [3.87],
  [Petit ks (ks=2, kf=10)], [5674], [7.0%], [7.29],
  [Petit kf (ks=10, kf=2)], [5980], [0.1%], [2.14],
  [High traffic], [8188], [0.0%], [5.25]
)

#figure(
  image("results/waterfall_scenario/queue_length.png", width: 90%),
  caption: [Longueurs de files pour les configurations waterfall]
)

Le bottleneck se situe généralement au niveau du feedback (μ_feed < μ_exec). Augmenter kf améliore le temps de séjour, tandis qu'augmenter ks réduit les rejets à l'entrée.

#figure(
  image("results/waterfall_scenario/waiting_time.png", width: 90%),
  caption: [Distribution des temps d'attente en cascade]
)

= Cas 3: Populations Hétérogènes (Channels)

== Paramètres

- Population ING: λ_ING = 1.5, μ_ING = 2.5
- Population PREPA: λ_PREPA = 0.5, μ_PREPA = 2.0  
- Serveurs: c = 2
- Politiques testées: FIFO, SJF, PRIORITY

== Comportement du système

Le système gère deux populations avec des caractéristiques distinctes. La politique d'ordonnancement influence les performances:

#table(
  columns: (auto, auto, auto, auto),
  [*Politique*], [*ING (temps)*], [*PREPA (temps)*], [*Différence*],
  [FIFO], [0.4827], [0.5597], [+16.0%],
  [SJF], [0.4647], [0.5490], [+18.1%],
  [PRIORITY], [0.4679], [0.5920], [+26.5%]
)

FIFO offre l'équité la plus proche entre populations (différence 16.0%). PRIORITY favorise ING au détriment de PREPA (+26.5% de différence). Les deux populations ont traité respectivement 3061 et 956 jobs.

= Cas 4: Barrage Temporel (Gating)

== Paramètres

- Population ING: λ = 1.5, μ = 2.5
- Population PREPA: λ = 0.5, μ = 2.0
- Serveurs: c = 2
- Période de barrage: tb = 100
- Durée d'ouverture: 50 unités
- Intervalles de fermeture testés: [(0, 100), (150, 250), (300, 400)]

== Comportement du système

Le gating introduit des périodes de fermeture pendant lesquelles la population PREPA ne peut pas accéder au système. Cela augmente drastiquement les temps de réponse:

#table(
  columns: (auto, auto, auto, auto),
  [*Population*], [*Sans gating*], [*Avec gating*], [*Augmentation*],
  [ING], [0.4869], [9.8174], [+1916.4%],
  [PREPA], [0.5519], [10.0912], [+1728.5%]
)

Pendant les périodes de fermeture, les jobs PREPA s'accumulent dans la file, créant un effet de "burst" lors de la réouverture. L'impact est massif sur les deux populations malgré que seule PREPA soit bloquée directement.

= Cas 5: Validation Théorique (Advanced Metrics)

== Paramètres

- λ = 2.0 jobs/unité
- μ = 3.0 jobs/unité
- c = 2 serveurs
- ρ = 0.3333

== Vérification Loi de Little

La loi de Little stipule: L = λW (nombre moyen dans le système = taux d'arrivée × temps moyen de séjour)

#table(
  columns: (auto, auto, auto),
  [*Métrique*], [*Valeur*], [*Statut*],
  [L (observé)], [0.8027], [-],
  [λW], [0.7478], [-],
  [Erreur relative], [6.84%], [✓ Validé]
)

== Comparaison simulation vs théorie M/M/c

#table(
  columns: (auto, auto, auto, auto),
  [*Métrique*], [*Simulée*], [*Théorique*], [*Erreur*],
  [Utilisation], [0.3326], [0.3333], [0.23%],
  [Temps d'attente], [0.0412], [0.0417], [1.09%]
)

La simulation présente une *excellente* concordance avec la théorie M/M/c (erreur moyenne 0.63%). Les écarts sont dus à la variance d'échantillonnage.

#figure(
  image("results/advanced_scenario/queue_length.png", width: 90%),
  caption: [Stabilité du système avec c=2 serveurs]
)

= Cas 6: Stratégies de Backup

== Paramètres

- λ = 2.0 jobs/unité
- μ = 3.0 (service principal)
- μ_b = 10.0 (service backup)
- c = 2 serveurs
- Durée: 2000 unités

== Comportement des stratégies

Trois stratégies de backup ont été testées:

#table(
  columns: (auto, auto, auto, auto),
  [*Stratégie*], [*Jobs traités*], [*Jobs sauvegardés*], [*Taux backup*],
  [Systematic], [4002], [4004], [100.05%],
  [Random 50%], [3934], [2013], [51.17%],
  [Random 20%], [4000], [811], [20.28%]
)

Le temps de backup moyen reste stable (~0.10) pour toutes les stratégies. La stratégie systematic garantit la sauvegarde de tous les jobs, tandis que les stratégies probabilistes permettent d'économiser des ressources au prix d'une couverture partielle.

#figure(
  image("results/backup_scenario/response_time_by_type.png", width: 90%),
  caption: [Temps de réponse selon la stratégie de backup]
)

= Synthèse et Observations

== Stabilité des systèmes

- *M/M/c stable*: ρ < 1 assure la stabilité (cas 1 et 5)
- *Files finies*: taux de rejet fonction de la capacité (cas 2)
- *Gating*: instabilité temporaire pendant les fermetures (cas 4)

== Métriques clés observées

#table(
  columns: (auto, auto, auto, auto),
  [*Scénario*], [*Débit*], [*Utilisation*], [*Temps réponse*],
  [Basic M/M/1], [1.99], [65.32%], [1.03],
  [Waterfall], [9.39], [163.14%], [0.79],
  [Advanced M/M/2], [2.01], [33.26%], [0.37],
)

== Impact des paramètres

- *Capacités (ks, kf)*: augmentation réduit rejets mais accroît temps de séjour
- *Politique ordonnancement*: FIFO plus équitable, PRIORITY favorise une population
- *Gating*: impact majeur (+1900%) sur temps de réponse
- *Nombre serveurs*: c=2 vs c=1 réduit fortement temps d'attente (0.04 vs 0.70)

= Conclusion

Les simulations démontrent que le système de moulinette peut être modélisé efficacement comme un réseau de files d'attente. Les paramètres critiques sont:
- Le taux d'utilisation ρ pour la stabilité
- Les capacités des files pour gérer les pics
- La politique d'ordonnancement pour l'équité
- La gestion temporelle (gating) qui a l'impact le plus significatif

