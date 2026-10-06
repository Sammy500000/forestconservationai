# Forest Conservation AI

A reproducible, local-first research prototype for satellite-based forest-loss screening and priority-aware early warning.

## Phase 5 status — complete implementation

Phase 5 connects the Phase 3 bi-temporal detection core to the Phase 4 alert-routing layer.

The integrated path is:

`before/after images → 64×64 aligned patches → ResNet50 inference → Forest-to-nonforest candidate detection → ForestEvent → priority-aware routing → concurrent recipient delivery`

### End-to-end entry point

Run:

    python scripts/run_phase5_demo.py

The command uses:

- `data/external/forest_change` as the default input source.
- the public EuroSAT ResNet50 checkpoint configured in `configs/model.yaml`.
- Phase 3 confidence and patch settings from `configs/detection.yaml`.
- the deterministic Phase 4 weighted topology and concurrent notification simulation.

The demo writes:

    artifacts/metrics/phase5_demo.json

The result includes the selected sample, patch-level detection metrics, candidate event metadata, network routes, route costs, notification recipients, and measured local notification latency.

### Expected dataset

Place the Forest-Change benchmark at:

    data/external/forest_change/images/test/A/
    data/external/forest_change/images/test/B/
    data/external/forest_change/images/test/label/

The repository intentionally excludes the external image data from Git.

### Scope

Phase 5 uses in-memory concurrent delivery for a deterministic end-to-end integration test. The existing Phase 4 Paho/Mosquitto adapters remain available for broker-backed integration. Live Sentinel-2 acquisition and external Hansen/GFW validation are intentionally outside the critical path.

## Verification

Run the existing test suite:

    pytest

Run lint:

    python -m ruff check .

Run the Phase 5 integration demo after the Forest-Change dataset is available:

    python scripts/run_phase5_demo.py

## License

MIT. See LICENSE.
