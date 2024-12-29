import os
from .download import DATASET_PATH

class ColorGraph:
    @staticmethod
    def list_file():
        os.makedirs(DATASET_PATH, exist_ok=True)
        ls = os.listdir(DATASET_PATH)
        return [file for file in ls if file.endswith(".col")]
    
    @staticmethod
    def list_name():
        ls = ColorGraph.list_file()
        return [os.path.splitext(file)[0] for file in ls]
    
    @staticmethod
    def load(name):
        if name not in ColorGraph.list_name():
            raise FileNotFoundError(f"Dataset '{name}' not found in {DATASET_PATH}")
        return ColorGraph(name)
    
    @staticmethod
    def parse(file_content):
        graph = {}
        num_vertices = 0
        for line in file_content.split("\n"):
            if line.startswith("p"):
                num_vertices = int(line.split()[2])
                for i in range(1, num_vertices + 1):
                    graph[i] = []
            elif line.startswith("e"):
                _, node1, node2 = line.split()
                node1, node2 = int(node1), int(node2)
                graph[node1].append(node2)
                graph[node2].append(node1)
        return graph
    
    
    def __init__(self, name):
        if name not in ColorGraph.list_name():
            raise FileNotFoundError(f"Dataset '{name}' not found in {DATASET_PATH}")
        self.filepath = os.path.join(DATASET_PATH, name + ".col")
        self.name = name
        with open(self.filepath, 'r') as file:
            self.graph = self.parse(file.read())
        self.colors = {k: 0 for k in self.graph}
                    
            
    def countNode(self):
        return len(self.graph)
    
    def countEdge(self):
        return sum([len(self.graph[node]) for node in self.graph]) // 2
    
    def getGraph(self):
        return self.graph
    
    def childNode(self, node):
        return self.graph[node]
    
    def setColors(self, colors: dict[int, int]):
        set_nodes = set(colors.keys())
        
        if not isinstance(colors, dict):
            raise ValueError("Variable 'colors' must be a dictionary")
        if set_nodes != set(self.graph.keys()):
            raise ValueError("Variable 'colors' must have the same keys as the graph")
        if not all([isinstance(v, int) for v in colors.values()]):
            raise ValueError("Variable 'colors' must have integer values")
        
        self.colors = colors
        
    def getColors(self):
        return self.colors
    
    def countColors(self):
        return len(set(self.colors.values())) 