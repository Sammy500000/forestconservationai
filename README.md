# Forest Conservation AI

A reproducible, local-first research prototype for satellite-based forest-loss screening and priority-aware early warning.

## Phase 6 status — complete implementation

Phase 6 adds a minimal Streamlit presentation layer over the generated Phase 2–5 research artifacts.

The dashboard displays:

- EuroSAT model accuracy, macro precision, macro recall, macro F1, and confusion matrix.
- Forest-Change before/after imagery, recorded ground-truth and prediction masks, and patch-level detection metrics.
- Alert event ID, confidence, priority, tile coordinates, and location.
- Shortest route, route cost, delivery status, and measured notification latency.

The dashboard does not run inference, change detection, routing, persistence, authentication, or network APIs. It reads generated JSON artifacts and the existing Forest-Change images only.

### Dashboard entry point

Install the dashboard extra:

    python -m pip install -e ".[dashboard]"

Run:

    streamlit run src/forestwatch/dashboard/app.py

By default the dashboard reads:

    artifacts/metrics/eurosat_metrics.json
    artifacts/metrics/phase5_demo.json
    data/external/forest_change

The sidebar allows these paths to be changed without modifying code.

### Generate the displayed artifacts

Generate EuroSAT evaluation metrics:

    python scripts/evaluate_eurosat.py

Generate the Phase 5 end-to-end results after the Forest-Change dataset is available:

    python scripts/run_phase5_demo.py

The repository intentionally excludes external image datasets from Git.

## Verification

Run the existing test suite:

    pytest

Run lint:

    python -m ruff check .

Run the Phase 5 integration demo after the Forest-Change dataset is available:

    python scripts/run_phase5_demo.py

Run the Phase 6 dashboard:

    streamlit run src/forestwatch/dashboard/app.py

## Scope

Phases 1–5 provide the model, bi-temporal detection, priority-aware networking, and end-to-end event integration. Phase 6 is presentation-only. React, FastAPI, authentication, a database, REST APIs, and live Sentinel-2/Hansen/GFW acquisition are outside the Phase 6 critical path.

## License

MIT. See LICENSE.
