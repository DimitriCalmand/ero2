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
  #text(1em, "École Pour l'Informatique et les Techniques Avancées")
]

#pagebreak()

#outline()

#pagebreak()

= Introduction
Dans le cadre de ce projet, nous allons explorer l'infrastructure de correction automatique de l'École, la "moulinette", sous l'angle des systèmes d'attente. L'objectif est d'analyser son comportement et de proposer des modélisations.

= Livrables
Le présent rapport inclut, pour chaque cas d'étude :
#enum(
  [Le code permettant de simuler les systèmes d'attente.],
  [Une analyse du comportement de chaque cas traité, comprenant au minimum :
    #list(
      [Les paramètres en jeu.],
      [Le comportement du système d'attente en fonction des paramètres qui le définissent, notamment en ce qui concerne sa stabilité.],
      [Une évaluation du système au regard de métriques standard : nombre d'agents, temps de séjour, taux de blocage, etc.],
      [Une synthèse des résultats et des recommandations pour des plages de paramètres permettant un comportement acceptable et efficace, incluant une analyse des risques côté expérience utilisateur.]
    )
  ],
  [Les résultats bruts des simulations soutenant les observations.]
)

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

=== Simulation
Le code de simulation utilise la classe `WaterfallScenario` du module capacity. Pour les files infinies, nous utilisons `finite=False` pour éviter les rejets et observer le comportement naturel. Pour les files finies, nous comparons des scénarios avec et sans files d'attente limitées.

Exemple de code pour simulation infinie :
```
scenario = WaterfallScenario(
    env=engine.env,
    logger=engine.logger,
    num_servers=2,
    execution_queue_size=None,  # Ignoré en mode infini
    execution_rate=2.5,
    feedback_queue_size=None,
    feedback_rate=1.5,
    arrival_rate=3.0,
    duration=1000.0,
    finite=False
)
engine.env.process(scenario.arrivals())
engine.run(duration)
sojourn_stats = scenario.get_sojourn_stats()
```

Pour les files finies, nous exécutons plusieurs configurations avec différents paramètres (λ, μ_exec, μ_feed, c, ks, kf).

=== Analyse
Les paramètres en jeu incluent :
- λ : taux d'arrivée des jobs (push tags).
- μ_exec : taux de service pour l'exécution (test-suite).
- μ_feed : taux de service pour l'envoi des résultats.
- c : nombre de serveurs pour l'exécution.
- ks, kf : tailles maximales des files d'exécution et de feedback (pour mode fini).

Le comportement du système montre que les files infinies évitent les rejets mais entraînent des temps de séjour élevés avec forte variance (ex. : temps moyen ~23.6, variance ~93.6 pour λ=3.0, μ_exec=2.5, μ_feed=1.5, c=2). En mode fini, les rejets apparaissent principalement dans la file de feedback (ex. : 52-60% de rejets sans file, réduits à 7-55% avec files limitées), améliorant le débit d'exécution (+60-70 jobs) mais maintenant des rejets.

La stabilité dépend de ρ = λ/(c*μ_exec) : pour ρ < 1, le système est stable, sinon instable. Recommandations : files finies avec ks=5-10, kf=5-10 pour λ=3.0 permettent un bon compromis débit/rejets. Analyse des risques : rejets élevés peuvent frustrer les utilisateurs ; backup nécessaire pour éviter pertes de données.

=== Résultats bruts
Simulation infinie (durée=100, λ=3.0, μ_exec=2.5, μ_feed=1.5, c=2) :
- Jobs exécutés : 306
- Jobs finalisés : 140
- Temps de séjour moyen : 23.6116
- Variance empirique : 93.5903
- Rejets (Exec/Feed) : 0/0

Configuration "Reference" (ks=5, kf=5) :
- Sans file : Exec 226 complétés (28.0% rejets), Feed 95 (57.5% rejets)
- Avec files : Exec 289 (0.7% rejets), Feed 133 (52.6% rejets)
- Gain Exec : +63 jobs
- Temps séjour moyen : 4.4729, Variance : 3.5904

[Autres configurations similaires, avec variations selon ks/kf.]

== Canaux et Barrages
Dans ce modèle, certaines populations d'étudiants ont des temps d'attente plus élevés que d'autres. Des régulations peuvent être introduites pour minimiser le temps de séjour moyen.

=== Simulation
[Insérer le code de simulation pour le modèle Canaux et Barrages ici.]

=== Analyse
[Analyser les paramètres en jeu, le comportement du système, la stabilité, les métriques (nombre d'agents, temps de séjour, taux de blocage), synthèse des résultats et recommandations.]

=== Résultats bruts
[Insérer les résultats bruts des simulations ici.]

= Conclusion
[Synthèse générale du projet, leçons apprises, perspectives.]

= Références
[Liste des références utilisées.]
