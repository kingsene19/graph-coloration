import sys
import os
import time
import threading
from pulp import LpProblem, LpVariable, lpSum, LpMinimize, LpBinary, LpStatus
from pulp import PULP_CBC_CMD
from concurrent.futures import ThreadPoolExecutor, as_completed
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.graph import ColorGraph

TIMEOUT_SECONDS = 60
MAX_WORKERS = 8

def solve_with_timeout(graph, timeout):
    """
    Fonction qui résout le problème de coloration de graphe avec une limite de temps.
    Utilise la bibliothèque PuLP pour formuler le problème comme un problème de programmation linéaire.
    """
    def solve_internal():
        num_nodes = graph.countNode()
        num_edges = graph.countEdge()

        # Création du problème de programmation linéaire
        problem = LpProblem("Graph_Coloring", LpMinimize)

        # Variables de décision X[(i, c)] : 1 si le nœud i utilise la couleur c
        X = {
            (i, c): LpVariable(f"X_{i}_{c}", 0, 1, LpBinary)
            for i in range(num_nodes)
            for c in range(num_nodes)
        }

        # Variable "used[c]" indique si la couleur c est utilisée
        used = {c: LpVariable(f"used_{c}", 0, 1, LpBinary) for c in range(num_nodes)}

        # Objectif : minimiser le nombre de couleurs utilisées
        problem += lpSum(used[c] for c in range(num_nodes)), "Minimize_Colors"

        # Contrainte : chaque nœud doit avoir exactement une couleur
        for i in range(num_nodes):
            problem += lpSum(X[(i, c)] for c in range(num_nodes)) == 1, f"One_Color_Node_{i}"

        # Contrainte : les nœuds adjacents doivent avoir des couleurs différentes
        edge_count = 0
        for i in range(1, num_nodes + 1):
            for j in graph.childNode(i):  # Récupérer les voisins du nœud i
                if i < j:  # Éviter de traiter chaque arête deux fois
                    for c in range(num_nodes):
                        problem += X[(i - 1, c)] + X[(j - 1, c)] <= 1, f"Diff_Color_Edge_{edge_count}_Color_{c}"
                    edge_count += 1

        # Contrainte : si un nœud utilise une couleur, alors cette couleur doit être marquée comme utilisée
        for i in range(num_nodes):
            for c in range(num_nodes):
                problem += X[(i, c)] <= used[c], f"Link_Node_{i}_Color_{c}"

        # Résolution du problème avec le solveur CBC de PuLP
        solver = PULP_CBC_CMD(msg=False, timeLimit=timeout)
        status = problem.solve(solver)

        # Vérification si la solution trouvée est optimale
        if LpStatus[problem.status] == "Optimal":
            coloring = {}
            num_colors_used = sum(used[c].varValue for c in range(num_nodes))  # Nombre de couleurs utilisées
            for i in range(num_nodes):
                for c in range(num_nodes):
                    if X[(i, c)].varValue > 0.5:  # Si la variable X[(i, c)] est active, le nœud i a la couleur c
                        coloring[i + 1] = c
                        break
            return True, coloring, num_colors_used
        return False, None, None  

    result = [None]
    start_time = time.time() 

    def target():
        """Fonction exécutée dans un thread, qui appelle la fonction de résolution."""
        try:
            result[0] = solve_internal()
        except Exception as e:
            print(f"\nError in solver for {graph.name}: {str(e)}")
            result[0] = (False, None, None)

    thread = threading.Thread(target=target)
    thread.start()
    thread.join(timeout)

    duration = time.time() - start_time

    if thread.is_alive():
        print(f"\nTimeout occurred for {graph.name}")
        return False, None, None, duration
        
    status, coloring, n_colors = result[0]
    return status, coloring, n_colors, duration

def process_graph(graph):
    """Fonction qui traite un graphe individuel et retourne les résultats du traitement"""
    print(f"\nProcessing graph: {graph.name}")
    try:
        status, coloring, n_colors, duration = solve_with_timeout(graph, TIMEOUT_SECONDS)
        msg = f"\rProcessing {graph.name}: [n={n_colors if n_colors else 0}] ({duration:.2f}s)\x1b[0m\n"
        sys.stdout.write(msg)
        sys.stdout.flush()
        num_nodes = graph.countNode()
        num_edges = graph.countEdge()
        edge_density = 2 * num_edges / (num_nodes * (num_nodes - 1)) if num_nodes > 1 else 0
        return (graph.name, num_nodes, edge_density, duration, status)
    except Exception as e:
        print(f"\nError processing {graph.name}: {str(e)}")
        return None

def main():
    """Fonction principale qui charge les graphes, les traite en parallèle et affiche les résultats"""
    list_g = [ColorGraph.load(name) for name in ColorGraph.list_name()]
    list_g = sorted(list_g, key=lambda x: x.countNode())
    results = []

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_graph = {executor.submit(process_graph, graph): graph for graph in list_g}
        
        for future in as_completed(future_to_graph):
            try:
                result = future.result()
                if result:
                    results.append(result)
            except Exception as e:
                graph = future_to_graph[future]
                print(f"\nUnexpected error for {graph.name}: {str(e)}")

    if results:
        print("\nSummary:")
        print(f"Total graphs: {len(list_g)}")
        print(f"Solved: {sum(1 for r in results if r[4])}")
        avg_time = sum(r[3] for r in results) / len(results)
        print(f"Average time: {avg_time:.2f}s")

if __name__ == "__main__":
    main()
