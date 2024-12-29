import sys
import os
import time
from ortools.sat.python import cp_model
from concurrent.futures import ThreadPoolExecutor, TimeoutError

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.graph import ColorGraph

TIMEOUT_SECONDS = 60
MAX_WORKERS = 8

def solve(graph):
    """
    Résout le problème de coloriage de graphe en utilisant le solveur CP-SAT d'OR-Tools.
    - Définit des variables pour les couleurs des nœuds.
    - Ajoute des contraintes pour garantir un coloriage valide.
    - Minimise le nombre de couleurs utilisées.
    """
    g = graph.getGraph()
    model = cp_model.CpModel()
    num_nodes = len(g)

    # Crée des variables de décision pour les couleurs des nœuds
    colors = {node: model.NewIntVar(0, num_nodes - 1, f'color_{node}') for node in g}
    max_color = model.NewIntVar(0, num_nodes - 1, 'max_color')

    # Ajoute des contraintes : les nœuds adjacents ne doivent pas partager la même couleur
    added_edges = set()
    for node in g:
        for child in g[node]:
            if (node, child) not in added_edges and (child, node) not in added_edges:
                model.Add(colors[node] != colors[child])  # Enforce des couleurs différentes pour les nœuds adjacents
                added_edges.add((node, child))

    # Ajoute des contraintes : la couleur de chaque nœud ne doit pas dépasser la couleur maximale
    for node in g:
        model.Add(colors[node] <= max_color)

    # Objectif : minimiser la couleur maximale utilisée
    model.Minimize(max_color)

    # Résout le modèle avec un délai d'attente
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = TIMEOUT_SECONDS
    st = time.time()
    status = solver.Solve(model)
    duration = time.time() - st  # Temps écoulé pour résoudre le modèle

    # Traite les résultats si une solution a été trouvée
    if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
        coloring = {node: solver.Value(colors[node]) for node in g}
        num_colors_used = solver.Value(max_color) + 1
        return status, coloring, num_colors_used, duration
    else:
        return status, None, None, duration

def process_graph(graph):
    """
    Traite un seul graphe :
    - Appelle la fonction solve pour calculer le coloriage.
    - Affiche le statut et les métriques de performance pour le graphe.
    """
    print(f"\nTraitement du graphe : {graph.name}")
    status, coloring, n_colors, duration = solve(graph)

    # Traduction du statut du solveur en un format lisible
    status_name = {
        cp_model.OPTIMAL: "OPTIMAL",
        cp_model.FEASIBLE: "FEASIBLE",
        cp_model.INFEASIBLE: "INFEASIBLE",
        cp_model.MODEL_INVALID: "MODEL_INVALID"
    }.get(status, "UNKNOWN")

    # Choix de la couleur d'affichage en fonction du statut
    status_color = {
        cp_model.OPTIMAL: "\x1b[32m",  # Vert pour OPTIMAL
        cp_model.FEASIBLE: "\x1b[32m",  # Vert pour FEASIBLE
        cp_model.INFEASIBLE: "\x1b[31m",  # Rouge pour INFEASIBLE
        cp_model.MODEL_INVALID: "\x1b[31m"  # Rouge pour MODEL_INVALID
    }.get(status, "\x1b[33m")  # Jaune pour un statut inconnu

    # Affichage du statut et du nombre de couleurs utilisées
    sys.stdout.write(f"\rTraitement du graphe {graph.name}: {status_color}{status_name} [n={n_colors if n_colors else 0}] ({duration:.2f}s)\x1b[0m\n")

    solved = status_name == "OPTIMAL"

    # Calcul de la densité des arêtes pour le graphe
    num_nodes = graph.countNode()
    num_edges = graph.countEdge()
    edge_density = 2 * num_edges / (num_nodes * (num_nodes - 1)) if num_nodes > 1 else 0

    return (num_nodes, edge_density, duration, solved)

def main():
    """
    Fonction principale :
    - Charge et trie tous les graphes par le nombre de nœuds.
    - Traite chaque graphe en parallèle.
    - Affiche un résumé des résultats.
    """
    list_g = [ColorGraph.load(name) for name in ColorGraph.list_name()]
    list_g = sorted(list_g, key=lambda x: x.countNode())

    results = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(process_graph, graph): i for i, graph in enumerate(list_g)}
        for future in futures:
            stats = future.result()
            if stats:
                results.append(stats)

    if results:
        print("\nRésumé :")
        print(f"Total des graphes : {len(list_g)}")
        print(f"Résolus : {sum(1 for r in results if r[3])}")
        avg_time = sum(r[2] for r in results) / len(results)
        print(f"Temps moyen : {avg_time:.2f}s")

if __name__ == "__main__":
    main()
