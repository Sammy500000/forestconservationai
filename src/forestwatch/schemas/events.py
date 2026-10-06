from __future__ import annotations

from datetime import UTC, datetime
from enum import IntEnum, StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator


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


class EventBounds(BaseModel):
    """Axis-aligned event footprint with an explicit coordinate reference system."""

    model_config = ConfigDict(extra="forbid")

    left: float
    bottom: float
    right: float
    top: float
    crs: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_extent(self) -> EventBounds:
        if self.left >= self.right:
            raise ValueError("bounds.left must be smaller than bounds.right")
        if self.bottom >= self.top:
            raise ValueError("bounds.bottom must be smaller than bounds.top")
        return self


class ForestEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_id: str = Field(min_length=1)
    event_type: EventType
    priority: AlertPriority
    confidence: float = Field(ge=0, le=1)
    location: Coordinates
    detected_at: datetime
    before_class: str | None = None
    after_class: str | None = None
    sample_id: str | None = None
    patch_row: int | None = Field(default=None, ge=0)
    patch_column: int | None = Field(default=None, ge=0)
    bounds: EventBounds | None = None

    @classmethod
    def example(cls) -> ForestEvent:
        return cls(
            event_id="PHASE1-EXAMPLE-0001",
            event_type=EventType.FOREST_LOSS_CANDIDATE,
            priority=AlertPriority.HIGH,
            confidence=0.90,
            location=Coordinates(latitude=0.0, longitude=0.0),
            detected_at=datetime.now(UTC),
        )
