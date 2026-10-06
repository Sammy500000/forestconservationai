"""Deterministic local networking demonstration."""
from __future__ import annotations

import asyncio
import time

from forestwatch.networking.metrics import DeliverySample, calculate_metrics
from forestwatch.networking.notifications import deliver_concurrently
from forestwatch.networking.priority import PriorityEventQueue
from forestwatch.networking.router import PriorityRouter
from forestwatch.networking.topology import build_default_topology
from forestwatch.schemas.events import ForestEvent


RECIPIENTS: tuple[str, ...] = ("node_a", "district", "control_room")


def build_demo_events() -> list[ForestEvent]:
    """Create four events covering every configured priority level."""
    return [
        ForestEvent(
            event_id=f"PHASE4-DEMO-{priority.name}",
            event_type="forest_loss_candidate",
            priority=priority,
            confidence=0.8 + (0.04 * (3 - int(priority))),
            location={"latitude": 0.0, "longitude": 0.0},
            detected_at=__import__("datetime").datetime.now(__import__("datetime").UTC),
        )
        for priority in (
            __import__("forestwatch.schemas.events", fromlist=["AlertPriority"]).AlertPriority.CRITICAL,
            __import__("forestwatch.schemas.events", fromlist=["AlertPriority"]).AlertPriority.HIGH,
            __import__("forestwatch.schemas.events", fromlist=["AlertPriority"]).AlertPriority.MEDIUM,
            __import__("forestwatch.schemas.events", fromlist=["AlertPriority"]).AlertPriority.LOW,
        )
    ]


async def run_demo() -> dict[str, object]:
    """Run the priority queue and concurrent shortest-path demonstration."""
    graph = build_default_topology()
    router = PriorityRouter(graph)
    queue = PriorityEventQueue()
    for event in build_demo_events():
        queue.put(event)

    ordered: list[str] = []
    samples: list[DeliverySample] = []
    deliveries: list[dict[str, object]] = []

    while not queue.is_empty():
        event = queue.get()
        ordered.append(event.priority.name)
        start = time.perf_counter()
        results = await deliver_concurrently(event, recipients=RECIPIENTS, router=router)
        latency_ms = (time.perf_counter() - start) * 1000
        samples.append(
            DeliverySample(
                priority=int(event.priority),
                latency_ms=latency_ms,
                delivered=len(results) == len(RECIPIENTS),
            )
        )
        deliveries.append(
            {
                "event_id": event.event_id,
                "priority": event.priority.name,
                "recipients": [result.recipient for result in results],
                "routes": {result.recipient: list(result.path) for result in results},
                "path_costs": {result.recipient: result.path_cost for result in results},
            }
        )

    metrics = calculate_metrics(samples)
    return {
        "ordered_priorities": ordered,
        "deliveries": deliveries,
        "metrics": metrics,
    }
