from __future__ import annotations

from datetime import datetime, timezone
from enum import IntEnum, StrEnum

from pydantic import BaseModel, ConfigDict, Field


class AlertPriority(IntEnum):
    CRITICAL = 0
    HIGH = 1
    MEDIUM = 2
    LOW = 3


class EventType(StrEnum):
    FOREST_LOSS_CANDIDATE = "forest_loss_candidate"


class Coordinates(BaseModel):
    model_config = ConfigDict(extra="forbid")

    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


class ForestEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_id: str = Field(min_length=1)
    event_type: EventType
    priority: AlertPriority
    confidence: float = Field(ge=0, le=1)
    location: Coordinates
    detected_at: datetime

    @classmethod
    def example(cls) -> "ForestEvent":
        return cls(
            event_id="PHASE1-EXAMPLE-0001",
            event_type=EventType.FOREST_LOSS_CANDIDATE,
            priority=AlertPriority.HIGH,
            confidence=0.90,
            location=Coordinates(latitude=0.0, longitude=0.0),
            detected_at=datetime.now(timezone.utc),
        )
