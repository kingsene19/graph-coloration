### Coloration de graphes

Ce projet traite du problème de coloration de graphes, consistant à attribuer des couleurs aux sommets d'un graphe de manière à ce que deux sommets adjacents n'aient jamais la même couleur. Le but est de minimiser le nombre de couleurs utilisées (nombre chromatique). Ce problème est NP-difficile et a des applications variées telles que la planification et l'allocation de ressources. Il a été réalisé en collaboration avec Axel Colmant dans le cadre du l'UE Graphes, Complexité et Combinatoire à l'Université Claude Bernard Lyon 1.

#### Approches utilisées

**Approche Complète**
- Modélisation en utilisant des variables représentant les couleurs attribuées aux nœuds.
- Contraintes d’inégalité entre les nœuds adjacents.
- Deux variantes :
    - Attribution directe des couleurs.
    - Utilisation de variables booléennes pour valider ou non une couleur.
- Résolution via OR-Tools avec des stratégies d’optimisation basées sur la densité du graphe.

**Approche Incomplète**
- Algorithme glouton aléatoire : construction progressive de groupes stables.
- Optimisation locale et réassignation aléatoire pour éviter les minima locaux.
- DSATUR : algorithme basé sur la saturation des couleurs pour prioriser les sommets à traiter.

#### Benchmarks
Utilisation des ensembles de données standards DIMACS et Queen Graphs pour évaluer la performance.