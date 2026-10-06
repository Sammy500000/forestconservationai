# Forest Conservation AI

A reproducible, local-first research prototype for satellite-based forest-loss screening and priority-aware early warning.

## Current project status

Phases 1–7 are complete. Phase 8 adds an optional external validation path against the official Hansen Global Forest Change (GFC) 2000–2024 v1.12 `lossyear` raster.

The reference design uses two-date land-cover classification to flag forest-to-nonforest transitions. The supplied project abstract additionally calls for priority-aware publish/subscribe messaging, shortest-path delivery, and concurrent notifications. Those core prototype components remain unchanged by Phase 8.

## Phase 8 — Hansen GFC validation

Phase 8 compares generated ForestWatch candidate events against the Hansen GFC `lossyear` raster. The validator is deliberately local-first: it does not depend on the Global Forest Watch web application or API and it does not download the global GFC archive automatically.

Hansen GFC v1.12 covers global forest-cover change from 2000 through 2024. Its `lossyear` layer encodes stand-replacement forest loss as 0 for no loss or 1–24 for loss primarily detected in 2001–2024. The data are approximately 30 m per pixel. See the official download page:

    https://storage.googleapis.com/earthenginepartners-hansen/GFC-2024-v1.12/download.html

### Install

Install the optional geospatial dependencies:

    python -m pip install -e ".[geospatial]"

### Prepare the raster

Download only the GFC `lossyear` granule covering the study area from the official page and put it under:

    data/external/gfc/

GFC raster files are intentionally excluded from Git because the global archive is large.

### Run validation

    python scripts/validate_against_gfc.py \
      --detections artifacts/metrics/phase5_demo.json \
      --gfc data/external/gfc/<lossyear>.tif

The command writes:

    artifacts/metrics/phase8_gfc_validation.json

### Important data-contract limitation

The existing Phase 5 event schema records latitude/longitude and patch row/column, but it does not yet encode a CRS-aware geographic bounding box for each candidate. Because of that, the Phase 8 CLI intentionally refuses to manufacture raster coordinates from latitude/longitude alone.

This keeps the validation scientifically safe: a GFC overlap percentage must not be reported unless the event geometry can be transformed into the GFC raster CRS correctly.

The geospatial validator itself already supports a raster bounding box and reads only the intersecting raster window, so a future CRS-aware event geometry adapter can be added without redesigning the validation core.

### Scientific interpretation

GFC `lossyear` is a forest-loss/stand-replacement disturbance reference. A match means that the candidate overlaps GFC forest-loss evidence. It does not by itself establish that the cause was illegal logging, mining, encroachment, or another specific activity.

## Verification

Run:

    pytest
    python -m ruff check .
    python -m compileall -q src

Phase 8 also has deterministic unit tests in:

    tests/test_phase8_gfc.py

These tests do not require external raster data or network access.

## Scope boundary

Phase 8 does not change the existing ML model, Forest-Change detector, MQTT routing, or Streamlit dashboard behavior. Live Sentinel-2 acquisition remains an optional future enhancement.

## License

MIT. See LICENSE.

## Earlier phase documentation

### Phase 6 — Dashboard

The Streamlit dashboard reads generated Phase 2–5 artifacts only. Run:

    python -m pip install -e ".[dashboard]"
    streamlit run src/forestwatch/dashboard/app.py

### Phase 7 — Final acceptance

Run:

    python scripts/verify_phase7.py

The Phase 7 gate checks tests, Ruff, source compilation, configuration coherence, model/detection/network smoke checks, and artifact directories. It deliberately does not require external datasets, model downloads, live Sentinel-2/Hansen/GFW access, MQTT connectivity, or a running Streamlit server.
