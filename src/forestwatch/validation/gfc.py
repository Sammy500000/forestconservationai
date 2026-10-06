"""Validation against the Hansen Global Forest Change lossyear raster."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

try:
    import rasterio
    from rasterio.coords import BoundingBox
    from rasterio.windows import from_bounds
except ImportError:  # pragma: no cover - optional dependency
    rasterio = None
    BoundingBox = object  # type: ignore[assignment,misc]
    from_bounds = None


@dataclass(frozen=True)
class GFCValidationRecord:
    """GFC evidence measured for one candidate event."""

    event_id: str
    loss_fraction: float
    has_loss: bool
    min_loss_year: int | None
    max_loss_year: int | None


@dataclass(frozen=True)
class GFCValidationSummary:
    """Aggregate comparison between predicted candidate events and GFC loss evidence."""

    candidate_count: int
    candidates_with_loss: int
    agreement_rate: float
    mean_loss_fraction: float
    records: tuple[GFCValidationRecord, ...]


def _require_rasterio() -> None:
    if rasterio is None or from_bounds is None:
        raise RuntimeError(
            "Phase 8 requires the optional geospatial dependencies. "
            "Install with: python -m pip install -e '.[geospatial]'"
        )


def validate_event_bounds(
    *,
    event_id: str,
    bounds: BoundingBox,
    dataset_path: Path,
    threshold: int = 1,
) -> GFCValidationRecord:
    """Read only the raster window overlapping one event bounding box."""
    _require_rasterio()
    if threshold < 1 or threshold > 255:
        raise ValueError("threshold must be in [1, 255]")

    dataset_path = dataset_path.expanduser().resolve()
    if not dataset_path.is_file():
        raise FileNotFoundError(f"GFC raster not found: {dataset_path}")

    with rasterio.open(dataset_path) as dataset:
        window = from_bounds(
            bounds.left,
            bounds.bottom,
            bounds.right,
            bounds.top,
            transform=dataset.transform,
        )
        window = window.round_offsets().round_lengths()
        data = dataset.read(1, window=window, masked=True)

        if data.size == 0:
            return GFCValidationRecord(event_id, 0.0, False, None, None)

        values = data.compressed().astype("int64", copy=False)
        if values.size == 0:
            return GFCValidationRecord(event_id, 0.0, False, None, None)

        loss_values = values[values >= threshold]
        loss_fraction = float(loss_values.size / values.size)
        if loss_values.size == 0:
            return GFCValidationRecord(event_id, loss_fraction, False, None, None)

        # GFC lossyear encodes 2001 as 1 through 2024 as 24.
        years = loss_values[loss_values <= 24] + 2000
        return GFCValidationRecord(
            event_id=event_id,
            loss_fraction=loss_fraction,
            has_loss=True,
            min_loss_year=int(years.min()) if years.size else None,
            max_loss_year=int(years.max()) if years.size else None,
        )


def summarize_records(records: Iterable[GFCValidationRecord]) -> GFCValidationSummary:
    """Aggregate event-level GFC agreement statistics."""
    record_tuple = tuple(records)
    candidate_count = len(record_tuple)
    matched = sum(record.has_loss for record in record_tuple)
    fractions = [record.loss_fraction for record in record_tuple]

    return GFCValidationSummary(
        candidate_count=candidate_count,
        candidates_with_loss=matched,
        agreement_rate=(matched / candidate_count) if candidate_count else 0.0,
        mean_loss_fraction=(sum(fractions) / len(fractions)) if fractions else 0.0,
        records=record_tuple,
    )
