"""Priority queue helpers for ForestWatch alerts."""
from __future__ import annotations

import heapq
from dataclasses import dataclass, field
from itertools import count

from forestwatch.schemas.events import AlertPriority, ForestEvent


@dataclass(order=True, frozen=True)
class QueuedEvent:
    """Heap entry ordered by alert priority and insertion sequence."""

    priority: int
    sequence: int
    event: ForestEvent = field(compare=False)


class PriorityEventQueue:
    """Stable priority queue where lower numeric priority is delivered first."""

    def __init__(self) -> None:
        self._heap: list[QueuedEvent] = []
        self._sequence = count()

    def put(self, event: ForestEvent) -> None:
        heapq.heappush(
            self._heap,
            QueuedEvent(int(event.priority), next(self._sequence), event),
        )

    def get(self) -> ForestEvent:
        if not self._heap:
            raise IndexError("cannot get from an empty priority queue")
        return heapq.heappop(self._heap).event

    def __len__(self) -> int:
        return len(self._heap)

    def is_empty(self) -> bool:
        return not self._heap



def priority_name(priority: AlertPriority) -> str:
    """Return a stable display name for an alert priority."""
    return priority.name
