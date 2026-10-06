"""End-to-end event routing and local MQTT helpers."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from queue import Empty, Queue
from threading import Event, Lock, Thread

from forestwatch.networking.mqtt import MQTTConfig, MQTTPublisher, MQTTSubscriber
from forestwatch.networking.router import PriorityRouter
from forestwatch.networking.topology import build_default_topology
from forestwatch.schemas.events import ForestEvent


@dataclass(frozen=True)
class RoutedNotification:
    """One routed notification produced from an alert event."""

    event_id: str
    recipient: str
    path: tuple[str, ...]
    path_cost: float
    delivered_at: datetime


def route_event_to_recipients(
    event: ForestEvent,
    *,
    recipients: tuple[str, ...],
    router: PriorityRouter | None = None,
    source: str = "forest_hub",
) -> list[RoutedNotification]:
    """Compute a route for every recipient."""
    active_router = router or PriorityRouter(build_default_topology())
    now = datetime.now(UTC)
    routed: list[RoutedNotification] = []
    for recipient in recipients:
        route = active_router.route(event, source=source, destination=recipient).route
        routed.append(
            RoutedNotification(
                event_id=event.event_id,
                recipient=recipient,
                path=route.path,
                path_cost=route.cost,
                delivered_at=now,
            )
        )
    return routed


class InMemorySubscriber:
    """Thread-safe recipient sink for the deterministic end-to-end demo."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.received: list[ForestEvent] = []
        self._lock = Lock()

    def receive(self, event: ForestEvent) -> None:
        with self._lock:
            self.received.append(event)


def deliver_in_memory_concurrently(
    event: ForestEvent,
    *,
    recipients: tuple[str, ...],
    router: PriorityRouter | None = None,
) -> list[RoutedNotification]:
    """Fan one event out concurrently to all recipients."""
    if not recipients:
        return []

    active_router = router or PriorityRouter(build_default_topology())
    sinks = {name: InMemorySubscriber(name) for name in recipients}
    barrier = Event()
    completed: Queue[RoutedNotification] = Queue()

    def worker(recipient: str) -> None:
        route = active_router.route(
            event,
            source="forest_hub",
            destination=recipient,
        ).route
        barrier.wait()
        result = RoutedNotification(
            event_id=event.event_id,
            recipient=recipient,
            path=route.path,
            path_cost=route.cost,
            delivered_at=datetime.now(UTC),
        )
        sinks[recipient].receive(event)
        completed.put(result)

    threads = [
        Thread(target=worker, args=(recipient,), daemon=True)
        for recipient in recipients
    ]
    for thread in threads:
        thread.start()
    barrier.set()
    for thread in threads:
        thread.join(timeout=5.0)

    results: list[RoutedNotification] = []
    while True:
        try:
            results.append(completed.get_nowait())
        except Empty:
            break

    if len(results) != len(recipients):
        raise RuntimeError("One or more concurrent notification workers did not complete.")

    return results


def publish_event(
    event: ForestEvent,
    *,
    config: MQTTConfig | None = None,
) -> float:
    """Publish one event and return publish elapsed time in milliseconds."""
    publisher = MQTTPublisher(config or MQTTConfig())
    started = __import__("time").perf_counter()
    try:
        publisher.connect()
        publisher.publish(event)
        return (__import__("time").perf_counter() - started) * 1000
    finally:
        publisher.close()


def subscribe_once(
    *,
    client_id: str,
    config: MQTTConfig | None = None,
) -> MQTTSubscriber:
    """Connect a subscriber and return it with its background loop running."""
    subscriber = MQTTSubscriber(config or MQTTConfig(), client_id)
    subscriber.connect()
    return subscriber
