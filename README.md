# Forest Conservation AI

A reproducible, local-first research prototype for satellite-based forest-loss screening and priority-aware early warning.

## Current project status

Phases 1–8 are complete. Phase 9 is the final reproducibility and submission gate.

The reference design uses two-date land-cover classification to flag forest-to-nonforest transitions. The supplied project abstract additionally calls for priority-aware publish/subscribe messaging, shortest-path delivery, and concurrent notifications.

## Phase 9 — Final reproducibility and submission package

Phase 9 does not add new application features. It verifies and documents the existing prototype so that the project can be reproduced and presented consistently.

See:

    docs/phase-9-plan.md

### Mandatory acceptance commands

    python -m pytest
    python -m ruff check .
    python -m compileall -q src
    python scripts/verify_phase7.py
    python scripts/verify_phase8.py

The Phase 9 completion gate runs the same checks through:

    python scripts/verify_phase9.py

Phase 8 verification requires:

    python -m pip install -e ".[geospatial]"

### Runtime research runs

When the external datasets/model are available:

    python scripts/evaluate_eurosat.py
    python scripts/run_phase5_demo.py

For real Hansen GFC validation, use the Phase 8 CLI with candidate events that contain real CRS-aware bounds.

### Final artifact locations

Generated research outputs belong under:

    artifacts/metrics/
    artifacts/figures/

Do not commit downloaded image datasets, model checkpoints, or large GFC rasters.

### Scientific interpretation

EuroSAT classifier performance, bi-temporal Forest-Change detection performance, networking performance, and GFC overlap are separate measurements. Benchmark accuracy must not be presented as deforestation-detection accuracy.

A GFC overlap indicates mapped forest-loss evidence within a candidate footprint. It does not establish illegal logging, mining, encroachment, or another specific cause.

Live Sentinel-2 acquisition remains an optional future enhancement and is not required to close the prototype.

## License

MIT. See LICENSE.
