from datetime import timezone

import pytest
from pydantic import ValidationError

from forestwatch.schemas.events import (
    AlertPriority,
    Coordinates,
    EventType,
    ForestEvent,
)


def test_forest_event_contract() -> None:
    event = ForestEvent.example()

    assert event.priority is AlertPriority.HIGH
    assert event.event_type is EventType.FOREST_LOSS_CANDIDATE
    assert event.detected_at.tzinfo is not None
    assert event.detected_at.astimezone(timezone.utc).tzinfo == timezone.utc


def test_coordinates_are_bounded() -> None:
    with pytest.raises(ValidationError):
        Coordinates(latitude=91, longitude=0)

    with pytest.raises(ValidationError):
        Coordinates(latitude=0, longitude=181)


def test_confidence_is_bounded() -> None:
    with pytest.raises(ValidationError):
        ForestEvent(
            event_id="invalid",
            event_type=EventType.FOREST_LOSS_CANDIDATE,
            priority=AlertPriority.LOW,
            confidence=1.1,
            location=Coordinates(latitude=0, longitude=0),
            detected_at=ForestEvent.example().detected_at,
        )
