from typing import Tuple, Dict
import os
import sys
import time
from collections import deque
from concurrent.futures import ThreadPoolExecutor
import random
import numpy as np

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.graph import ColorGraph
from helpers.solutions_stats import SolutionStats
from helpers.solution_visualisation import visualize_resolution_time, visualize_solvability
from helpers.solution_save import save_results_to_file

TIMEOUT_SECONDS = 600
MAX_WORKERS = 8

class GraphColoringSolver:
    def __init__(self, graph):
        """Initialise le solveur avec un graphe donné."""
        self.graph = graph
        self.num_nodes = graph.countNode()
        self.num_edges = graph.countEdge()

    def calculate_conflicts(self, colors: Dict[int, int]) -> Tuple[int, set]:
        """
        Calcule le nombre de conflits dans la coloration actuelle (c'est-à-dire les arêtes entre sommets de même couleur).
        Retourne le nombre de conflits et les nœuds impliqués dans ces conflits.
        """
        conflicts = 0
        conflict_nodes = set()
        for node, neighbors in self.graph.getGraph().items():
            for neighbor in neighbors:
                if neighbor in colors and colors[node] == colors[neighbor]:
                    conflicts += 1
                    conflict_nodes.add(node)
        return conflicts // 2, conflict_nodes  # Diviser par 2 car chaque conflit est compté deux fois

    def select_next_node_probabilistic(self, available_nodes: set, probabilities: Dict[int, float]) -> int:
        """
        Sélectionne un nœud parmi les nœuds disponibles, selon une distribution de probabilités.
        """
        nodes = list(available_nodes)
        weights = [probabilities.get(node, 0) for node in nodes]  # Poids associés à chaque nœud
        if sum(weights) == 0:
            weights = [1.0 / len(nodes)] * len(nodes)  # Si aucune probabilité, attribuer des poids égaux
        return random.choices(nodes, weights=weights, k=1)[0]  # Sélection aléatoire basée sur les poids

    def find_solution(self, probabilities: Dict[int, float]) -> Tuple[Dict[int, int], int]:
        """
        Trouve une solution initiale en utilisant une heuristique basée sur les probabilités.
        La stratégie choisit un nœud à colorier, puis colore un ensemble indépendant autour de ce nœud.
        """
        colors = {}
        available_nodes = set(self.graph.getGraph().keys())
        color = 0

        while available_nodes:
            # Sélectionne un nœud à colorier probabilistiquement
            node = self.select_next_node_probabilistic(available_nodes, probabilities)
            independent_set = {node}  # Ensemble indépendant de nœuds
            queue = deque([node])
            available_nodes.remove(node)

            while queue:
                # Défilement du nœud actuel
                current_node = queue.popleft()
                candidates = [
                    neighbor for neighbor in self.graph.getGraph()[current_node]
                    if neighbor in available_nodes and all(
                        n not in self.graph.getGraph()[neighbor] for n in independent_set
                    )
                ]
                for candidate in candidates:
                    independent_set.add(candidate)
                    queue.append(candidate)
                    available_nodes.remove(candidate)

            # Assigne des couleurs aux nœuds de l'ensemble indépendant
            for node in independent_set:
                possible_colors = set(range(color)) - {
                    colors.get(neighbor) for neighbor in self.graph.getGraph()[node]
                }
                if possible_colors:
                    colors[node] = min(possible_colors)  # Choisit la plus petite couleur disponible
                else:
                    colors[node] = color  # Si aucune couleur possible, on crée une nouvelle couleur
                    color += 1

        return colors, color  # Retourne la solution et le nombre de couleurs utilisées

    def random_reassign_colors(self, colors: Dict[int, int], percentage: float = 0.2) -> Dict[int, int]:
        """
        Réassigne aléatoirement les couleurs à un pourcentage de nœuds pour éviter les minima locaux.
        """
        nodes = list(colors.keys())
        random.shuffle(nodes)
        num_to_reassign = int(len(nodes) * percentage)
        for node in nodes[:num_to_reassign]:
            colors[node] = random.randint(0, max(colors.values()))
        return colors

    def local_search(self, colors: Dict[int, int], max_iterations: int = 50) -> Tuple[Dict[int, int], int]:
        """
        Améliore la solution obtenue en utilisant une recherche locale, en essayant de réduire le nombre de couleurs.
        """
        best_colors = colors.copy()
        best_num_colors = max(colors.values()) + 1

        for iteration in range(max_iterations):
            improved = False
            nodes = list(best_colors.keys())
            random.shuffle(nodes)

            for node in nodes:
                original_color = best_colors[node]
                for new_color in range(best_num_colors - 1):
                    # Essaye de réaffecter la couleur du nœud sans créer de conflit
                    if all(best_colors.get(neighbor) != new_color for neighbor in self.graph.getGraph()[node]):
                        best_colors[node] = new_color
                        break

                current_num_colors = max(best_colors.values()) + 1
                if current_num_colors < best_num_colors:
                    best_num_colors = current_num_colors
                    improved = True
                else:
                    best_colors[node] = original_color  # Restaure la couleur initiale du nœud

            if not improved:
                best_colors = self.random_reassign_colors(best_colors)  # Si aucune amélioration, réassigner les couleurs aléatoirement

        return best_colors, best_num_colors

    def solve(self) -> SolutionStats:
        """
        Résout le problème de coloration du graphe en combinant la recherche probabilistique et la recherche locale.
        """
        if self.num_nodes == 0:
            return SolutionStats(
                status="INFEASIBLE",
                coloring={},
                num_colors=0,
                duration=0,
                num_nodes=self.num_nodes,
                edge_density=0,
                solved=False
            )

        start_time = time.time()
        # Probabilités initiales égales pour chaque nœud
        probabilities = {node: 1.0 / self.num_nodes for node in self.graph.getGraph().keys()}
        best_solution = None
        best_num_colors = self.num_nodes

        for iteration in range(10):
            # Trouve une solution initiale avec l'heuristique probabilistique
            solution, num_colors = self.find_solution(probabilities)
            if num_colors < best_num_colors:
                best_solution = solution
                best_num_colors = num_colors

            # Calcule les conflits et ajuste les probabilités pour les nœuds impliqués dans des conflits
            _, conflict_nodes = self.calculate_conflicts(solution)
            for node in conflict_nodes:
                probabilities[node] += 0.1  # Augmente la probabilité pour les nœuds en conflit
            total_probability = sum(probabilities.values())
            if total_probability > 0:
                for node in probabilities:
                    probabilities[node] /= total_probability  # Normalise les probabilités

        # Améliore la solution obtenue avec une recherche locale
        if best_solution:
            refined_solution, refined_num_colors = self.local_search(best_solution, max_iterations=50)
        else:
            refined_solution, refined_num_colors = {}, self.num_nodes

        duration = time.time() - start_time
        solved = refined_solution is not None and duration < TIMEOUT_SECONDS

        return SolutionStats(
            status="OPTIMAL" if solved else "INFEASIBLE",
            coloring=refined_solution,
            num_colors=refined_num_colors if solved else None,
            duration=duration,
            num_nodes=self.num_nodes,
            edge_density=self.num_edges / ((self.num_nodes * (self.num_nodes - 1)) // 2) if self.num_nodes > 1 else 0,
            solved=solved
        )

def process_graph(graph):
    """ Traite un graphe et sauvegarde les résultats de la résolution. """
    print(f"\nTraitement du graphe : {graph.name}")
    solver = GraphColoringSolver(graph)
    stats = solver.solve()

    if stats:
        print(f"Statut: {'OPTIMAL' if stats.solved else 'INFEASIBLE'}")
        print(f"Nombre de nœuds: {stats.num_nodes}")
        print(f"Densité: {stats.edge_density:.3f}")
        if stats.solved:
            print(f"Couleurs utilisées: {stats.num_colors}")
        print(f"Temps: {stats.duration:.2f}s")

        edges = list(graph.getGraph().items())
        edges = [(node, child) for node, children in edges for child in children]

        save_results_to_file("results_incomplete", graph.name, stats, edges, "OPTIMAL" if stats.solved else "INFEASIBLE")

    return stats

def main():
    """ Point d'entrée du programme pour traiter plusieurs graphes. """
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
        print("\nRésumé:")
        print(f"Total des graphes : {len(list_g)}")
        print(f"Résolus : {sum(1 for r in results if r.solved)}")
        avg_time = sum(r.duration for r in results) / len(results)
        print(f"Temps moyen : {avg_time:.2f}s")

        visualize_solvability(results)
        visualize_resolution_time(results)

if __name__ == "__main__":
    main()
