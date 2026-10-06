"""Offline Phase 8 acceptance checks for the Hansen GFC validation layer."""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

try:
    import rasterio
    from rasterio.coords import BoundingBox
    from rasterio.transform import from_origin
except ImportError:  # pragma: no cover
    rasterio = None
    BoundingBox = object  # type: ignore[assignment,misc]
    from_origin = None

from forestwatch.schemas.events import EventBounds, ForestEvent


def run(command: list[str]) -> None:
    print("$", " ".join(command))
    subprocess.run(command, check=True)


def verify_event_schema() -> None:
    event = ForestEvent(
        event_id="PHASE8-SMOKE",
        event_type="forest_loss_candidate",
        priority=1,
        confidence=0.95,
        location={"latitude": 1.0, "longitude": 2.0},
        detected_at="2026-01-01T00:00:00Z",
        bounds=EventBounds(
            left=10.0,
            bottom=20.0,
            right=11.0,
            top=21.0,
            crs="EPSG:4326",
        ),
    )
    assert event.bounds is not None
    assert event.bounds.crs == "EPSG:4326"


def verify_synthetic_raster() -> None:
    if rasterio is None or from_origin is None:
        raise RuntimeError(
            "Phase 8 verification requires rasterio. Install with: "
            "python -m pip install -e '.[geospatial]'"
        )

    from forestwatch.validation.gfc import validate_event_bounds

    with tempfile.TemporaryDirectory(prefix="forestwatch-phase8-") as tmp:
        raster_path = Path(tmp) / "lossyear.tif"
        data = np.array([[0, 0, 4, 0], [0, 24, 0, 0], [1, 0, 0, 0], [0, 0, 0, 2]], dtype=np.uint8)
        with rasterio.open(
            raster_path,
            "w",
            driver="GTiff",
            height=4,
            width=4,
            count=1,
            dtype=data.dtype,
            crs="EPSG:4326",
            transform=from_origin(0, 4, 1, 1),
        ) as dataset:
            dataset.write(data, 1)

        record = validate_event_bounds(
            event_id="PHASE8-SMOKE",
            bounds=BoundingBox(0, 2, 2, 4),
            bounds_crs="EPSG:4326",
            dataset_path=raster_path,
        )
        assert record.overlaps_raster
        assert record.valid_pixels == 4
        assert record.loss_pixels == 1
        assert record.loss_fraction == 0.25
        assert record.min_loss_year == 2024
        assert record.max_loss_year == 2024


def main() -> int:
    run([sys.executable, "-m", "pytest"])
    run([sys.executable, "-m", "ruff", "check", "."])
    run([sys.executable, "-m", "compileall", "-q", "src"])
    verify_event_schema()
    verify_synthetic_raster()
    print("Phase 8 acceptance verification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
