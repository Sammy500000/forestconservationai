# Forest Conservation AI

A reproducible, local-first research prototype for satellite-based forest-loss screening and priority-aware early warning.

The project follows the supplied project materials: train a land-cover classifier with transfer learning, apply it to satellite imagery from different dates, identify candidate forest-to-nonforest transitions, and later connect those events to a publish/subscribe notification layer with prioritized routing. See the project reference guide and abstract for the intended research direction.

## Phase 1 status

Phase 1 establishes the repository and runtime foundation only.

It provides:

- Python 3.12 project configuration.
- Reproducible dependency management through `pyproject.toml`.
- Ruff linting and Pytest test configuration.
- Docker and Docker Compose for local execution.
- A minimal standard-library health service.
- A local Eclipse Mosquitto MQTT broker configuration for later phases.
- Central configuration files for model, detection, network, and study-area settings.
- A deterministic logging setup.
- A small typed event contract foundation for later networking work.
- No satellite or ML data are stored in Git.

Phase 1 intentionally does **not** implement model training, Sentinel-2 acquisition, change detection, MQTT routing, or the dashboard. Those belong to later phases.

## Prerequisites

For local development:

- Python 3.12+
- Git
- Docker Desktop with Docker Compose

For the fully containerized path, only Docker Desktop is required.

## Local setup

Create an environment and install the project with development dependencies:

```bash
python -m venv .venv
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
# macOS/Linux
source .venv/bin/activate

python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Run the Phase 1 checks:

```bash
pytest
ruff check .
python -m forestwatch
```

The module command should print the project health summary and exit successfully.

## Docker

Build and start the Phase 1 services:

```bash
docker compose up --build
```

The health service is available on:

```
http://localhost:8500/healthz
```

The local MQTT broker listens on:

```
localhost:1883
```

The Mosquitto configuration intentionally allows anonymous access because this broker is for local development only. Do not expose the Phase 1 broker directly to the public internet.

Stop the services:

```bash
docker compose down
```

## Project layout

```
forestconservationai/
├── configs/
│   ├── model.yaml
│   ├── detection.yaml
│   ├── network.yaml
│   └── study_area.yaml
├── data/
│   └── README.md
├── mosquitto/
│   └── config/
│       └── mosquitto.conf
├── scripts/
│   └── verify_phase1.py
├── src/
│   └── forestwatch/
│       ├── __init__.py
│       ├── __main__.py
│       ├── app.py
│       ├── config.py
│       ├── logging.py
│       └── schemas/
│           ├── __init__.py
│           └── events.py
├── tests/
│   ├── test_config.py
│   └── test_health.py
├── .dockerignore
├── .env.example
├── .gitignore
├── Dockerfile
├── LICENSE
├── Makefile
├── docker-compose.yml
└── pyproject.toml
```

## Design principles

1. Keep the system local-first and reproducible.
2. Keep project components independently testable.
3. Avoid storing large datasets or generated model artifacts in Git.
4. Keep configuration outside application logic.
5. Introduce external services only when they support an implemented research requirement.
6. Prefer small, explicit interfaces over framework-heavy abstractions.

## Planned implementation sequence

1. Repository/runtime foundation — **implemented here**.
2. EuroSAT data loading and ResNet50 transfer learning.
3. Classifier evaluation and research artifacts.
4. Sentinel-2 acquisition and geospatial patch extraction.
5. Two-date land-cover inference and candidate forest-loss detection.
6. Hansen Global Forest Change validation.
7. MQTT event publishing and subscribers.
8. Priority-aware routing and shortest-path simulation.
9. Concurrent notification delivery.
10. End-to-end integration and Streamlit dashboard.
11. Final reproducibility and acceptance testing.

## License

MIT. See `LICENSE`.
