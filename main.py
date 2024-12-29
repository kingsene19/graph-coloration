import json
import networkx as nx
import matplotlib.pyplot as plt
import json
import os
from statistics import mean
import math

def visualize_coloring(filename):
    with open(filename, "r") as f:
        data = json.load(f)

    G = nx.Graph()
    G.add_nodes_from(data["coloring"].keys())
    
    G.add_edges_from(data["edges"])

    try:
        color_map = [data["coloring"][str(node)] for node in G.nodes]
    except KeyError as e:
        print(f"KeyError: Node {e} n'est pas dans les donnees.")
        return

    plt.figure(figsize=(10, 7))
    pos = nx.spring_layout(G)


    nx.draw_networkx_edges(G, pos, edge_color='black')
    nx.draw_networkx_nodes(G, pos, node_color=color_map, node_size=50)
    nx.draw_networkx_labels(G, pos, font_weight='bold', font_size=4)


    plt.title(f'Coloration pour {data["graph_name"]}')
    plt.axis('off')
    plt.show()

def compare_graph_colors(reference_file, results_folder):
    with open(reference_file, 'r') as f:
        reference_data = json.load(f)
    
    comparison_results = {
        'same': 0,
        'inferior': 0,
        'more': 0,
        'better': [],
        'worse': []
    }
    
    for ref_graph in reference_data:
        graph_name = ref_graph['graph_name']
        ref_colors = ref_graph['num_colors']
        
        result_file = os.path.join(results_folder, f"{graph_name}_results.json")
        
        try:
            with open(result_file, 'r') as f:
                result_data = json.load(f)
                result_colors = result_data['num_colors']
                
                if result_colors is not None:
                    if result_colors == ref_colors:
                        comparison_results['same'] += 1
                    elif result_colors < ref_colors:
                        comparison_results['inferior'] += 1
                        comparison_results['better'].append(graph_name)
                    else:
                        comparison_results['more'] += 1
                        comparison_results['worse'].append(graph_name)
                else:
                    comparison_results['more'] += 1
                    comparison_results['worse'].append(graph_name)
                
        except FileNotFoundError:
            print(f"Pas de fichier pour le graphe {graph_name}")
            continue

    print(f"\nComparaison au benchmark {results_folder}")
    print("-" * 50)
    print(f"Nombre de résolution similaire: {comparison_results['same']}")
    print(f"Nombre de résolution meilleure: {comparison_results['inferior']}")
    print(f"Nombre de résolution pire: {comparison_results['more']}")
    print(f"Liste des instances meilleure: {comparison_results['better']}")
    print(f"Liste des instances pires: {comparison_results['worse']}")
    
    return comparison_results

def analyze_results(results_dir, results_optimized_dir, method_1, method_2):
    stats = {
        'mean_solving_duration_results': 0,
        'mean_solving_duration_optimized': 0,
        'total_instances': 0,
        'total_solved': 0,
        'results_better': 0,
        'optimized_better': 0,
        'only_results_solved': 0,
        'only_optimized_solved': 0,
        'both_solved': 0
    }
    
    result_files = set(os.listdir(results_dir))
    optimized_files = set(os.listdir(results_optimized_dir))
    common_files = result_files.intersection(optimized_files)
    
    results_durations = []
    optimized_durations = []
    
    stats['total_instances'] = len(common_files)
    
    for filename in common_files:
        with open(os.path.join(results_dir, filename)) as f:
            result_data = json.load(f)
        with open(os.path.join(results_optimized_dir, filename)) as f:
            optimized_data = json.load(f)
            
        result_solved = result_data.get('solved', False) or result_data.get('status') == 'FEASIBLE'
        optimized_solved = optimized_data.get('solved', False) or optimized_data.get('status') == 'FEASIBLE'
        
        if result_solved:
            results_durations.append(result_data['duration'])
        if optimized_solved:
            optimized_durations.append(optimized_data['duration'])
        
        if result_solved and optimized_solved:
            stats['both_solved'] += 1
            result_colors = result_data['num_colors']
            optimized_colors = optimized_data['num_colors']
            
            if result_colors == optimized_colors:
                if result_data['duration'] < optimized_data['duration']:
                    stats['results_better'] += 1
                elif result_data['duration'] > optimized_data['duration']:
                    stats['optimized_better'] += 1
            elif result_colors < optimized_colors:
                stats['results_better'] += 1
            else:
                stats['optimized_better'] += 1
        elif result_solved:
            stats['only_results_solved'] += 1
        elif optimized_solved:
            stats['only_optimized_solved'] += 1
    
    stats['mean_solving_duration_results'] = mean(results_durations) if results_durations else 0
    stats['mean_solving_duration_optimized'] = mean(optimized_durations) if optimized_durations else 0
    
    print("\nAnalysis Results:")
    print("-" * 50)
    print(f"Nombre d'instances totales: {stats['total_instances']}")
    print("\nStatistiques de résolution:")
    print(f"Instances résolues par les deux méthodes: {stats['both_solved']}")
    print(f"Instances résolues seulement par {method_1}: {stats['only_results_solved']}")
    print(f"Instances résolues seulement par {method_2}: {stats['only_optimized_solved']}")
    print("\nComparaison:")
    print(f"{method_1} meilleur: {stats['results_better']}")
    print(f"{method_2} meilleur: {stats['optimized_better']}")
    print("\nPerformance:")
    print(f"Temps de résolution moyen de {method_1}: {stats['mean_solving_duration_results']:.4f} seconds")
    print(f"Temps de résolution moyen de {method_2}: {stats['mean_solving_duration_optimized']:.4f} seconds")

