"""Concurrent notification simulation for ForestWatch recipients."""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import UTC, datetime

from forestwatch.networking.router import PriorityRouter
from forestwatch.schemas.events import ForestEvent


@dataclass(frozen=True)
class NotificationResult:
    """Delivery result for one recipient."""

    event_id: str
    recipient: str
    delivered_at: datetime
    path: tuple[str, ...]
    path_cost: float


async def deliver_one(
    event: ForestEvent,
    *,
    recipient: str,
    router: PriorityRouter,
    source: str = "forest_hub",
) -> NotificationResult:
    """Route and deliver one notification without blocking other recipients."""
    routed = router.route(event, source=source, destination=recipient)
    await asyncio.sleep(0)
    return NotificationResult(
        event_id=event.event_id,
        recipient=recipient,
        delivered_at=datetime.now(UTC),
        path=routed.route.path,
        path_cost=routed.route.cost,
    )


async def deliver_concurrently(
    event: ForestEvent,
    *,
    recipients: tuple[str, ...],
    router: PriorityRouter,
    source: str = "forest_hub",
) -> list[NotificationResult]:
    """Deliver one event concurrently to all configured recipients."""
    return await asyncio.gather(
        *(deliver_one(event, recipient=name, router=router, source=source) for name in recipients)
    )
