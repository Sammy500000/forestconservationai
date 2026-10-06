"""Forest-loss candidate detection from aligned two-date model predictions."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ChangePrediction:
    """Model outputs for two dates corresponding to one spatial patch."""

    before_class: str
    before_confidence: float
    after_class: str
    after_confidence: float


@dataclass(frozen=True)
class CandidateChange:
    """A patch classified as a candidate forest-loss event."""

    row: int
    column: int
    before_class: str
    after_class: str
    confidence: float


def is_forest_loss_candidate(
    prediction: ChangePrediction,
    *,
    forest_class: str = "Forest",
    target_non_forest_classes: tuple[str, ...] = (
        "AnnualCrop",
        "Pasture",
        "Industrial",
        "Residential",
    ),
    confidence_threshold: float = 0.70,
) -> bool:
    """Apply the project reference's forest-to-target-nonforest rule."""
    if not 0 <= confidence_threshold <= 1:
        raise ValueError("confidence_threshold must be in [0, 1]")
    return (
        prediction.before_class == forest_class
        and prediction.after_class in target_non_forest_classes
        and prediction.before_confidence >= confidence_threshold
        and prediction.after_confidence >= confidence_threshold
    )


def build_candidate_change(
    prediction: ChangePrediction,
    *,
    row: int,
    column: int,
    forest_class: str = "Forest",
    target_non_forest_classes: tuple[str, ...] = (
        "AnnualCrop",
        "Pasture",
        "Industrial",
        "Residential",
    ),
    confidence_threshold: float = 0.70,
) -> CandidateChange | None:
    """Create a candidate record when the change rule is satisfied."""
    if not is_forest_loss_candidate(
        prediction,
        forest_class=forest_class,
        target_non_forest_classes=target_non_forest_classes,
        confidence_threshold=confidence_threshold,
    ):
        return None
    return CandidateChange(
        row=row,
        column=column,
        before_class=prediction.before_class,
        after_class=prediction.after_class,
        confidence=min(prediction.before_confidence, prediction.after_confidence),
    )
