import matplotlib.pyplot as plt
import networkx as nx

def plot_resolution_map(data):
    num_nodes, edge_densities, durations = zip(*[(d[0], d[1], d[2]) for d in data])

    plt.figure(figsize=(10, 6))
    sc = plt.scatter(num_nodes, edge_densities, c=durations, cmap='viridis', s=100, alpha=0.7, edgecolors='w', linewidth=0.5)
    plt.colorbar(sc, label='Temps de résolution (s)')
    plt.xlabel('Nombre de noeuds')
    plt.ylabel('Densité')
    plt.title('Temps de résolution en fonction du nombre de noeuds et de la densité')
    plt.grid(True)
    plt.show()

def plot_solved_vs_unsolved(data):
    num_nodes, edge_densities, solved = zip(*[(d[0], d[1], d[3]) for d in data])

    solved_numeric = [1 if s else 0 for s in solved]

    plt.figure(figsize=(10, 6))
    sc = plt.scatter(num_nodes, edge_densities, c=solved_numeric, cmap='coolwarm', s=100, alpha=0.7, edgecolors='w', linewidth=0.5)
    plt.colorbar(sc, label='Résolus (1) / Non Résolus (0)')
    plt.xlabel('Nombre de noeuds')
    plt.ylabel('Densité')
    plt.title('Statut de résolution en fonction du nombre de noeuds et de la densité')
    plt.grid(True)
    plt.show()
