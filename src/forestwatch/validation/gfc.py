"""Validation against the Hansen Global Forest Change lossyear raster."""
from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import rasterio
    from pyproj import CRS, Transformer
    from rasterio.coords import BoundingBox
    from rasterio.windows import Window, from_bounds
except ImportError:  # pragma: no cover - optional dependency
    rasterio = None
    CRS = Transformer = None
    BoundingBox = object  # type: ignore[assignment,misc]
    Window = object  # type: ignore[assignment,misc]
    from_bounds = None


@dataclass(frozen=True)
class GFCValidationRecord:
    """GFC evidence measured for one candidate event."""

    event_id: str
    loss_fraction: float
    has_loss: bool
    min_loss_year: int | None
    max_loss_year: int | None
    valid_pixels: int
    loss_pixels: int
    overlaps_raster: bool = True


@dataclass(frozen=True)
class GFCValidationSummary:
    """Aggregate comparison between candidate events and GFC loss evidence."""

    candidate_count: int
    comparable_count: int
    candidates_with_loss: int
    agreement_rate: float
    mean_loss_fraction: float
    records: tuple[GFCValidationRecord, ...]


def _require_geospatial_dependencies() -> None:
    if rasterio is None or from_bounds is None or CRS is None or Transformer is None:
        raise RuntimeError(
            "Phase 8 requires the optional geospatial dependencies. "
            "Install with: python -m pip install -e '.[geospatial]'"
        )


def _transform_bounds(
    bounds: BoundingBox,
    *,
    source_crs: str,
    target_crs: object,
) -> BoundingBox:
    """Transform an axis-aligned bounding box into the raster CRS."""
    _require_geospatial_dependencies()
    source = CRS.from_user_input(source_crs)
    target = CRS.from_user_input(target_crs)
    if source == target:
        return bounds

    transformer = Transformer.from_crs(source, target, always_xy=True)
    corners = (
        (bounds.left, bounds.bottom),
        (bounds.left, bounds.top),
        (bounds.right, bounds.bottom),
        (bounds.right, bounds.top),
    )
    transformed = [transformer.transform(x, y) for x, y in corners]
    xs = [point[0] for point in transformed]
    ys = [point[1] for point in transformed]
    return BoundingBox(min(xs), min(ys), max(xs), max(ys))


def _intersect_window(dataset: Any, window: Window) -> Window | None:
    """Return the intersection with the raster extent, if non-empty."""
    raster_left = 0.0
    raster_top = 0.0
    raster_right = float(dataset.width)
    raster_bottom = float(dataset.height)

    left = max(float(window.col_off), raster_left)
    top = max(float(window.row_off), raster_top)
    right = min(float(window.col_off + window.width), raster_right)
    bottom = min(float(window.row_off + window.height), raster_bottom)

    if right <= left or bottom <= top:
        return None

    return Window(left, top, right - left, bottom - top)


def validate_event_bounds(
    *,
    event_id: str,
    bounds: BoundingBox,
    bounds_crs: str,
    dataset_path: Path,
    threshold: int = 1,
) -> GFCValidationRecord:
    """Read only the GFC raster window intersecting an event footprint."""
    _require_geospatial_dependencies()
    if threshold < 1 or threshold > 24:
        raise ValueError("threshold must be in the GFC lossyear range [1, 24].")

    dataset_path = dataset_path.expanduser().resolve()
    if not dataset_path.is_file():
        raise FileNotFoundError(f"GFC raster not found: {dataset_path}")

    with rasterio.open(dataset_path) as dataset:
        if dataset.crs is None:
            raise ValueError(f"GFC raster has no CRS metadata: {dataset_path}")

        raster_bounds = _transform_bounds(
            bounds,
            source_crs=bounds_crs,
            target_crs=dataset.crs,
        )
        requested_window = from_bounds(
            raster_bounds.left,
            raster_bounds.bottom,
            raster_bounds.right,
            raster_bounds.top,
            transform=dataset.transform,
        )
        window = _intersect_window(dataset, requested_window)
        if window is not None:
            window = window.round_offsets().round_lengths()
        if window is None or window.width <= 0 or window.height <= 0:
            return GFCValidationRecord(
                event_id=event_id,
                loss_fraction=0.0,
                has_loss=False,
                min_loss_year=None,
                max_loss_year=None,
                valid_pixels=0,
                loss_pixels=0,
                overlaps_raster=False,
            )

        data = dataset.read(1, window=window, masked=True)
        if data.size == 0:
            return GFCValidationRecord(
                event_id=event_id,
                loss_fraction=0.0,
                has_loss=False,
                min_loss_year=None,
                max_loss_year=None,
                valid_pixels=0,
                loss_pixels=0,
            )

        values = data.compressed().astype("int16", copy=False)
        valid_pixels = int(values.size)
        if valid_pixels == 0:
            return GFCValidationRecord(
                event_id=event_id,
                loss_fraction=0.0,
                has_loss=False,
                min_loss_year=None,
                max_loss_year=None,
                valid_pixels=0,
                loss_pixels=0,
            )

        loss_values = values[(values >= threshold) & (values <= 24)]
        loss_pixels = int(loss_values.size)
        if loss_pixels == 0:
            return GFCValidationRecord(
                event_id=event_id,
                loss_fraction=0.0,
                has_loss=False,
                min_loss_year=None,
                max_loss_year=None,
                valid_pixels=valid_pixels,
                loss_pixels=0,
            )

        years = loss_values.astype("int16") + 2000
        return GFCValidationRecord(
            event_id=event_id,
            loss_fraction=loss_pixels / valid_pixels,
            has_loss=True,
            min_loss_year=int(years.min()),
            max_loss_year=int(years.max()),
            valid_pixels=valid_pixels,
            loss_pixels=loss_pixels,
        )


def summarize_records(records: Iterable[GFCValidationRecord]) -> GFCValidationSummary:
    """Aggregate event-level GFC agreement statistics over comparable events."""
    record_tuple = tuple(records)
    comparable = tuple(record for record in record_tuple if record.overlaps_raster)
    matched = sum(record.has_loss for record in comparable)
    fractions = [record.loss_fraction for record in comparable]

    return GFCValidationSummary(
        candidate_count=len(record_tuple),
        comparable_count=len(comparable),
        candidates_with_loss=matched,
        agreement_rate=(matched / len(comparable)) if comparable else 0.0,
        mean_loss_fraction=(sum(fractions) / len(fractions)) if fractions else 0.0,
        records=record_tuple,
    )
