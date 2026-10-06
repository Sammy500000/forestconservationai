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


## Phase 7 — Final acceptance and research artifact verification

Phase 7 is the finalization gate for the current prototype. It does not add new production infrastructure or live satellite acquisition. It verifies the committed ML, bi-temporal detection, priority-routing, notification, and artifact contracts together.

### Verification

Run:

    python scripts/verify_phase7.py

The verifier runs the repository test suite, Ruff, source compilation, configuration checks, model/detection/network smoke checks, and artifact-directory checks.

Phase 7 deliberately does not require external datasets, model downloads, live Sentinel-2 access, Global Forest Watch access, MQTT network connectivity, or a running Streamlit server. Those are runtime/data integrations and remain outside the final static acceptance gate.

### Research artifact checklist

Before reporting final experimental results, generate and archive the actual run outputs locally (the repository keeps external datasets and generated model/data artifacts out of Git):

    python scripts/evaluate_eurosat.py
    python scripts/run_phase5_demo.py
    streamlit run src/forestwatch/dashboard/app.py

The report should distinguish benchmark classifier performance, Forest-Change bi-temporal candidate detection, and simulated priority-aware message delivery. No generated metric should be interpreted as proof of real-world deforestation without the corresponding external validation experiment.
