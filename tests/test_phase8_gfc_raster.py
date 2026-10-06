from __future__ import annotations

from pathlib import Path

import pytest

from forestwatch.validation.gfc import validate_event_bounds


@pytest.fixture
def geospatial_modules():
    rasterio = pytest.importorskip("rasterio")
    from rasterio.coords import BoundingBox
    from rasterio.transform import from_origin

    return rasterio, BoundingBox, from_origin


def test_validate_event_bounds_reads_lossyear_window(tmp_path: Path, geospatial_modules) -> None:
    import numpy as np

    rasterio, BoundingBox, from_origin = geospatial_modules
    path = tmp_path / "lossyear.tif"
    data = np.array(
        [
            [0, 0, 1, 2],
            [0, 24, 0, 3],
            [4, 0, 0, 0],
            [0, 0, 5, 6],
        ],
        dtype=np.uint8,
    )

    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        height=data.shape[0],
        width=data.shape[1],
        count=1,
        dtype=data.dtype,
        crs="EPSG:4326",
        transform=from_origin(0, 4, 1, 1),
    ) as dataset:
        dataset.write(data, 1)

    record = validate_event_bounds(
        event_id="EVT-001",
        bounds=BoundingBox(0, 2, 2, 4),
        bounds_crs="EPSG:4326",
        dataset_path=path,
    )

    assert record.overlaps_raster is True
    assert record.valid_pixels == 4
    assert record.loss_pixels == 1
    assert record.loss_fraction == pytest.approx(0.25)
    assert record.has_loss is True
    assert record.min_loss_year == 2024
    assert record.max_loss_year == 2024


def test_validate_event_bounds_transforms_crs(tmp_path: Path, geospatial_modules) -> None:
    import numpy as np

    rasterio, BoundingBox, from_origin = geospatial_modules
    path = tmp_path / "lossyear.tif"
    data = np.ones((2, 2), dtype=np.uint8)

    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        height=2,
        width=2,
        count=1,
        dtype=data.dtype,
        crs="EPSG:3857",
        transform=from_origin(0, 200000, 100000, 100000),
    ) as dataset:
        dataset.write(data, 1)

    record = validate_event_bounds(
        event_id="EVT-CRS",
        bounds=BoundingBox(0, 0, 1.5, 1.5),
        bounds_crs="EPSG:4326",
        dataset_path=path,
    )

    assert record.overlaps_raster is True
    assert record.has_loss is True
    assert record.loss_fraction == pytest.approx(1.0)


def test_validate_event_bounds_outside_raster_is_not_comparable(
    tmp_path: Path,
    geospatial_modules,
) -> None:
    import numpy as np

    rasterio, BoundingBox, from_origin = geospatial_modules
    path = tmp_path / "lossyear.tif"
    data = np.zeros((1, 1), dtype=np.uint8)

    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        height=1,
        width=1,
        count=1,
        dtype=data.dtype,
        crs="EPSG:4326",
        transform=from_origin(0, 1, 1, 1),
    ) as dataset:
        dataset.write(data, 1)

    record = validate_event_bounds(
        event_id="EVT-OUTSIDE",
        bounds=BoundingBox(10, 10, 11, 11),
        bounds_crs="EPSG:4326",
        dataset_path=path,
    )

    assert record.overlaps_raster is False
    assert record.valid_pixels == 0
    assert record.loss_pixels == 0


def test_validate_event_bounds_missing_file(tmp_path: Path, geospatial_modules) -> None:
    _, BoundingBox, _ = geospatial_modules

    with pytest.raises(FileNotFoundError, match="GFC raster not found"):
        validate_event_bounds(
            event_id="EVT-MISSING",
            bounds=BoundingBox(0, 0, 1, 1),
            bounds_crs="EPSG:4326",
            dataset_path=tmp_path / "missing.tif",
        )


def test_validate_event_bounds_rejects_invalid_threshold(
    tmp_path: Path,
    geospatial_modules,
) -> None:
    import numpy as np

    rasterio, BoundingBox, from_origin = geospatial_modules
    path = tmp_path / "lossyear.tif"
    data = np.zeros((1, 1), dtype=np.uint8)

    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        height=1,
        width=1,
        count=1,
        dtype=data.dtype,
        crs="EPSG:4326",
        transform=from_origin(0, 1, 1, 1),
    ) as dataset:
        dataset.write(data, 1)

    with pytest.raises(ValueError, match="lossyear range"):
        validate_event_bounds(
            event_id="EVT-THRESHOLD",
            bounds=BoundingBox(0, 0, 1, 1),
            bounds_crs="EPSG:4326",
            dataset_path=path,
            threshold=25,
        )