def analyze_incomplete_vs_complete(results_dir, incomplete_results_dir):
    stats = {
        'mean_solving_duration_complete': 0,
        'mean_solving_duration_incomplete': 0,
        'mean_normalized_distance_to_optimal': 0,
        'total_instances': 0,
        'complete_solved': 0,
        'incomplete_solved': 0,
        'complete_better': 0,
        'incomplete_better': 0,
        'both_solved': 0,
    }
    
    result_files = set(os.listdir(results_dir))
    incomplete_files = set(os.listdir(incomplete_results_dir))
    common_files = result_files.intersection(incomplete_files)
    
    complete_durations = []
    incomplete_durations = []
    normalized_distances = []
    
    stats['total_instances'] = len(common_files)
    
    for filename in common_files:
        with open(os.path.join(results_dir, filename)) as f:
            complete_data = json.load(f)
        with open(os.path.join(incomplete_results_dir, filename)) as f:
            incomplete_data = json.load(f)
            
        complete_solved = complete_data.get('solved', False) or complete_data.get('status') == 'FEASIBLE'
        incomplete_solved = incomplete_data.get('solved', False)
        
        if complete_solved:
            complete_durations.append(complete_data['duration'])
        if incomplete_solved:
            incomplete_durations.append(incomplete_data['duration'])

        complete_colors = complete_data['num_colors'] 
        incomplete_colors = incomplete_data['num_colors']
        
        if complete_solved and incomplete_solved:
            normalized_distance = (complete_colors / incomplete_colors) * 100
            normalized_distances.append(normalized_distance)
            stats['both_solved'] += 1
            if incomplete_colors > complete_colors:
                stats['complete_better'] += 1
            elif incomplete_colors < complete_colors:
                stats['incomplete_better'] += 1
            else:  
                if complete_data['duration'] < incomplete_data['duration']:
                    stats['complete_better'] += 1
                else:
                    stats['incomplete_better'] += 1
        elif complete_solved:
            stats['complete_solved'] += 1
        elif incomplete_solved:
            stats['incomplete_solved'] += 1

    stats['mean_solving_duration_complete'] = mean(complete_durations) if complete_durations else 0
    stats['mean_solving_duration_incomplete'] = mean(incomplete_durations) if incomplete_durations else 0
    stats['mean_normalized_distance_to_optimal'] = mean(normalized_distances) if normalized_distances else 0
    
    print("\nRésultats de l'Analyse:")
    print("-" * 50)
    print(f"Nombre total d'instances: {stats['total_instances']}")
    print("\nRésolution:")
    print(f"Instances résolues par les deux approches: {stats['both_solved']}")
    print(f"Instances résolues uniquement par l'approche complète: {stats['complete_solved']}")
    print(f"Instances résolues uniquement par l'approche incomplète: {stats['incomplete_solved']}")
    print("\nComparaison de Qualité:")
    print(f"L'approche complète a produit de meilleures solutions: {stats['complete_better']}")
    print(f"L'approche incomplète a produit de meilleures solutions: {stats['incomplete_better']}")
    print(f"Distance moyenne normalisée à l'optimal pour l'approche incomplète: {stats['mean_normalized_distance_to_optimal']:.2f}%")
    print("\nPerformance:")
    print(f"Temps moyen de résolution de l'approche complète: {stats['mean_solving_duration_complete']:.4f} secondes")
    print(f"Temps moyen de résolution de l'approche incomplète: {stats['mean_solving_duration_incomplete']:.4f} secondes")


if __name__ == "__main__":
    compare_graph_colors("benchmark_results.json", "results")
    compare_graph_colors("benchmark_results.json", "results_optimized")
    compare_graph_colors("benchmark_results.json", "results_incomplete")
    compare_graph_colors("benchmark_results.json", "results_dsatur")
    analyze_results("results", "results_optimized", "solveur param default", "solveur nos params")
    analyze_results("results_incomplete", "results_dsatur", "glouton aleatoire", "DSATUR")
    analyze_incomplete_vs_complete("results_optimized", "results_dsatur")