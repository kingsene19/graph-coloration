from typing import Tuple, Optional
import sys
import os
import time
from ortools.sat.python import cp_model
from concurrent.futures import ThreadPoolExecutor, TimeoutError
import json

utils_path = '../../'
base_dir = os.path.dirname(__file__)
sys.path.append(os.path.abspath(os.path.join(base_dir, utils_path)))

from utils.graph import ColorGraph
from helpers.solutions_stats import SolutionStats
from helpers.solution_visualisation import visualize_resolution_time, visualize_solvability
from helpers.solution_save import save_results_to_file

TIMEOUT_SECONDS = 600 
MAX_WORKERS = 8

class GraphColoringSolver:
    """
    Cette classe gère la résolution du problème de coloration de graphes
    en utilisant OR-Tools pour formuler et résoudre les contraintes.
    """

    def __init__(self, graph: ColorGraph):
        self.graph = graph
        self.model = cp_model.CpModel()
        self.solver = cp_model.CpSolver()
        self.colors = {}
        self.max_color = None
        self.setup_solver()

    def setup_solver(self):
        self.solver.parameters.max_time_in_seconds = TIMEOUT_SECONDS
        self.solver.parameters.num_search_workers = MAX_WORKERS
        self.solver.parameters.log_search_progress = False
        self.solver.parameters.search_branching = cp_model.FIXED_SEARCH

    def create_variables(self):
        """
        Crée les variables du modèle :
        - Une variable pour chaque nœud, représentant sa couleur (valeurs possibles : [0, n-1]).
        - Une variable globale pour la couleur maximale utilisée.
        """
        g = self.graph.getGraph()
        num_nodes = len(g)
        self.colors = {node: self.model.NewIntVar(0, num_nodes - 1, f'color_{node}') for node in g}
        self.max_color = self.model.NewIntVar(0, num_nodes - 1, 'max_color')

    def add_constraints(self):
        """
        Ajoute les contraintes principales :
        - Les couleurs de deux nœuds connectés (par une arête) doivent être différentes.
        - Chaque nœud doit avoir une couleur inférieure ou égale à la couleur maximale.
        """
        g = self.graph.getGraph()
        for node in g:
            for child in g[node]:
                self.model.Add(self.colors[node] != self.colors[child])
            self.model.Add(self.colors[node] <= self.max_color)

    def add_custom_search_strategy(self, edge_density):
        """
        Ajoute une stratégie de recherche personnalisée en fonction de la densité des arêtes :
        - Si le graphe est peu dense, priorité aux nœuds avec un degré élevé.
        - Si le graphe est dense, priorité aux nœuds avec une saturation élevée (nombre de couleurs déjà assignées aux voisins).
        """
        g = self.graph.getGraph()
        
        if edge_density < 0.5:
            # Tri des nœuds par degré décroissant pour graphes peu denses
            sorted_nodes_by_degree = sorted(g.keys(), key=lambda node: len(g[node]), reverse=True)
            degree_based_variables = [self.colors[node] for node in sorted_nodes_by_degree]
            self.model.AddDecisionStrategy(
                degree_based_variables,
                cp_model.CHOOSE_FIRST,
                cp_model.SELECT_MIN_VALUE
            )
            if len(sorted_nodes_by_degree) > 0:
                self.model.Add(self.colors[sorted_nodes_by_degree[0]] == 0)
        else:
            # Tri par saturation estimée pour graphes denses
            estimated_saturation_order = sorted(
                g.keys(),
                key=lambda node: len(set(g[node])),
                reverse=True
            )
            saturation_variables = [self.colors[node] for node in estimated_saturation_order]
            self.model.AddDecisionStrategy(
                saturation_variables,
                cp_model.CHOOSE_FIRST,
                cp_model.SELECT_MIN_VALUE
            )
            if len(estimated_saturation_order) > 0:
                self.model.Add(self.colors[estimated_saturation_order[0]] == 0)

    def solve(self):
        """
        Résout le problème de coloration de graphe :
        - Définit les variables, les contraintes et la stratégie de recherche.
        - Minimise la couleur maximale utilisée.
        - Retourne les statistiques de la solution.
        """
        if not self.graph.getGraph():
            return SolutionStats(
                status=cp_model.INFEASIBLE,
                coloring={},
                num_colors=0,
                duration=0.0,
                num_nodes=0,
                edge_density=0.0,
                solved=False
            )
        
        self.create_variables()
        self.add_constraints()
        num_nodes = self.graph.countNode()
        num_edges = self.graph.countEdge()
        max_edges = (num_nodes * (num_nodes - 1)) // 2
        edge_density = num_edges / max_edges if max_edges > 0 else 0
        self.add_custom_search_strategy(edge_density)
        self.model.Minimize(self.max_color)

        start_time = time.time()
        status = self.solver.Solve(self.model)
        duration = time.time() - start_time
        
        # Vérifie si le problème a été résolu dans le délai imparti
        solved = (status in (cp_model.OPTIMAL, cp_model.FEASIBLE)) and (duration <= TIMEOUT_SECONDS)
        coloring = {node: self.solver.Value(self.colors[node]) for node in self.colors} if (status in (cp_model.OPTIMAL, cp_model.FEASIBLE)) else None
        num_colors = self.solver.Value(self.max_color) + 1 if (status in (cp_model.OPTIMAL, cp_model.FEASIBLE)) else None

        return SolutionStats(
            status=status,
            coloring=coloring,
            num_colors=num_colors,
            duration=duration,
            num_nodes=num_nodes,
            edge_density=edge_density,
            solved=solved
        )

def process_graph(graph):
    """
    Traite un graphe en utilisant le solveur, puis sauvegarde et affiche les résultats.
    """
    print(f"\nProcessing graph: {graph.name}")
    solver = GraphColoringSolver(graph)
    stats = solver.solve()
    
    if stats is not None:
        status_name = {
            cp_model.OPTIMAL: "OPTIMAL",
            cp_model.FEASIBLE: "FEASIBLE",
            cp_model.INFEASIBLE: "INFEASIBLE",
            cp_model.MODEL_INVALID: "MODEL_INVALID"
        }.get(stats.status, "UNKNOWN")
        
        print(f"Status: {status_name}")
        print(f"Number of nodes: {stats.num_nodes}")
        print(f"Density: {stats.edge_density:.3f}")
        if stats.solved:
            print(f"Colors used: {stats.num_colors}")
        print(f"Time: {stats.duration:.2f}s")
        
        edges = list(graph.getGraph().items())
        edges = [(node, child) for node, children in edges for child in children]
        save_results_to_file("results_optimized", graph.name, stats, edges, status_name)

    return stats

def main():
    """
    Fonction principale :
    - Charge tous les graphes.
    - Résout les problèmes en parallèle.
    - Affiche un résumé des performances.
    """
    list_g = [ColorGraph.load(name) for name in ColorGraph.list_name()]
    graphs = sorted(list_g, key=lambda x: x.countNode())
    
    results = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(process_graph, graph): i for i, graph in enumerate(graphs)
        }
        
        for future in futures:
            stats = future.result(timeout=TIMEOUT_SECONDS)
            if stats:
                results.append(stats)

    if results:
        print("\nSummary:")
        print(f"Total graphs: {len(list_g)}")
        print(f"Solved: {sum(1 for r in results if r.solved)}")
        avg_time = sum(r.duration for r in results) / len(results)
        print(f"Average time: {avg_time:.2f}s")
        
        # Visualisation des résultats
        visualize_solvability(results)
        visualize_resolution_time(results)

if __name__ == "__main__":
    main()
