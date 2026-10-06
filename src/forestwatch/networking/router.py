"""Priority-aware routing over the weighted prototype graph."""
from __future__ import annotations

from dataclasses import dataclass

import networkx as nx

from forestwatch.networking.topology import Route, shortest_route
from forestwatch.schemas.events import ForestEvent


@dataclass(frozen=True)
class RoutedEvent:
    """An event paired with its selected destination and shortest path."""

    event: ForestEvent
    route: Route


class PriorityRouter:
    """Route ForestWatch events through the configured weighted graph."""

    def __init__(self, graph: nx.Graph | None = None) -> None:
        self.graph = graph if graph is not None else nx.Graph()

    def route(self, event: ForestEvent, *, source: str, destination: str) -> RoutedEvent:
        """Return the shortest path for an event."""
        route = shortest_route(self.graph, source, destination)
        return RoutedEvent(event=event, route=route)
