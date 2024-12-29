from dataclasses import dataclass
from typing import Optional, Dict

@dataclass
class SolutionStats:
    status: int
    coloring: Optional[Dict[int, int]]
    num_colors: Optional[int]
    duration: float
    num_nodes: int
    edge_density: float
    solved: bool