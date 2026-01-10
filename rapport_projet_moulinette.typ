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
Dans ce modèle, tout agent de la population suit un processus séquentiel.

=== Simulation
[Insérer le code de simulation pour le modèle Waterfall ici.]

=== Analyse
[Analyser les paramètres en jeu, le comportement du système, la stabilité, les métriques (nombre d'agents, temps de séjour, taux de blocage), synthèse des résultats et recommandations.]

=== Résultats bruts
[Insérer les résultats bruts des simulations ici.]

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
