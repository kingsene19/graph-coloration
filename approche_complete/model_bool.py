import sys
import os
import time
import matplotlib.pyplot as plt
import networkx as nx
from ortools.sat.python import cp_model
from concurrent.futures import ThreadPoolExecutor, TimeoutError

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.graph import ColorGraph

TIMEOUT_SECONDS = 60
MAX_WORKERS = 8

def solve(graph):
    """
    Résout le problème de coloration de graphe en utilisant OR-Tools.
    - Crée un modèle de programmation par contraintes.
    - Ajoute les contraintes pour garantir une coloration valide.
    - Minimise le nombre de couleurs utilisées.
    """
    model = cp_model.CpModel()
    num_nodes = graph.countNode()
    
    # Création des variables de décision
    # X[(i, c)] indique si le nœud i utilise la couleur c
    X = {}
    for i in range(num_nodes):
        for c in range(num_nodes):
            X[(i, c)] = model.NewBoolVar(f'X_{i}_{c}')
    
    # used[c] indique si la couleur c est utilisée
    used = [model.NewBoolVar(f'used_{c}') for c in range(num_nodes)]
    
    # Contrainte : Chaque nœud doit utiliser exactement une couleur
    for i in range(num_nodes):
        model.Add(sum(X[(i, c)] for c in range(num_nodes)) == 1)
    
    # Contrainte : Deux nœuds adjacents ne peuvent pas avoir la même couleur
    for i in range(1, num_nodes + 1):
        for j in graph.childNode(i):
            if i < j:  # Évite les doublons en traitant chaque arête une seule fois
                for c in range(num_nodes):
                    model.Add(X[(i-1, c)] + X[(j-1, c)] <= 1)
    
    # Contrainte : Si un nœud utilise une couleur, cette couleur est marquée comme utilisée
    for i in range(num_nodes):
        for c in range(num_nodes):
            model.AddImplication(X[(i, c)], used[c])
    
    # Objectif : Minimiser le nombre total de couleurs utilisées
    model.Minimize(sum(used))
    
    # Configuration et résolution du modèle
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = TIMEOUT_SECONDS
    st = time.time()
    status = solver.Solve(model)
    duration = time.time() - st
    
    # Si une solution est trouvée, on récupère les résultats
    if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
        coloring = {i + 1: c for i in range(num_nodes) for c in range(num_nodes) if solver.Value(X[(i, c)])}
        num_colors_used = sum(solver.Value(used[c]) for c in range(num_nodes))
        return status, coloring, num_colors_used, duration
    else:
        return status, None, None, duration

def process_graph(graph):
    """
    Traite un graphe individuel :
    - Appelle la fonction `solve` pour résoudre la coloration.
    - Affiche le statut et les statistiques du graphe.
    """
    print(f"\nProcessing graph: {graph.name}")
    status, coloring, n_colors, duration = solve(graph)
    
    # Conversion du statut en texte lisible
    status_name = {
        cp_model.OPTIMAL: "OPTIMAL",
        cp_model.FEASIBLE: "FEASIBLE",
        cp_model.INFEASIBLE: "INFEASIBLE",
        cp_model.MODEL_INVALID: "MODEL_INVALID"
    }.get(status, "UNKNOWN")
    
    # Couleur pour l'affichage du statut
    status_color = {
        cp_model.OPTIMAL: "\x1b[32m",
        cp_model.FEASIBLE: "\x1b[32m",
        cp_model.INFEASIBLE: "\x1b[31m",
        cp_model.MODEL_INVALID: "\x1b[31m"
    }.get(status, "\x1b[33m")
    
    sys.stdout.write(f"\rProcessing {graph.name}: {status_color}{status_name} [n={n_colors if n_colors else 0}] ({duration:.2f}s)\x1b[0m\n")
    
    solved = status_name == "OPTIMAL"
    print(solved)
    
    num_nodes = graph.countNode()
    num_edges = graph.countEdge()
    edge_density = 2 * num_edges / (num_nodes * (num_nodes - 1)) if num_nodes > 1 else 0
    
    return (num_nodes, edge_density, duration, solved)

def main():
    """
    Fonction principale :
    - Charge tous les graphes à résoudre.
    - Traite chaque graphe en parallèle.
    - Affiche un résumé global des performances.
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
        print("\nSummary:")
        print(f"Total graphs: {len(results)}")
        print(f"Solved: {sum(1 for r in results if r[3])}")
        avg_time = sum(r[2] for r in results) / len(results)
        print(f"Average time: {avg_time:.2f}s")

if __name__ == "__main__":
    main()
