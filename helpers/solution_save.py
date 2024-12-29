from helpers.solutions_stats import SolutionStats
import json
import numpy as np

def convert_int64_to_int(obj):
    if isinstance(obj, dict):
        return {convert_int64_to_int(k): convert_int64_to_int(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_int64_to_int(item) for item in obj]
    elif isinstance(obj, np.int64):
        return int(obj)
    else:
        return obj

def save_results_to_file(folder_name,graph_name, stats, edges, status_name):
    result = {
        "graph_name": graph_name,
        "status": status_name,
        "coloring": stats.coloring,
        "num_colors": stats.num_colors,
        "duration": stats.duration,
        "num_nodes": stats.num_nodes,
        "edge_density": stats.edge_density,
        "solved": stats.solved,
        "edges": edges
    }
    result = convert_int64_to_int(result)
    with open(f"{folder_name}/{graph_name}_results.json", "w") as f:
        json.dump(result, f, indent=4)