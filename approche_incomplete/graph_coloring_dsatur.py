from typing import Tuple, Optional
import sys
import os
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.graph import ColorGraph
from helpers.solutions_stats import SolutionStats
from helpers.solution_visualisation import visualize_resolution_time, visualize_solvability
from helpers.solution_save import save_results_to_file

TIMEOUT_SECONDS = 600
MAX_WORKERS = 8

class GraphColoringSolver:
    def __init__(self, graph):
        self.graph = graph
        self.colors = {}
        self.max_color = None
        self.uncolored_vertices = set(graph.getGraph().keys())

    def get_neighbors(self, vertex):
        """ Récupère les voisins d'un sommet dans le graphe. """
        return self.graph.getGraph().get(vertex, [])

    def get_saturation_degree(self, vertex, color_assignment):
        """
        Calcul du degré de saturation d'un sommet (nombre de couleurs utilisées par ses voisins).
        """
        neighbors = self.get_neighbors(vertex)
        colors_used = set()

        for neighbor in neighbors:
            if neighbor in color_assignment:
                colors_used.add(color_assignment[neighbor])

        return len(colors_used)

    def dsatur_coloring(self):
        """
        Algorithme de coloriage DSATUR pour résoudre le problème de coloriage de graphe.
        L'algorithme choisit le sommet avec le plus grand degré de saturation pour l'assigner à une couleur.
        """
        color_assignment = {}
        available_colors = {i for i in range(len(self.graph.getGraph()))} 
        uncolored_vertices = self.uncolored_vertices.copy() 

        # Initialisation : choisir un sommet arbitraire (le premier sommet de la liste)
        first_vertex = next(iter(uncolored_vertices))
        color_assignment[first_vertex] = 0
        uncolored_vertices.remove(first_vertex)

        while uncolored_vertices:
            # Trouver le sommet avec la plus grande saturation
            max_saturation = -1
            vertex_to_color = None

            # Parcourt les sommets non coloriés et trouve celui avec la plus grande saturation
            for vertex in uncolored_vertices:
                saturation = self.get_saturation_degree(vertex, color_assignment)
                if saturation > max_saturation:
                    max_saturation = saturation
                    vertex_to_color = vertex
                elif saturation == max_saturation:
                    # En cas d'égalité, choisit celui avec le plus grand degré
                    if len(self.get_neighbors(vertex)) > len(self.get_neighbors(vertex_to_color)):
                        vertex_to_color = vertex

            # Assigner la couleur la plus faible disponible pour ce sommet
            neighbor_colors = set(color_assignment.get(neighbor) for neighbor in self.get_neighbors(vertex_to_color))
            for color in available_colors:
                if color not in neighbor_colors:
                    color_assignment[vertex_to_color] = color
                    break

            uncolored_vertices.remove(vertex_to_color)

        return color_assignment

    def solve(self):
        """
        Résout le problème de coloriage pour le graphe en utilisant l'algorithme DSATUR.
        """
        if not self.graph.getGraph():
            return SolutionStats(
                status="INFEASIBLE",
                coloring={},
                num_colors=0,
                duration=0.0,
                num_nodes=0,
                edge_density=0.0,
                solved=False
            )

        start_time = time.time()
        coloring = self.dsatur_coloring()
        duration = time.time() - start_time

        num_nodes = len(self.graph.getGraph())
        num_edges = sum(len(neighbors) for neighbors in self.graph.getGraph().values()) // 2
        max_edges = (num_nodes * (num_nodes - 1)) // 2
        edge_density = num_edges / max_edges if max_edges > 0 else 0

        num_colors = len(set(coloring.values())) 

        solved = True if num_colors > 0 else False

        return SolutionStats(
            status="OPTIMAL" if solved else "INFEASIBLE",
            coloring=coloring,
            num_colors=num_colors,
            duration=duration,
            num_nodes=num_nodes,
            edge_density=edge_density,
            solved=solved
        )

def process_graph(graph):
    """
    Traite un graphe : résout le problème de coloriage et sauvegarde les résultats.
    """
    print(f"\nTraitement du graphe : {graph.name}")
    solver = GraphColoringSolver(graph)
    stats = solver.solve()

    if stats is not None:
        status_name = stats.status
        print(f"Status: {status_name}")
        print(f"Nombre de nœuds: {stats.num_nodes}")
        print(f"Densité: {stats.edge_density:.3f}")
        if stats.solved:
            print(f"Couleurs utilisées: {stats.num_colors}")
        print(f"Temps: {stats.duration:.2f}s")

        edges = list(graph.getGraph().items())
        edges = [(node, child) for node, children in edges for child in children]

        save_results_to_file("results_dsatur", graph.name, stats, edges, status_name)

    return stats

def main():
    """
    Fonction principale qui charge les graphes, les traite en parallèle et affiche un résumé.
    """
    list_g = [ColorGraph.load(name) for name in ColorGraph.list_name()]
    graphs = sorted(list_g, key=lambda x: x.countNode())

    results = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(process_graph, graph): i for i, graph in enumerate(graphs)
        }
        for future in futures:
            stats = future.result()
            if stats:
                results.append(stats)

    if results:
        print("\nRésumé :")
        print(f"Total des graphes : {len(list_g)}")
        print(f"Résolus : {sum(1 for r in results if r.solved)}")
        avg_time = sum(r.duration for r in results) / len(results)
        print(f"Temps moyen : {avg_time:.2f}s")

        visualize_solvability(results)
        visualize_resolution_time(results)

if __name__ == "__main__":
    main()
