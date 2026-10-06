# Phase 9 — Final Reproducibility and Submission Package

Phase 9 is the completion gate after the implemented prototype phases. It does not add new application features. It packages the existing ML, bi-temporal detection, networking, dashboard, and GFC validation work into a repeatable research run.

## Objectives

- provide one documented clean-run sequence
- centralize the final artifact set
- record environment and project metadata
- verify tests, lint, compilation, and existing phase gates
- avoid requiring external data/model downloads for the acceptance gate
- distinguish generated research results from optional runtime integrations

## Mandatory acceptance commands

    python -m pytest
    python -m ruff check .
    python -m compileall -q src
    python scripts/verify_phase7.py
    python scripts/verify_phase8.py

The Phase 8 verifier requires the optional geospatial dependencies. Install them with:

    python -m pip install -e ".[geospatial]"

## Optional runtime checks

When the external Forest-Change dataset and model access are available:

    python scripts/evaluate_eurosat.py
    python scripts/run_phase5_demo.py

When a real GFC lossyear raster and geospatial event bounds are available:

    python scripts/validate_against_gfc.py \
      --detections artifacts/metrics/georeferenced_detections.json \
      --gfc data/external/gfc/<lossyear>.tif

The GFC comparison is an overlap/agreement statistic, not a full-map accuracy estimate.

## Final artifact package

Keep generated files local unless they are intentionally small and useful for publication:

    artifacts/
      metrics/
      figures/

Recommended final evidence:

- EuroSAT classification metrics and confusion matrix
- bi-temporal forest-change detection metrics
- representative before/after/change figures
- priority-order and shortest-path networking measurements
- concurrent notification measurements
- GFC validation output when a georeferenced run exists

## Reproducibility rules

- Do not commit downloaded image datasets, model checkpoints, or large GFC rasters.
- Record the exact configuration values used for the final run.
- Record dataset source and revision/commit where practical.
- Do not invent geospatial coordinates for benchmark images that have no geospatial metadata.
- Do not describe GFC overlap as proof of illegal activity.
- Do not claim real-time satellite monitoring unless the optional live Sentinel-2 path is actually executed.
- Do not report benchmark classifier accuracy as deforestation-detection accuracy.

## Completion definition

Phase 9 is complete when the repository passes the mandatory acceptance commands, the final artifacts are generated or explicitly unavailable because an external runtime dependency was not used, and the README documents the final reproducible sequence.

No new model architecture, API, database, cloud deployment, or live satellite integration is required to close Phase 9.

