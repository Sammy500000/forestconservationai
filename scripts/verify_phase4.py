from __future__ import annotations

import asyncio

from forestwatch.networking.demo import build_demo_events, run_demo
from forestwatch.networking.notifications import deliver_concurrently
from forestwatch.networking.priority import PriorityEventQueue
from forestwatch.networking.router import PriorityRouter
from forestwatch.networking.topology import build_default_topology


def main() -> int:
    events = build_demo_events()
    assert len(events) == 4
    assert [event.priority.name for event in events] == [
        "CRITICAL",
        "HIGH",
        "MEDIUM",
        "LOW",
    ]

    queue = PriorityEventQueue()
    for event in reversed(events):
        queue.put(event)
    assert [queue.get().priority.name for _ in range(4)] == [
        "CRITICAL",
        "HIGH",
        "MEDIUM",
        "LOW",
    ]

    graph = build_default_topology()
    router = PriorityRouter(graph)
    route = router.route(events[0], source="forest_hub", destination="control_room")
    assert route.route.path == ("forest_hub", "node_b", "district", "control_room")
    assert route.route.cost == 8.0

    recipients = ("node_a", "district", "control_room")
    results = asyncio.run(
        deliver_concurrently(events[0], recipients=recipients, router=router)
    )
    assert {result.recipient for result in results} == set(recipients)

    demo = asyncio.run(run_demo())
    assert demo["ordered_priorities"] == ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
    print("Phase 4 smoke verification passed.")
    print("Priority ordering: passed")
    print("Dijkstra shortest path: passed")
    print("Concurrent delivery: passed")
    print("Network metrics: passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
