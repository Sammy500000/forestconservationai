from __future__ import annotations

import asyncio

import pytest

pytest.importorskip("networkx")

from forestwatch.networking.demo import build_demo_events
from forestwatch.networking.metrics import DeliverySample, calculate_metrics
from forestwatch.networking.notifications import deliver_concurrently
from forestwatch.networking.priority import PriorityEventQueue
from forestwatch.networking.router import PriorityRouter
from forestwatch.networking.topology import build_default_topology, shortest_route
from forestwatch.schemas.events import AlertPriority


def test_priority_queue_orders_critical_to_low() -> None:
    queue = PriorityEventQueue()
    for event in reversed(build_demo_events()):
        queue.put(event)
    assert [queue.get().priority for _ in range(4)] == [
        AlertPriority.CRITICAL,
        AlertPriority.HIGH,
        AlertPriority.MEDIUM,
        AlertPriority.LOW,
    ]


def test_priority_queue_is_stable_with_equal_priority() -> None:
    queue = PriorityEventQueue()
    events = build_demo_events()
    high = [event for event in events if event.priority is AlertPriority.HIGH][0]
    queue.put(high.model_copy(update={"event_id": "first"}))
    queue.put(high.model_copy(update={"event_id": "second"}))
    assert queue.get().event_id == "first"
    assert queue.get().event_id == "second"


def test_default_topology_has_expected_nodes_and_edges() -> None:
    graph = build_default_topology()
    assert set(graph.nodes) == {
        "forest_hub",
        "node_a",
        "node_b",
        "village_a",
        "district",
        "control_room",
    }
    assert graph["forest_hub"]["node_a"]["weight"] == 2.0


def test_dijkstra_route_is_minimum_weight() -> None:
    graph = build_default_topology()
    route = shortest_route(graph, "forest_hub", "control_room")
    assert route.path == ("forest_hub", "node_b", "district", "control_room")
    assert route.cost == pytest.approx(8.0)


def test_concurrent_delivery_reaches_all_recipients() -> None:
    graph = build_default_topology()
    router = PriorityRouter(graph)
    event = build_demo_events()[0]
    results = asyncio.run(
        deliver_concurrently(
            event,
            recipients=("node_a", "district", "control_room"),
            router=router,
        )
    )
    assert {result.recipient for result in results} == {
        "node_a",
        "district",
        "control_room",
    }
    assert all(result.path[0] == "forest_hub" for result in results)


def test_metrics_calculation() -> None:
    metrics = calculate_metrics(
        [
            DeliverySample(priority=0, latency_ms=10.0),
            DeliverySample(priority=3, latency_ms=30.0),
        ]
    )
    assert metrics.sample_count == 2
    assert metrics.delivery_rate == 1.0
    assert metrics.mean_latency_ms == pytest.approx(20.0)
    assert metrics.critical_mean_latency_ms == pytest.approx(10.0)


def test_demo_events_cover_all_priorities() -> None:
    assert [event.priority for event in build_demo_events()] == list(AlertPriority)
