# Forest Conservation AI

A local-first research prototype for satellite-image land-cover classification, bi-temporal forest-change screening, priority-aware event delivery, and optional validation against the Hansen Global Forest Change dataset.

[![CI](https://github.com/Sammy500000/forestconservationai/actions/workflows/ci.yml/badge.svg)](https://github.com/Sammy500000/forestconservationai/actions/workflows/ci.yml)

## Project status

The implementation is complete for the current nine-phase project scope.

The repository contains:

- EuroSAT land-cover classification using ResNet50
- Bi-temporal forest-change candidate detection
- Priority-aware event queues
- Shortest-path routing with NetworkX
- Concurrent event notification delivery
- A health endpoint for the application service
- Optional Hansen Global Forest Change (GFC) validation
- Offline acceptance checks and reproducibility tooling
- Docker and Docker Compose configuration
- Automated CI checks

This is a research and demonstration system. It is not a production deforestation-monitoring service and does not provide live satellite ingestion by default.

## How the system is structured

The main processing path is:

```
Satellite / benchmark imagery
        |
        v
Land-cover classification
        |
        v
Bi-temporal change screening
        |
        v
Forest-loss candidate event
        |
        v
Priority queue
        |
        v
Network routing
        |
        v
Concurrent notifications
        |
        v
Optional GFC spatial validation
```

The ML benchmark and the GFC validation layer measure different things. EuroSAT classification accuracy must not be reported as deforestation-detection accuracy.

## Repository layout

```
.
├── configs/                 # Model, detection and networking configuration
├── data/
│   └── external/            # Local datasets; large downloads are not committed
├── docs/                    # Phase and reproducibility documentation
├── models/                  # Local model/cache files; not committed
├── scripts/                 # Evaluation, demo and verification commands
├── src/forestwatch/         # Application and library code
├── tests/                   # Automated tests
├── artifacts/
│   ├── metrics/             # Generated JSON/CSV metrics
│   └── figures/             # Generated plots and figures
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
└── README.md
```

## Requirements

- Python 3.12 recommended
- Python 3.13 is also supported by the package metadata, but the CI/reference environment uses Python 3.12
- Git
- Docker Desktop, if using the containerized setup

The full development environment uses:

- PyTorch / torchvision
- Hugging Face Hub
- scikit-learn
- NetworkX
- Paho MQTT
- Rasterio / PyProj
- Streamlit
- pytest / Ruff

## Quick start

### 1. Clone the repository

```bash
git clone https://github.com/Sammy500000/forestconservationai.git
cd forestconservationai
```

### 2. Create a virtual environment

#### Windows PowerShell

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If `py -3.12` is unavailable, install Python 3.12 and make sure it is available on your PATH.

#### Linux / macOS

```bash
python3.12 -m venv .venv
source .venv/bin/activate
```

### 3. Upgrade pip

```bash
python -m pip install --upgrade pip
```

### 4. Install the complete project environment

For the full project, install all optional dependency groups:

```bash
python -m pip install -e ".[dev,ml,networking,geospatial,dashboard]"
```

This installs the package in editable mode, so changes under `src/` are immediately available to the environment.

### 5. Verify the installation

Run the complete test suite:

```bash
python -m pytest
```

Then run the final project acceptance gate:

```bash
python scripts/verify_phase9.py
```

A successful run ends with:

```
Phase 9 acceptance verification passed.
```

## Run the application locally

The base application exposes a lightweight HTTP health service.

Start it with:

```bash
python -m forestwatch
```

By default it listens on:

```
http://127.0.0.1:8500
```

Open the health endpoint in a browser:

```
http://127.0.0.1:8500/healthz
```

Expected response:

```json
{"status":"ok","service":"forestwatch","version":"0.1.0"}
```

Stop the service with `Ctrl+C`.

You can change the bind address and port with:

```bash
FORESTWATCH_APP_HOST=127.0.0.1 FORESTWATCH_APP_PORT=8500 python -m forestwatch
```

On Windows PowerShell, set the variables first:

```powershell
$env:FORESTWATCH_APP_HOST="127.0.0.1"
$env:FORESTWATCH_APP_PORT="8500"
python -m forestwatch
```

## Run the ML evaluation

The EuroSAT evaluation script downloads the public EuroSAT RGB dataset when it is not already present and downloads the configured public ResNet50 checkpoint when no local checkpoint is supplied.

Run:

```bash
python scripts/evaluate_eurosat.py
```

The default locations are:

```
data/external/eurosat/
models/cache/
artifacts/metrics/
artifacts/figures/
```

The script reports:

- test-set sample count
- accuracy
- macro precision
- macro recall
- macro F1
- checkpoint used
- generated metric and confusion-matrix paths

To force CPU execution:

```bash
python scripts/evaluate_eurosat.py --device cpu
```

To use a local safetensors checkpoint:

```bash
python scripts/evaluate_eurosat.py --checkpoint path/to/model.safetensors
```

Downloaded datasets and model files are intentionally excluded from Git.

## Run the end-to-end Phase 5 demonstration

The Phase 5 demonstration connects detection, event creation, priority ordering, routing, and concurrent notification delivery.

It expects an extracted Forest-Change dataset under:

```
data/external/forest_change/
```

Run:

```bash
python scripts/run_phase5_demo.py
```

For a small smoke run:

```bash
python scripts/run_phase5_demo.py --limit 1 --device cpu
```

The default output is:

```
artifacts/metrics/phase5_demo.json
```

The repository does not commit the external Forest-Change dataset. If the dataset is not available locally, the Phase 5 runtime demo cannot be executed; this does not affect the offline repository acceptance tests.

## Hansen Global Forest Change validation

Phase 8 provides an optional geospatial validation path using the Hansen Global Forest Change v1.12 2000–2024 `lossyear` product.

Install the geospatial dependencies if they are not already installed:

```bash
python -m pip install -e ".[geospatial]"
```

For the official GFC product and download information, see:

https://storage.googleapis.com/earthenginepartners-hansen/GFC-2024-v1.12/download.html

Place only the required local raster tiles under:

```
data/external/gfc/
```

Do not commit GFC rasters to Git.

First run the offline Phase 8 check:

```bash
python scripts/verify_phase8.py
```

For a real validation run, the detection artifact must contain georeferenced event bounds. Then run:

```bash
python scripts/validate_against_gfc.py \
  --detections artifacts/metrics/georeferenced_detections.json \
  --gfc data/external/gfc/<lossyear>.tif
```

The validator produces:

```
artifacts/metrics/phase8_gfc_validation.json
```

GFC overlap is an evidence/agreement statistic. It does not establish the cause of forest loss and should not be described as proof of illegal logging, mining, encroachment, or another specific activity.

## Docker

Docker provides a reproducible application environment.

Build and start the complete local stack:

```bash
docker compose up --build
```

The application health service is available at:

```
http://127.0.0.1:8500/healthz
```

The Compose stack contains:

- `forestwatch` — application service
- `mosquitto` — MQTT broker used by the networking configuration

Stop the stack:

```bash
docker compose down
```

To rebuild from scratch:

```bash
docker compose build --no-cache
docker compose up
```

## Verification and CI

The final acceptance sequence is:

```bash
python -m pytest
python -m ruff check .
python -m compileall -q src
python scripts/verify_phase7.py
python scripts/verify_phase8.py
python scripts/verify_phase9.py
```

The Phase 9 verifier also checks that large downloaded datasets, model checkpoints, and GFC rasters are not tracked in Git.

GitHub Actions runs the project checks and Docker build automatically.

## Configuration

The main configuration files are:

```
configs/model.yaml
configs/detection.yaml
configs/network.yaml
```

Important defaults include:

- ResNet50 with 10 EuroSAT classes
- 224 × 224 model input
- deterministic 80/10/10-style dataset splitting
- forest-change confidence threshold of 0.70
- 64-pixel detection patches
- Dijkstra shortest-path routing
- MQTT networking configuration

Change configuration files rather than hard-coding experiment-specific values in source code.

## Generated artifacts

Research outputs should be kept under:

```
artifacts/metrics/
artifacts/figures/
```

Typical outputs include:

- EuroSAT metrics
- classification reports
- confusion matrices
- Phase 5 demonstration results
- GFC validation results

Large datasets, downloaded checkpoints, and GFC rasters should remain local.

## Reproducibility notes

For a final run, record:

1. Python version
2. installed dependency environment
3. configuration values
4. dataset source and revision where applicable
5. model checkpoint and revision
6. command used to generate each artifact

The project deliberately keeps external runtime data outside Git so that the repository remains lightweight and reproducible without storing large binary assets.

## Scope and limitations

This repository does not currently provide:

- live Sentinel-2 acquisition
- a continuously running global monitoring service
- a production database
- cloud deployment
- a full global GFC archive
- automated attribution of the cause of a detected change

The current system is intended to demonstrate the ML, change-detection, networking, and geospatial-validation components in a reproducible local environment.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE).
