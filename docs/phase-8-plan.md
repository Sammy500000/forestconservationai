# Phase 8 — Hansen Global Forest Change Validation

## Objective

Add an optional, local-first validation layer that compares ForestWatch's candidate forest-loss patches/events against the official Hansen Global Forest Change (GFC) 2000–2024 v1.12 `lossyear` layer.

The existing project already has a working benchmark change detector and dashboard. Phase 8 must not replace or alter that critical path.

## Scope

- Input: existing Phase 5/7 detection JSON artifact plus a user-provided local GFC `lossyear` GeoTIFF.
- GFC source: official Hansen GFC 2024 v1.12.
- Processing: geospatially align candidate patches to the GFC raster and calculate whether/what fraction of each patch intersects a non-zero loss-year pixel.
- Output: per-patch validation records and aggregate precision/recall/F1-style overlap statistics.
- No online GFW API dependency.
- No full global GFC download.
- No database.
- No live Sentinel-2 acquisition.
- No change to the existing Phase 5/6 demo behavior.

## Important limitation

GFC `lossyear` identifies forest-cover loss/stand-replacement disturbance, not the cause of that loss. Therefore the result must be described as agreement with GFC forest-loss evidence, not proof of illegal deforestation.

## Data handling

Users download only the GFC granule covering their study area from the official v1.12 download page and place it under `data/external/gfc/`. GFC files are intentionally excluded from Git.

Expected file example:

`data/external/gfc/Hansen_GFC-2024-v1.12_lossyear_<tile>.tif`

The implementation should also accept an arbitrary local path via CLI.

## Proposed commands

```bash
python scripts/validate_against_gfc.py \
  --detections artifacts/metrics/phase5_demo.json \
  --gfc data/external/gfc/<lossyear>.tif \
  --output artifacts/metrics/phase8_gfc_validation.json
```

## Acceptance criteria

1. Existing `pytest` and Ruff checks remain green.
2. The validator handles a missing GFC file with a clear actionable message.
3. Raster CRS/transform are read from metadata; no hard-coded CRS is assumed.
4. Candidate patch bounds are derived from the patch grid and configured source resolution when geographic bounds are available.
5. The validator reports per-event GFC loss coverage and aggregate agreement metrics.
6. A deterministic synthetic raster/unit-test path exists, so CI does not require external GFC data.
7. README explains the official GFC source, licensing/data provenance, local download requirement, and scientific limitation.
8. Dashboard remains unchanged unless the validation artifact is present; when present, it may display a small validation summary.

## Implementation order

1. Add a small GFC raster adapter.
2. Add patch-to-raster overlap calculation.
3. Add aggregate metrics.
4. Add CLI.
5. Add synthetic tests.
6. Add documentation.
7. Run tests + Ruff + compileall.
