"""Small weighted communication topology used by the prototype."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final

import networkx as nx


DEFAULT_EDGES: Final[tuple[tuple[str, str, float], ...]] = (
    ("forest_hub", "node_a", 2.0),
    ("forest_hub", "node_b", 5.0),
    ("node_a", "village_a", 3.0),
    ("node_b", "district", 2.0),
    ("district", "control_room", 1.0),
)


@dataclass(frozen=True)
class Route:
    """A weighted shortest route between two network nodes."""

    source: str
    destination: str
    path: tuple[str, ...]
    cost: float



def build_default_topology() -> nx.Graph:
    """Build the deterministic six-node ForestWatch prototype topology."""
    graph = nx.Graph()
    graph.add_weighted_edges_from(DEFAULT_EDGES, weight="weight")
    return graph



def shortest_route(graph: nx.Graph, source: str, destination: str) -> Route:
    """Find the minimum-weight route using Dijkstra's algorithm."""
    path = nx.shortest_path(graph, source=source, target=destination, weight="weight")
    cost = float(nx.path_weight(graph, path, weight="weight"))
    return Route(source, destination, tuple(path), cost)
