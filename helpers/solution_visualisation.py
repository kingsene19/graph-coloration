import matplotlib.pyplot as plt

def visualize_solvability(results):
    num_nodes = [stats.num_nodes for stats in results]
    edge_densities = [stats.edge_density for stats in results]
    solvable = [1 if stats.solved else 0 for stats in results]

    plt.figure(figsize=(10, 6))
    plt.scatter(num_nodes, edge_densities, c=solvable, cmap='coolwarm', label='Solvability', alpha=0.7)
    plt.colorbar(label='Solvability (1: Solved, 0: Not Solved)')
    plt.title('Graph Coloring Solvability Based on Nodes and Edge Density')
    plt.xlabel('Number of Nodes')
    plt.ylabel('Edge Density')
    plt.grid()
    plt.show()

def visualize_resolution_time(results):
    num_nodes = [stats.num_nodes for stats in results]
    edge_densities = [stats.edge_density for stats in results]
    durations = [stats.duration for stats in results]

    plt.figure(figsize=(10, 6))
    plt.scatter(num_nodes, edge_densities, c=durations, cmap='viridis', label='Resolution Time', alpha=0.7)
    plt.colorbar(label='Resolution Time (seconds)')
    plt.title('Graph Coloring Resolution Time Based on Nodes and Edge Density')
    plt.xlabel('Number of Nodes')
    plt.ylabel('Edge Density')
    plt.grid()
    plt.show()