# Phase 8 — Hansen Global Forest Change Validation

Phase 8 adds an optional, local-first external validation path. It compares georeferenced ForestWatch candidate events against the official Hansen Global Forest Change (GFC) 2000–2024 v1.12 `lossyear` raster.

## What Phase 8 adds

- CRS-aware event footprints via optional `ForestEvent.bounds`.
- A Rasterio-based GFC adapter that reads only the raster window needed for each event.
- CRS transformation with PyProj when event and raster CRS differ.
- Per-event loss fraction and loss-year range.
- Aggregate GFC agreement rate over spatially comparable events.
- Offline synthetic GeoTIFF tests and an acceptance verifier.
- A command-line validator for real GFC rasters.

The existing Phase 2–7 ML, detection, networking, and dashboard paths are not replaced.

## Data source

Use the official Hansen Global Forest Change v1.12 2000–2024 `lossyear` product:

    https://storage.googleapis.com/earthenginepartners-hansen/GFC-2024-v1.12/download.html

The `lossyear` band uses 0 for no mapped loss and 1–24 for loss years 2001–2024. GFC pixels are approximately 30 m.

Download only the tile(s) needed for the area represented by your georeferenced candidate events. Do not commit the raster to Git.

Place local rasters under:

    data/external/gfc/

## Required event geometry

GFC comparison is a spatial operation. A latitude/longitude point and a patch row/column are not enough to identify the patch footprint in a raster.

Phase 8 therefore adds this optional event field:

    bounds:
      left: ...
      bottom: ...
      right: ...
      top: ...
      crs: "EPSG:4326"

The validator transforms these bounds into the GFC raster CRS before reading the overlapping pixels.

The existing benchmark Phase 5 demo uses non-georeferenced Forest-Change images and placeholder coordinates, so its artifact cannot be truthfully compared to a real GFC raster until a geospatial event producer supplies real event bounds.

## Install

    python -m pip install -e ".[geospatial]"

## Offline acceptance verification

This requires only the local optional geospatial dependencies and synthetic data:

    python scripts/verify_phase8.py

The verifier runs the full test suite, Ruff, source compilation, event-schema checks, and a synthetic GFC GeoTIFF validation.

## Real GFC validation

After generating an artifact whose candidate events contain real `bounds`:

    python scripts/validate_against_gfc.py \
      --detections artifacts/metrics/georeferenced_detections.json \
      --gfc data/external/gfc/<lossyear>.tif

Output:

    artifacts/metrics/phase8_gfc_validation.json

The result reports:

- candidate event count
- spatially comparable event count
- candidates overlapping GFC loss evidence
- agreement rate
- mean GFC loss fraction
- loss-year range per event

## Interpretation

The reported agreement rate is an overlap/agreement statistic. It is not a precision, recall, or accuracy estimate for the full GFC map because the validator is evaluating predicted candidate events against the presence of GFC loss evidence inside those event footprints.

A GFC match means that the candidate overlaps mapped forest-loss/stand-replacement disturbance. It does not establish the cause of the loss or prove illegal logging, mining, or encroachment.

## Scope boundary

Phase 8 does not require:

- the Global Forest Watch web application or API
- the full global GFC archive
- live Sentinel-2 acquisition
- a database
- a cloud deployment

Those can remain future integrations.